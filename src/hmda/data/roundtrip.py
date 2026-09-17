"""Chạy round-trip HMDA local → PostgreSQL → snapshot local cho TASK-023."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from hmda import __version__
from hmda.core.config import ConfigLoader
from hmda.core.exceptions import RepositoryError
from hmda.core.path import ProjectPaths
from hmda.data.contracts import DataBatch, SnapshotStatus, SourceDescriptor, ValidationSummary
from hmda.data.loader import CSVBytesLoader
from hmda.data.postgres import (
    HMDA_BUSINESS_COLUMNS,
    PostgresRepository,
    PostgresSettings,
    make_connection_factory,
)
from hmda.data.repository import (
    IdempotencyIdentity,
    IngestionRequest,
    IngestionStatus,
    RecordSetSummary,
    make_idempotency_key,
    require_reconciled_record_sets,
    summarize_record_set,
)
from hmda.data.snapshot import (
    AtomicSnapshotExporter,
    SnapshotManifest,
    SnapshotSerialization,
    create_staging_manifest,
)
from hmda.data.source_identity import SourceIdentity, require_registered_source
from hmda.data.validator import ConfigurableDataValidator, QualityIssue, require_publishable


TRANSFORM_VERSION = "hmda-raw-transport-v1"
PROTOCOL_VERSION = "g2-minimal-dec-011"
_CODE_FILES = (
    "src/hmda/data/loader.py",
    "src/hmda/data/postgres.py",
    "src/hmda/data/repository.py",
    "src/hmda/data/roundtrip.py",
    "src/hmda/data/snapshot.py",
    "src/hmda/data/source_identity.py",
    "src/hmda/data/validator.py",
)


@dataclass(frozen=True, slots=True)
class RoundTripResult:
    ingestion_id: str
    snapshot_id: str
    status: str
    database: str
    row_count: int
    column_count: int
    distinct_record_id_count: int
    content_checksum: str
    data_checksum: str
    quality_checksum: str
    quality_error_count: int
    quality_warning_count: int
    snapshot_path: str
    evidence_path: str
    reused_existing: bool


def run_phase2_roundtrip(paths: ProjectPaths | None = None) -> RoundTripResult:
    """Thực hiện hoặc xác minh lại đúng một logical ingestion có idempotency."""

    resolved_paths = paths or ProjectPaths.discover()
    bundle = ConfigLoader(resolved_paths).load()
    data_config = _mapping(bundle.get("data"), "data")
    database_config = _mapping(bundle.get("database"), "database")
    schema_config = _mapping(bundle.get("schema"), "schema")
    quality_config = _mapping(bundle.get("quality"), "quality")

    business_columns = tuple(schema_config.get("column_order", ()))
    if business_columns != HMDA_BUSINESS_COLUMNS:
        raise RepositoryError("Schema config không khớp 18 cột PostgreSQL đã khóa")

    registered = require_registered_source(data_config)
    source_path = resolved_paths.resolve(registered.location, must_exist=True)
    source = SourceDescriptor(
        source_id=registered.source_id,
        version=registered.version,
        location=str(source_path),
        checksum=registered.checksum,
    )
    source_config = _mapping(data_config.get("source"), "data.source")
    batch = CSVBytesLoader(
        encoding=str(source_config["encoding"]),
        delimiter=str(source_config["delimiter"]),
    ).load(source)
    validation = ConfigurableDataValidator().validate(batch, config=quality_config)
    require_publishable(validation)
    local_summary = summarize_record_set(
        batch.payload,
        business_columns=business_columns,
    )

    source_identity = SourceIdentity(
        source_id=batch.source.source_id,
        version=batch.source.version,
        checksum=str(batch.source.checksum),
        byte_size=int(batch.metadata["byte_size"]),
    )
    schema_version = (
        f"{schema_config['schema_version']}+{database_config['schema_version']}"
    )
    identity = IdempotencyIdentity(
        source_id=source_identity.source_id,
        source_version=source_identity.version,
        source_checksum=source_identity.checksum,
        schema_version=schema_version,
        config_hash=bundle.config_hash(),
        transform_version=TRANSFORM_VERSION,
    )
    idempotency_key = make_idempotency_key(identity)
    request = IngestionRequest.create(
        ingestion_id=f"ing-{idempotency_key[:24]}",
        snapshot_id=f"hmda-2024-ny-{idempotency_key[:24]}",
        identity=identity,
    )

    settings = PostgresSettings.from_config(bundle)
    repository = PostgresRepository(make_connection_factory(settings))
    snapshot_root = resolved_paths.resolve(
        _mapping(database_config.get("target"), "database.target")[
            "local_snapshot_root"
        ]
    )
    final_exporter = AtomicSnapshotExporter(snapshot_root)
    pending_exporter = AtomicSnapshotExporter(snapshot_root / ".pending")
    final_path = snapshot_root / request.snapshot_id
    pending_path = pending_exporter.root / request.snapshot_id
    code_version = _code_version(resolved_paths)

    existing = repository.get_ingestion_by_key(idempotency_key)
    if existing is not None:
        if existing.status is not IngestionStatus.READY:
            raise RepositoryError(
                f"Logical ingestion đã tồn tại ở trạng thái {existing.status.value}; "
                "không tự ghi đè hoặc tạo run mới"
            )
        if (
            existing.ingestion_id != request.ingestion_id
            or existing.snapshot_id != request.snapshot_id
        ):
            raise RepositoryError("Logical ingestion READY có ID khác contract hiện hành")
        _recover_pending_snapshot(pending_path, final_path)
        return _verify_and_record(
            resolved_paths=resolved_paths,
            repository=repository,
            exporter=final_exporter,
            settings=settings,
            request=request,
            batch=batch,
            source_path=source_path,
            quality_config=quality_config,
            validation=validation,
            local_summary=local_summary,
            schema_version=schema_version,
            code_version=code_version,
            reused_existing=True,
        )

    if final_path.exists() or pending_path.exists():
        raise RepositoryError(
            "Snapshot path đã tồn tại nhưng PostgreSQL chưa có logical ingestion; "
            "cần review orphan trước khi chạy"
        )

    serialization = SnapshotSerialization(
        columns=(
            "record_id",
            "source_row_number",
            "source_line_number",
            *business_columns,
        ),
        null_token="<NULL>",
        encoding="utf-8",
        delimiter=",",
        line_terminator="\n",
        record_id_field="record_id",
    )
    staging_manifest = create_staging_manifest(
        batch,
        validation,
        snapshot_id=request.snapshot_id,
        schema_version=schema_version,
        config_hash=identity.config_hash,
        code_version=code_version,
        transform_version=TRANSFORM_VERSION,
        serialization=serialization,
        protocol_version=PROTOCOL_VERSION,
    )

    staged_summary: RecordSetSummary | None = None
    raw_summary: RecordSetSummary | None = None
    pending_created = False
    with repository.transaction() as transaction:
        transaction.register_source(source_identity)
        ingestion = transaction.begin_ingestion(request)
        if ingestion.status is not IngestionStatus.STAGING:
            raise RepositoryError("Ingestion mới không ở trạng thái STAGING")
        transaction.stage_snapshot(
            ingestion.ingestion_id,
            staging_manifest.to_descriptor(),
        )
        staged_summary = transaction.stage_records(
            ingestion.ingestion_id,
            batch.payload,
        )
        raw_summary = transaction.promote_records(
            ingestion.ingestion_id,
            staged_summary,
        )
        require_reconciled_record_sets(local_summary, raw_summary)
        transaction.save_quality_result(ingestion.ingestion_id, validation)

        db_records = transaction.read_promoted_records(ingestion.ingestion_id)
        db_batch = DataBatch(
            payload=tuple(db_records),
            source=batch.source,
            metadata=dict(batch.metadata),
        )
        db_validation = ConfigurableDataValidator().validate(
            db_batch,
            config=quality_config,
        )
        require_publishable(db_validation)
        _require_same_quality(validation, db_validation)
        ready_descriptor = pending_exporter.export(
            db_batch,
            db_validation,
            staging_manifest,
            serialization,
        )
        pending_created = True
        transaction.clear_staged_records(
            ingestion.ingestion_id,
            local_summary.row_count,
        )
        transaction.publish_ready(ingestion.ingestion_id, ready_descriptor)
        transaction.commit()

    if staged_summary is None or raw_summary is None:
        raise RepositoryError("Round-trip kết thúc mà thiếu record summary")
    if not pending_created:
        raise RepositoryError("Round-trip kết thúc mà thiếu pending snapshot")
    _recover_pending_snapshot(pending_path, final_path)

    del db_records
    del db_batch
    return _verify_and_record(
        resolved_paths=resolved_paths,
        repository=repository,
        exporter=final_exporter,
        settings=settings,
        request=request,
        batch=batch,
        source_path=source_path,
        quality_config=quality_config,
        validation=validation,
        local_summary=local_summary,
        schema_version=schema_version,
        code_version=code_version,
        reused_existing=False,
        staged_summary=staged_summary,
        raw_summary=raw_summary,
    )


def _verify_and_record(
    *,
    resolved_paths: ProjectPaths,
    repository: PostgresRepository,
    exporter: AtomicSnapshotExporter,
    settings: PostgresSettings,
    request: IngestionRequest,
    batch: DataBatch[Sequence[Mapping[str, object]]],
    source_path: Path,
    quality_config: Mapping[str, Any],
    validation: ValidationSummary,
    local_summary: RecordSetSummary,
    schema_version: str,
    code_version: str,
    reused_existing: bool,
    staged_summary: RecordSetSummary | None = None,
    raw_summary: RecordSetSummary | None = None,
) -> RoundTripResult:
    descriptor = repository.get_ready(request.snapshot_id)
    if descriptor.status is not SnapshotStatus.READY:
        raise RepositoryError("PostgreSQL snapshot chưa READY sau commit")
    ready_records = repository.get_ready_records(request.snapshot_id)
    ready_summary = summarize_record_set(
        ready_records,
        business_columns=HMDA_BUSINESS_COLUMNS,
    )
    require_reconciled_record_sets(local_summary, ready_summary)

    ready_batch = DataBatch(
        payload=ready_records,
        source=batch.source,
        metadata=dict(batch.metadata),
    )
    ready_validation = ConfigurableDataValidator().validate(
        ready_batch,
        config=quality_config,
    )
    require_publishable(ready_validation)
    _require_same_quality(validation, ready_validation)
    manifest = exporter.require_reconciled_ready(
        request.snapshot_id,
        ready_records,
    )

    if manifest.data_checksum is None or manifest.quality_checksum is None:
        raise RepositoryError("READY manifest thiếu checksum")
    if descriptor.metadata.get("data_checksum") != manifest.data_checksum:
        raise RepositoryError("DB metadata không khớp data checksum local")
    if descriptor.metadata.get("quality_checksum") != manifest.quality_checksum:
        raise RepositoryError("DB metadata không khớp quality checksum local")

    cleaned_staging_rows = repository.cleanup_ready_staging(
        request.ingestion_id,
        ready_summary.row_count,
    )

    evidence_dir = resolved_paths.artifacts / "runs" / request.ingestion_id
    evidence_path = evidence_dir / "phase2_roundtrip.json"
    previous_evidence = _read_existing_evidence(evidence_path)
    evidence = {
        "evidence_kind": "phase2_real_roundtrip",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "database": settings.database,
        "source": {
            "source_id": batch.source.source_id,
            "source_version": batch.source.version,
            "source_checksum": batch.source.checksum,
            "source_path": str(source_path.relative_to(resolved_paths.root)).replace("\\", "/"),
            "byte_size": batch.metadata["byte_size"],
        },
        "ingestion": {
            "ingestion_id": request.ingestion_id,
            "snapshot_id": request.snapshot_id,
            "idempotency_key": request.idempotency_key,
            "status": descriptor.status.value,
            "reused_existing": reused_existing,
        },
        "versions": {
            "package_version": __version__,
            "schema_version": schema_version,
            "config_hash": request.identity.config_hash,
            "snapshot_code_version": manifest.code_version,
            "verification_code_version": code_version,
            "transform_version": TRANSFORM_VERSION,
            "protocol_version": PROTOCOL_VERSION,
        },
        "reconciliation": {
            "local": asdict(local_summary),
            "staging": asdict(staged_summary or local_summary),
            "raw": asdict(raw_summary or local_summary),
            "ready_readback": asdict(ready_summary),
            "staging_rows_after_cleanup": 0,
            "staging_rows_cleaned_in_this_verification": cleaned_staging_rows,
        },
        "quality": {
            "is_valid": ready_validation.is_valid,
            "error_count": ready_validation.metadata.get("error_count", 0),
            "warning_count": ready_validation.metadata.get("warning_count", 0),
            "issues": [_quality_issue(issue) for issue in ready_validation.issues],
        },
        "snapshot": {
            "path": str((exporter.root / request.snapshot_id).relative_to(resolved_paths.root)).replace("\\", "/"),
            "files": ["data.csv", "manifest.json", "quality_report.json"],
            "data_checksum": manifest.data_checksum,
            "quality_checksum": manifest.quality_checksum,
            "row_count": manifest.row_count,
            "column_count": manifest.column_count,
        },
    }
    if previous_evidence is not None and reused_existing:
        original_execution = previous_evidence.get(
            "original_execution",
            previous_evidence,
        )
        retry_verifications = list(previous_evidence.get("retry_verifications", []))
        retry_verifications.append({
            "verified_at": evidence["completed_at"],
            "verification_code_version": code_version,
            "staging_rows_cleaned": cleaned_staging_rows,
            "record_level_reconciliation": "PASS",
            "quality_reconciliation": "PASS",
        })
        evidence["original_execution"] = original_execution
        evidence["retry_verifications"] = retry_verifications
    _write_json_atomic(evidence_path, evidence)
    return RoundTripResult(
        ingestion_id=request.ingestion_id,
        snapshot_id=request.snapshot_id,
        status=descriptor.status.value,
        database=settings.database,
        row_count=ready_summary.row_count,
        column_count=len(ready_summary.columns),
        distinct_record_id_count=ready_summary.distinct_record_id_count,
        content_checksum=ready_summary.content_checksum,
        data_checksum=manifest.data_checksum,
        quality_checksum=manifest.quality_checksum,
        quality_error_count=int(ready_validation.metadata.get("error_count", 0)),
        quality_warning_count=int(ready_validation.metadata.get("warning_count", 0)),
        snapshot_path=evidence["snapshot"]["path"],
        evidence_path=str(evidence_path.relative_to(resolved_paths.root)).replace("\\", "/"),
        reused_existing=reused_existing,
    )


def _recover_pending_snapshot(pending_path: Path, final_path: Path) -> None:
    if final_path.exists():
        if pending_path.exists():
            raise RepositoryError("Cả pending và final snapshot cùng tồn tại")
        return
    if not pending_path.is_dir():
        raise RepositoryError("PostgreSQL READY nhưng thiếu pending/final snapshot local")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(pending_path, final_path)
    try:
        pending_path.parent.rmdir()
    except OSError:
        pass


def _require_same_quality(
    expected: ValidationSummary,
    actual: ValidationSummary,
) -> None:
    def signature(summary: ValidationSummary) -> tuple[tuple[Any, ...], ...]:
        return tuple(
            (
                getattr(issue, "rule_id", None),
                str(getattr(issue, "severity", "")),
                getattr(issue, "affected_count", None),
                getattr(issue, "denominator", None),
                tuple(getattr(issue, "sample_ids", ())),
            )
            for issue in summary.issues
        )

    if expected.is_valid != actual.is_valid or signature(expected) != signature(actual):
        raise RepositoryError("Quality result thay đổi qua round-trip")


def _code_version(paths: ProjectPaths) -> str:
    digest = sha256()
    for relative in _CODE_FILES:
        content = (paths.root / relative).read_bytes()
        encoded_name = relative.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(4, "big"))
        digest.update(encoded_name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _quality_issue(issue: object) -> dict[str, Any]:
    if not isinstance(issue, QualityIssue):
        return {"type": type(issue).__name__}
    return {
        "rule_id": issue.rule_id,
        "layer": issue.layer,
        "severity": issue.severity.value,
        "affected_count": issue.affected_count,
        "denominator": issue.denominator,
        "sample_ids": list(issue.sample_ids),
        "rule_version": issue.rule_version,
        "message": issue.message,
    }


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RepositoryError(f"{field_name} phải là mapping")
    return value


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    content = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    try:
        with temp_path.open("wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _read_existing_evidence(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise RepositoryError("Evidence hiện có không phải JSON object")
    return loaded


def main() -> int:
    result = run_phase2_roundtrip()
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
