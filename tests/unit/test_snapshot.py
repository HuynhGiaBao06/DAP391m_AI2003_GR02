import json

import pytest

from hmda.core.exceptions import DataValidationError, SnapshotError
from hmda.data.contracts import (
    DataBatch,
    SnapshotStatus,
    SourceDescriptor,
    ValidationSummary,
)
from hmda.data.snapshot import (
    AtomicSnapshotExporter,
    AtomicSnapshotManager,
    SnapshotManager,
    SnapshotSerialization,
    create_staging_manifest,
)
from hmda.data.validator import QualityIssue, QualitySeverity


def _batch(*, source_id: str = "fixture-source", checksum: str = "a" * 64):
    return DataBatch(
        payload=(
            {"record_id": "r1", "code": "001", "note": None},
            {"record_id": "r2", "code": "002", "note": "NA"},
        ),
        source=SourceDescriptor(
            source_id=source_id,
            version="v1",
            location="memory://fixture",
            checksum=checksum,
        ),
        metadata={"content_checksum": checksum},
    )


def _validation(*, valid: bool = True):
    return ValidationSummary(
        is_valid=valid,
        metadata={
            "error_count": 0 if valid else 1,
            "warning_count": 1,
        },
    )


def _serialization():
    return SnapshotSerialization(
        columns=("record_id", "code", "note"),
        null_token="<NULL>",
    )


def _manifest(batch=None, validation=None, **overrides):
    values = {
        "snapshot_id": "fixture-snapshot",
        "schema_version": "schema-v1",
        "config_hash": "b" * 64,
        "code_version": "code-v1",
        "transform_version": "transform-v1",
        "serialization": _serialization(),
        "created_at": "2026-09-11T00:00:00+00:00",
    }
    values.update(overrides)
    return create_staging_manifest(
        batch or _batch(),
        validation or _validation(),
        **values,
    )


def test_snapshot_lifecycle_is_one_way_and_ready_requires_export_checksum() -> None:
    staging = _manifest()
    failed = staging.transition(SnapshotStatus.FAILED)

    assert failed.status is SnapshotStatus.FAILED
    with pytest.raises(SnapshotError, match="không thể sửa"):
        failed.transition(SnapshotStatus.STAGING)
    with pytest.raises(SnapshotError, match="data_checksum"):
        staging.transition(SnapshotStatus.READY)
    with pytest.raises(SnapshotError, match="SnapshotStatus"):
        type(staging)(**{**staging.to_dict(), "status": "STAGING"})


def test_quality_error_blocks_ready_and_creates_no_snapshot_output(tmp_path) -> None:
    invalid = _validation(valid=False)
    manifest = _manifest(validation=invalid)
    exporter = AtomicSnapshotExporter(tmp_path)

    with pytest.raises(DataValidationError, match="chặn publish"):
        exporter.export(_batch(), invalid, manifest, _serialization())

    assert list(tmp_path.iterdir()) == []


def test_atomic_export_writes_verified_ready_snapshot_and_retry_is_idempotent(
    tmp_path,
) -> None:
    batch = _batch()
    validation = _validation()
    manifest = _manifest(batch, validation)
    exporter = AtomicSnapshotExporter(tmp_path)

    first = exporter.export(batch, validation, manifest, _serialization())
    retry_manifest = _manifest(
        batch,
        validation,
        created_at="2026-09-11T01:00:00+00:00",
    )
    retry = exporter.export(batch, validation, retry_manifest, _serialization())

    snapshot_dir = tmp_path / "fixture-snapshot"
    saved_manifest = json.loads(
        (snapshot_dir / "manifest.json").read_text(encoding="utf-8")
    )
    saved_quality = json.loads(
        (snapshot_dir / "quality_report.json").read_text(encoding="utf-8")
    )
    assert first.status is SnapshotStatus.READY
    assert retry == first
    assert sorted(path.name for path in snapshot_dir.iterdir()) == [
        "data.csv",
        "manifest.json",
        "quality_report.json",
    ]
    assert saved_manifest["status"] == "READY"
    assert saved_manifest["row_count"] == 2
    assert saved_manifest["quality_warning_count"] == 1
    assert saved_manifest["data_checksum"]
    assert saved_manifest["quality_checksum"]
    assert saved_quality["is_valid"] is True
    assert saved_quality["error_count"] == 0
    assert saved_quality["warning_count"] == 1
    assert saved_manifest["encoding"] == "utf-8"
    assert saved_manifest["null_token"] == "<NULL>"
    assert len(list(tmp_path.iterdir())) == 1


def test_retry_reconciles_content_instead_of_trusting_identity_only(tmp_path) -> None:
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(_batch(), _validation(), _manifest(), _serialization())
    changed = DataBatch(
        payload=(
            {"record_id": "r1", "code": "001", "note": "changed"},
            {"record_id": "r2", "code": "002", "note": "NA"},
        ),
        source=_batch().source,
        metadata=_batch().metadata,
    )

    with pytest.raises(SnapshotError, match="theo record_id"):
        exporter.export(
            changed,
            _validation(),
            _manifest(changed, _validation()),
            _serialization(),
        )


def test_retry_rejects_changed_quality_counts(tmp_path) -> None:
    batch = _batch()
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(batch, _validation(), _manifest(), _serialization())
    changed_validation = ValidationSummary(
        is_valid=True,
        metadata={"error_count": 0, "warning_count": 2},
    )

    with pytest.raises(SnapshotError, match="identity READY khác"):
        exporter.export(
            batch,
            changed_validation,
            _manifest(validation=changed_validation),
            _serialization(),
        )


def test_same_snapshot_id_cannot_overwrite_ready_snapshot_of_other_identity(
    tmp_path,
) -> None:
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(_batch(), _validation(), _manifest(), _serialization())
    other_batch = _batch(source_id="other-source", checksum="c" * 64)
    other_manifest = _manifest(other_batch, _validation())

    with pytest.raises(SnapshotError, match="identity READY khác"):
        exporter.export(
            other_batch,
            _validation(),
            other_manifest,
            _serialization(),
        )


def test_failure_before_directory_publish_leaves_no_partial_final_and_retry_works(
    tmp_path,
) -> None:
    def fail_publish(source, destination):
        raise OSError("fixture interruption")

    failing = AtomicSnapshotExporter(tmp_path, publish_directory=fail_publish)

    with pytest.raises(SnapshotError, match="export thất bại"):
        failing.export(_batch(), _validation(), _manifest(), _serialization())

    assert list(tmp_path.iterdir()) == []
    result = AtomicSnapshotExporter(tmp_path).export(
        _batch(), _validation(), _manifest(), _serialization()
    )
    assert result.status is SnapshotStatus.READY


def test_ready_reader_rejects_checksum_mismatch(tmp_path) -> None:
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(_batch(), _validation(), _manifest(), _serialization())
    data_path = tmp_path / "fixture-snapshot" / "data.csv"
    data_path.write_bytes(data_path.read_bytes() + b"tampered")

    with pytest.raises(SnapshotError, match="Checksum"):
        exporter.load_ready("fixture-snapshot")


def test_ready_reader_rejects_quality_report_checksum_mismatch(tmp_path) -> None:
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(_batch(), _validation(), _manifest(), _serialization())
    quality_path = tmp_path / "fixture-snapshot" / "quality_report.json"
    quality_path.write_bytes(quality_path.read_bytes() + b"tampered")

    with pytest.raises(SnapshotError, match="quality report"):
        exporter.load_ready("fixture-snapshot")


def test_ready_snapshot_reconciles_against_expected_records_streaming(tmp_path) -> None:
    exporter = AtomicSnapshotExporter(tmp_path)
    batch = _batch()
    exporter.export(batch, _validation(), _manifest(), _serialization())

    manifest = exporter.require_reconciled_ready(
        "fixture-snapshot",
        batch.payload,
    )

    assert manifest.status is SnapshotStatus.READY
    changed = (
        batch.payload[0],
        {**batch.payload[1], "note": "changed"},
    )
    with pytest.raises(SnapshotError, match="theo record_id"):
        exporter.require_reconciled_ready("fixture-snapshot", changed)


def test_quality_report_redacts_sensitive_metadata(tmp_path) -> None:
    validation = ValidationSummary(
        is_valid=True,
        metadata={
            "error_count": 0,
            "warning_count": 0,
            "connection": {"password": "must-not-be-persisted"},
            "observed_tokens": ["NA", "Exempt", ""],
        },
    )
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(
        _batch(),
        validation,
        _manifest(validation=validation),
        _serialization(),
    )
    report_text = (
        tmp_path / "fixture-snapshot" / "quality_report.json"
    ).read_text(encoding="utf-8")

    assert "must-not-be-persisted" not in report_text
    assert "***REDACTED***" in report_text
    assert '"observed_tokens":["NA","Exempt",""]' in report_text


def test_quality_report_serializes_structured_quality_issues(tmp_path) -> None:
    validation = ValidationSummary(
        is_valid=True,
        issues=(
            QualityIssue(
                rule_id="FIXTURE_WARNING",
                layer="raw",
                severity=QualitySeverity.WARNING,
                affected_count=1,
                denominator=2,
                sample_ids=("r1",),
            ),
        ),
        metadata={"error_count": 0, "warning_count": 1},
    )
    exporter = AtomicSnapshotExporter(tmp_path)
    exporter.export(
        _batch(),
        validation,
        _manifest(validation=validation),
        _serialization(),
    )
    report = json.loads(
        (tmp_path / "fixture-snapshot" / "quality_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["issues"][0]["rule_id"] == "FIXTURE_WARNING"
    assert report["issues"][0]["severity"] == "WARNING"


def test_snapshot_id_rejects_path_traversal() -> None:
    with pytest.raises(SnapshotError, match="identifier an toàn"):
        _manifest(snapshot_id="../outside")


def test_atomic_manager_implements_snapshot_protocol_without_persisting_extra_metadata(
    tmp_path,
) -> None:
    manager = AtomicSnapshotManager(AtomicSnapshotExporter(tmp_path))
    metadata = {
        "snapshot_id": "fixture-manager",
        "schema_version": "schema-v1",
        "config_hash": "b" * 64,
        "code_version": "code-v1",
        "transform_version": "transform-v1",
        "created_at": "2026-09-11T00:00:00+00:00",
        "serialization": _serialization(),
        "password": "must-not-be-persisted",
    }

    descriptor = manager.create(_batch(), _validation(), metadata=metadata)
    saved = json.loads(
        (tmp_path / "fixture-manager" / "manifest.json").read_text(encoding="utf-8")
    )

    assert isinstance(manager, SnapshotManager)
    assert descriptor.status is SnapshotStatus.READY
    assert "password" not in saved
