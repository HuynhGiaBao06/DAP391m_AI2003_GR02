from copy import deepcopy
from dataclasses import replace

import pytest

from hmda.core.exceptions import RepositoryError
from hmda.data.contracts import (
    SnapshotDescriptor,
    SnapshotStatus,
    ValidationSummary,
)
from hmda.data.repository import (
    DataRepository,
    IdempotencyIdentity,
    IngestionDescriptor,
    IngestionRequest,
    IngestionStatus,
    RepositoryUnitOfWork,
    make_idempotency_key,
)
from hmda.data.source_identity import SourceIdentity


class FakeRepository:
    """Transactional fake for contract evidence only; not a DB simulation."""

    def __init__(self) -> None:
        self.sources = {}
        self.ingestions = {}
        self.idempotency_index = {}
        self.quality_results = {}
        self.staged_snapshots = {}
        self.ready_snapshots = {}

    def transaction(self):
        return FakeUnitOfWork(self)

    def get_ready(self, snapshot_id: str) -> SnapshotDescriptor:
        try:
            return self.ready_snapshots[snapshot_id]
        except KeyError as exc:
            raise RepositoryError("Snapshot không READY hoặc không tồn tại") from exc


class FakeUnitOfWork:
    def __init__(self, repository: FakeRepository) -> None:
        self.repository = repository
        self.state = None
        self.closed = False

    def __enter__(self):
        self.state = {
            "sources": deepcopy(self.repository.sources),
            "ingestions": deepcopy(self.repository.ingestions),
            "idempotency_index": deepcopy(self.repository.idempotency_index),
            "quality_results": deepcopy(self.repository.quality_results),
            "staged_snapshots": deepcopy(self.repository.staged_snapshots),
            "ready_snapshots": deepcopy(self.repository.ready_snapshots),
        }
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.closed:
            self.rollback()
        return False

    def _open(self):
        if self.state is None or self.closed:
            raise RepositoryError("Unit of work không còn mở")
        return self.state

    def register_source(self, source: SourceIdentity) -> None:
        state = self._open()
        existing = state["sources"].get(source.source_id)
        if existing is not None and existing != source:
            raise RepositoryError("source_id đã thuộc identity khác")
        state["sources"][source.source_id] = source

    def begin_ingestion(self, request: IngestionRequest) -> IngestionDescriptor:
        state = self._open()
        existing_id = state["idempotency_index"].get(request.idempotency_key)
        if existing_id is not None:
            return state["ingestions"][existing_id]
        if request.ingestion_id in state["ingestions"]:
            raise RepositoryError("ingestion_id đã tồn tại")
        if any(
            item.snapshot_id == request.snapshot_id
            for item in state["ingestions"].values()
        ):
            raise RepositoryError("snapshot_id đã thuộc ingestion khác")
        descriptor = IngestionDescriptor(
            ingestion_id=request.ingestion_id,
            snapshot_id=request.snapshot_id,
            idempotency_key=request.idempotency_key,
            source_id=request.identity.source_id,
            status=IngestionStatus.STAGING,
        )
        state["ingestions"][request.ingestion_id] = descriptor
        state["idempotency_index"][request.idempotency_key] = request.ingestion_id
        return descriptor

    def save_quality_result(
        self, ingestion_id: str, validation: ValidationSummary
    ) -> None:
        state = self._open()
        self._require_staging(state, ingestion_id)
        state["quality_results"][ingestion_id] = validation

    def stage_snapshot(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None:
        state = self._open()
        ingestion = self._require_staging(state, ingestion_id)
        if snapshot.status is not SnapshotStatus.STAGING:
            raise RepositoryError("stage_snapshot yêu cầu descriptor STAGING")
        if (
            snapshot.snapshot_id != ingestion.snapshot_id
            or snapshot.source_id != ingestion.source_id
        ):
            raise RepositoryError("Snapshot không khớp ingestion identity")
        state["staged_snapshots"][ingestion_id] = snapshot

    def mark_failed(self, ingestion_id: str, *, reason: str) -> None:
        state = self._open()
        ingestion = self._require_staging(state, ingestion_id)
        if not isinstance(reason, str) or not reason.strip():
            raise RepositoryError("Failure reason không được rỗng")
        state["ingestions"][ingestion_id] = replace(
            ingestion, status=IngestionStatus.FAILED
        )

    def publish_ready(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None:
        state = self._open()
        ingestion = self._require_staging(state, ingestion_id)
        validation = state["quality_results"].get(ingestion_id)
        staged = state["staged_snapshots"].get(ingestion_id)
        if validation is None or not validation.is_valid:
            raise RepositoryError("Quality ERROR hoặc thiếu quality result chặn publish")
        if staged is None:
            raise RepositoryError("Chưa có staged snapshot")
        if snapshot.status is not SnapshotStatus.READY:
            raise RepositoryError("publish_ready yêu cầu filesystem snapshot READY")
        if (
            snapshot.snapshot_id != staged.snapshot_id
            or snapshot.source_id != staged.source_id
        ):
            raise RepositoryError("READY snapshot không khớp staged snapshot")
        state["ready_snapshots"][snapshot.snapshot_id] = snapshot
        state["ingestions"][ingestion_id] = replace(
            ingestion, status=IngestionStatus.READY
        )

    def commit(self) -> None:
        state = self._open()
        for name, value in state.items():
            setattr(self.repository, name, value)
        self.closed = True

    def rollback(self) -> None:
        self._open()
        self.closed = True

    @staticmethod
    def _require_staging(state, ingestion_id):
        try:
            ingestion = state["ingestions"][ingestion_id]
        except KeyError as exc:
            raise RepositoryError("Ingestion không tồn tại") from exc
        if ingestion.status is not IngestionStatus.STAGING:
            raise RepositoryError("Ingestion không còn ở STAGING")
        return ingestion


def _source(source_id="fixture-source", checksum="a" * 64):
    return SourceIdentity(source_id, "v1", checksum, 10)


def _identity(**overrides):
    values = {
        "source_id": "fixture-source",
        "source_version": "v1",
        "source_checksum": "a" * 64,
        "schema_version": "schema-v1",
        "config_hash": "b" * 64,
        "transform_version": "transform-v1",
    }
    values.update(overrides)
    return IdempotencyIdentity(**values)


def _request(ingestion_id="fixture-ingestion", snapshot_id="fixture-snapshot", **identity):
    return IngestionRequest.create(
        ingestion_id=ingestion_id,
        snapshot_id=snapshot_id,
        identity=_identity(**identity),
    )


def _snapshot(status):
    return SnapshotDescriptor(
        snapshot_id="fixture-snapshot",
        status=status,
        source_id="fixture-source",
    )


def test_idempotency_key_is_deterministic_and_changes_with_logical_identity() -> None:
    identity = _identity()

    assert make_idempotency_key(identity) == make_idempotency_key(identity)
    assert make_idempotency_key(identity) != make_idempotency_key(
        _identity(transform_version="transform-v2")
    )
    with pytest.raises(RepositoryError, match="không khớp"):
        IngestionRequest(
            "fixture-ingestion", "fixture-snapshot", identity, "tampered"
        )


def test_repository_and_unit_of_work_implement_vendor_neutral_protocols() -> None:
    repository = FakeRepository()

    assert isinstance(repository, DataRepository)
    with repository.transaction() as transaction:
        assert isinstance(transaction, RepositoryUnitOfWork)


def test_retry_same_key_returns_same_logical_ingestion_without_duplicate() -> None:
    repository = FakeRepository()
    request = _request()

    with repository.transaction() as transaction:
        first = transaction.begin_ingestion(request)
        retry = transaction.begin_ingestion(
            _request("retry-id", "retry-snapshot")
        )
        transaction.commit()

    assert retry == first
    assert len(repository.ingestions) == 1
    assert len(repository.idempotency_index) == 1


def test_different_identity_creates_separate_run_without_overwrite() -> None:
    repository = FakeRepository()

    with repository.transaction() as transaction:
        first = transaction.begin_ingestion(_request())
        second = transaction.begin_ingestion(
            _request(
                "fixture-ingestion-2",
                "fixture-snapshot-2",
                transform_version="transform-v2",
            )
        )
        transaction.commit()

    assert first.idempotency_key != second.idempotency_key
    assert set(repository.ingestions) == {
        "fixture-ingestion",
        "fixture-ingestion-2",
    }


def test_different_identity_cannot_reuse_existing_snapshot_id() -> None:
    repository = FakeRepository()
    with repository.transaction() as transaction:
        transaction.begin_ingestion(_request())
        transaction.commit()

    with pytest.raises(RepositoryError, match="snapshot_id đã thuộc"):
        with repository.transaction() as transaction:
            transaction.begin_ingestion(
                _request(
                    "fixture-ingestion-2",
                    "fixture-snapshot",
                    transform_version="transform-v2",
                )
            )

    assert set(repository.ingestions) == {"fixture-ingestion"}


def test_failure_before_publish_is_not_visible_to_ready_reader() -> None:
    repository = FakeRepository()

    with repository.transaction() as transaction:
        transaction.begin_ingestion(_request())
        transaction.mark_failed("fixture-ingestion", reason="fixture failure")
        transaction.commit()

    assert repository.ingestions["fixture-ingestion"].status is IngestionStatus.FAILED
    with pytest.raises(RepositoryError, match="không READY"):
        repository.get_ready("fixture-snapshot")


def test_exception_rolls_back_uncommitted_transaction() -> None:
    repository = FakeRepository()

    with pytest.raises(RuntimeError, match="fixture interruption"):
        with repository.transaction() as transaction:
            transaction.register_source(_source())
            transaction.begin_ingestion(_request())
            raise RuntimeError("fixture interruption")

    assert repository.sources == {}
    assert repository.ingestions == {}


def test_publish_ready_requires_quality_and_exported_ready_snapshot() -> None:
    repository = FakeRepository()

    with repository.transaction() as transaction:
        transaction.register_source(_source())
        transaction.begin_ingestion(_request())
        transaction.stage_snapshot(
            "fixture-ingestion", _snapshot(SnapshotStatus.STAGING)
        )
        transaction.save_quality_result(
            "fixture-ingestion",
            ValidationSummary(
                is_valid=True,
                metadata={"error_count": 0, "warning_count": 1},
            ),
        )
        transaction.publish_ready(
            "fixture-ingestion", _snapshot(SnapshotStatus.READY)
        )
        transaction.commit()

    visible = repository.get_ready("fixture-snapshot")
    assert visible.status is SnapshotStatus.READY
    assert repository.ingestions["fixture-ingestion"].status is IngestionStatus.READY


def test_invalid_quality_cannot_publish_and_rollback_preserves_no_partial_state() -> None:
    repository = FakeRepository()

    with pytest.raises(RepositoryError, match="Quality ERROR"):
        with repository.transaction() as transaction:
            transaction.begin_ingestion(_request())
            transaction.stage_snapshot(
                "fixture-ingestion", _snapshot(SnapshotStatus.STAGING)
            )
            transaction.save_quality_result(
                "fixture-ingestion", ValidationSummary(is_valid=False)
            )
            transaction.publish_ready(
                "fixture-ingestion", _snapshot(SnapshotStatus.READY)
            )

    assert repository.ingestions == {}
    assert repository.ready_snapshots == {}
