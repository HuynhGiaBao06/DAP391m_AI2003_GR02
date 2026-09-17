"""PostgreSQL settings, migrations và repository adapter cho Phase 2."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from hmda.core.config import ConfigBundle
from hmda.core.exceptions import ConfigurationError, RepositoryError
from hmda.data.contracts import SnapshotDescriptor, SnapshotStatus, ValidationSummary
from hmda.data.repository import (
    IngestionDescriptor,
    IngestionRequest,
    IngestionStatus,
    RecordSetSummary,
    require_reconciled_record_sets,
    summarize_record_set,
)
from hmda.data.source_identity import SourceIdentity


ConnectionFactory = Callable[[], Any]
_MIGRATION_LOCK_ID = 72405022
HMDA_BUSINESS_COLUMNS = (
    "income",
    "loan_amount",
    "combined_loan_to_value_ratio",
    "property_value",
    "loan_term",
    "debt_to_income_ratio",
    "loan_type",
    "loan_purpose",
    "lien_status",
    "occupancy_type",
    "construction_method",
    "total_units",
    "action_taken",
    "applicant_sex",
    "state_code",
    "county_code",
    "lei",
    "activity_year",
)
_RECORD_COLUMNS = (
    "record_id",
    "source_row_number",
    "source_line_number",
    *HMDA_BUSINESS_COLUMNS,
)
_RECORD_COLUMN_SQL = ", ".join(_RECORD_COLUMNS)
_STAGING_COPY_SQL = (
    "COPY hmda_staging.hmda_record "
    f"(ingestion_id, {_RECORD_COLUMN_SQL}) FROM STDIN"
)
_PROMOTE_SQL = f"""
    INSERT INTO hmda_raw.hmda_record (snapshot_id, {_RECORD_COLUMN_SQL})
    SELECT run.snapshot_id, {_RECORD_COLUMN_SQL}
    FROM hmda_staging.hmda_record AS staged
    JOIN hmda_audit.ingestion_run AS run
      ON run.ingestion_id = staged.ingestion_id
    WHERE staged.ingestion_id = %s
    ON CONFLICT (snapshot_id, record_id) DO NOTHING
"""
_STAGING_RECORDS_SQL = f"""
    SELECT {_RECORD_COLUMN_SQL}
    FROM hmda_staging.hmda_record
    WHERE ingestion_id = %s
    ORDER BY source_row_number
"""
_RAW_RECORDS_SQL = f"""
    SELECT {_RECORD_COLUMN_SQL}
    FROM hmda_raw.hmda_record
    WHERE snapshot_id = %s
    ORDER BY source_row_number
"""
_READY_RECORDS_SQL = f"""
    SELECT {_RECORD_COLUMN_SQL}
    FROM hmda_raw.ready_hmda_record
    WHERE snapshot_id = %s
    ORDER BY source_row_number
"""


@dataclass(frozen=True, slots=True)
class PostgresSettings:
    host: str
    port: int
    database: str
    username: str
    password: str = field(repr=False)
    sslmode: str = "require"
    channel_binding: str = "require"

    @classmethod
    def from_config(cls, config: ConfigBundle) -> "PostgresSettings":
        connection = config.get("database.connection")
        if not isinstance(connection, Mapping):
            raise ConfigurationError(
                "Thiếu cấu hình kết nối database",
                field_path="database.connection",
            )

        required = ("host", "port", "database", "username", "password")
        missing = [name for name in required if connection.get(name) in (None, "")]
        if missing:
            raise ConfigurationError(
                f"Thiếu trường kết nối bắt buộc: {', '.join(sorted(missing))}",
                field_path="database.connection",
            )
        try:
            port = int(connection["port"])
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Port database phải là số nguyên",
                field_path="database.connection.port",
            ) from exc

        return cls(
            host=str(connection["host"]),
            port=port,
            database=str(connection["database"]),
            username=str(connection["username"]),
            password=str(connection["password"]),
            sslmode=str(connection.get("sslmode") or "require"),
            channel_binding=str(connection.get("channel_binding") or "require"),
        )

    def connect_kwargs(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.username,
            "password": self.password,
            "sslmode": self.sslmode,
            "channel_binding": self.channel_binding,
            "connect_timeout": 10,
            "autocommit": False,
            "row_factory": dict_row,
        }


def make_connection_factory(settings: PostgresSettings) -> ConnectionFactory:
    """Tạo factory; không mở kết nối cho tới khi caller thực sự gọi."""

    def factory() -> Any:
        return psycopg.connect(**settings.connect_kwargs())

    return factory


class PostgresMigrationRunner:
    """Áp dụng migration forward theo thứ tự tên file trong một transaction."""

    def __init__(self, connection_factory: ConnectionFactory, migration_dir: Path) -> None:
        self.connection_factory = connection_factory
        self.migration_dir = Path(migration_dir)

    def discover(self) -> tuple[Path, ...]:
        if not self.migration_dir.is_dir():
            raise RepositoryError("Không tìm thấy thư mục migration")
        migrations = tuple(sorted(self.migration_dir.glob("*.up.sql")))
        if not migrations:
            raise RepositoryError("Không có migration forward")
        return migrations

    def apply_all(self) -> tuple[str, ...]:
        migrations = self.discover()
        connection = self._open_connection()
        applied: list[str] = []
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (_MIGRATION_LOCK_ID,),
                )
                cursor.execute("CREATE SCHEMA IF NOT EXISTS hmda_audit")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS hmda_audit.schema_migration (
                        version TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute("SELECT version FROM hmda_audit.schema_migration")
                existing = {row["version"] for row in cursor.fetchall()}
                for path in migrations:
                    version = path.name.removesuffix(".up.sql")
                    if version in existing:
                        continue
                    cursor.execute(path.read_text(encoding="utf-8"))
                    cursor.execute(
                        """
                        INSERT INTO hmda_audit.schema_migration (version)
                        VALUES (%s)
                        ON CONFLICT (version) DO NOTHING
                        """,
                        (version,),
                    )
                    applied.append(version)
            connection.commit()
            return tuple(applied)
        except (OSError, UnicodeError, psycopg.Error):
            connection.rollback()
            raise RepositoryError("Áp dụng PostgreSQL migration thất bại") from None
        finally:
            connection.close()

    def _open_connection(self) -> Any:
        try:
            return self.connection_factory()
        except psycopg.Error:
            raise RepositoryError("Không thể mở kết nối PostgreSQL") from None


class PostgresRepository:
    """PostgreSQL implementation của DataRepository contract."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def transaction(self) -> "PostgresUnitOfWork":
        try:
            connection = self.connection_factory()
        except psycopg.Error:
            raise RepositoryError("Không thể mở kết nối PostgreSQL") from None
        return PostgresUnitOfWork(connection)

    def get_ingestion_by_key(
        self,
        idempotency_key: str,
    ) -> IngestionDescriptor | None:
        """Đọc trạng thái logical ingestion để retry không tạo run mới."""

        connection = None
        try:
            connection = self.connection_factory()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT ingestion_id, snapshot_id, idempotency_key, source_id, status
                    FROM hmda_audit.ingestion_run
                    WHERE idempotency_key = %s
                    """,
                    (idempotency_key,),
                )
                row = cursor.fetchone()
        except psycopg.Error:
            raise RepositoryError("Không thể đọc ingestion PostgreSQL") from None
        finally:
            if connection is not None:
                connection.close()
        return None if row is None else _ingestion_descriptor(row)

    def get_ready(self, snapshot_id: str) -> SnapshotDescriptor:
        connection = None
        try:
            connection = self.connection_factory()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT snapshot_id, status, source_id, metadata
                    FROM hmda_audit.ready_snapshot
                    WHERE snapshot_id = %s
                    """,
                    (snapshot_id,),
                )
                row = cursor.fetchone()
        except psycopg.Error:
            raise RepositoryError("Không thể đọc snapshot PostgreSQL") from None
        finally:
            if connection is not None:
                connection.close()
        if row is None:
            raise RepositoryError("Snapshot không READY hoặc không tồn tại")
        return _snapshot_descriptor(row)

    def get_ready_records(self, snapshot_id: str) -> tuple[dict[str, object], ...]:
        """Đọc record của đúng snapshot READY theo thứ tự lineage."""

        connection = None
        try:
            connection = self.connection_factory()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM hmda_audit.ready_snapshot WHERE snapshot_id = %s",
                    (snapshot_id,),
                )
                if cursor.fetchone() is None:
                    raise RepositoryError("Snapshot không READY hoặc không tồn tại")
                cursor.execute(_READY_RECORDS_SQL, (snapshot_id,))
                records = tuple(dict(row) for row in cursor.fetchall())
        except psycopg.Error:
            raise RepositoryError("Không thể đọc record READY từ PostgreSQL") from None
        finally:
            if connection is not None:
                connection.close()
        summarize_record_set(records, business_columns=HMDA_BUSINESS_COLUMNS)
        return records

    def cleanup_ready_staging(
        self,
        ingestion_id: str,
        expected_row_count: int,
    ) -> int:
        """Dọn staging còn sót của đúng ingestion READY; retry là no-op an toàn."""

        if (
            isinstance(expected_row_count, bool)
            or not isinstance(expected_row_count, int)
            or expected_row_count < 1
        ):
            raise RepositoryError("expected_row_count phải là số nguyên dương")
        connection = None
        try:
            connection = self.connection_factory()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        run.status,
                        (
                            SELECT COUNT(*)
                            FROM hmda_staging.hmda_record AS staged
                            WHERE staged.ingestion_id = run.ingestion_id
                        ) AS staging_row_count
                    FROM hmda_audit.ingestion_run AS run
                    WHERE run.ingestion_id = %s
                    """,
                    (ingestion_id,),
                )
                row = cursor.fetchone()
                if row is None or row["status"] != "READY":
                    raise RepositoryError("Cleanup staging chỉ áp dụng cho ingestion READY")
                staging_row_count = int(row["staging_row_count"])
                if staging_row_count == 0:
                    connection.rollback()
                    return 0
                if staging_row_count != expected_row_count:
                    raise RepositoryError("Staging row_count không khớp evidence READY")
                cursor.execute(
                    "DELETE FROM hmda_staging.hmda_record WHERE ingestion_id = %s",
                    (ingestion_id,),
                )
                if cursor.rowcount != expected_row_count:
                    raise RepositoryError("Cleanup staging không xóa đúng số dòng dự kiến")
            connection.commit()
            return expected_row_count
        except psycopg.Error:
            if connection is not None:
                connection.rollback()
            raise RepositoryError("Không thể cleanup staging PostgreSQL") from None
        except Exception:
            if connection is not None:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()


class PostgresUnitOfWork:
    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.closed = False

    def __enter__(self) -> "PostgresUnitOfWork":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        if not self.closed:
            self.rollback()
        return False

    def register_source(self, source: SourceIdentity) -> None:
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                """
                INSERT INTO hmda_audit.source_file (
                    source_id, source_version, checksum, byte_size, identity_algorithm
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO NOTHING
                """,
                (
                    source.source_id,
                    source.version,
                    source.checksum,
                    source.byte_size,
                    source.algorithm,
                ),
                operation="đăng ký source",
            )
            self._execute(
                cursor,
                """
                SELECT source_version, checksum, byte_size, identity_algorithm
                FROM hmda_audit.source_file
                WHERE source_id = %s
                """,
                (source.source_id,),
                operation="đọc source",
            )
            row = cursor.fetchone()
        expected = {
            "source_version": source.version,
            "checksum": source.checksum,
            "byte_size": source.byte_size,
            "identity_algorithm": source.algorithm,
        }
        if row is None or any(row.get(key) != value for key, value in expected.items()):
            raise RepositoryError("source_id đã thuộc identity khác")

    def begin_ingestion(self, request: IngestionRequest) -> IngestionDescriptor:
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                (request.idempotency_key,),
                operation="khóa ingestion",
            )
            self._execute(
                cursor,
                """
                SELECT ingestion_id, snapshot_id, idempotency_key, source_id, status
                FROM hmda_audit.ingestion_run
                WHERE idempotency_key = %s
                """,
                (request.idempotency_key,),
                operation="đọc ingestion",
            )
            existing = cursor.fetchone()
            if existing is not None:
                return _ingestion_descriptor(existing)

            identity = request.identity
            self._execute(
                cursor,
                """
                INSERT INTO hmda_audit.ingestion_run (
                    ingestion_id, snapshot_id, idempotency_key,
                    source_id, source_version, source_checksum,
                    schema_version, config_hash, transform_version, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'STAGING')
                RETURNING ingestion_id, snapshot_id, idempotency_key, source_id, status
                """,
                (
                    request.ingestion_id,
                    request.snapshot_id,
                    request.idempotency_key,
                    identity.source_id,
                    identity.source_version,
                    identity.source_checksum,
                    identity.schema_version,
                    identity.config_hash,
                    identity.transform_version,
                ),
                operation="tạo ingestion",
            )
            created = cursor.fetchone()
        if created is None:
            raise RepositoryError("Không tạo được ingestion")
        return _ingestion_descriptor(created)

    def stage_records(
        self,
        ingestion_id: str,
        records: Sequence[Mapping[str, object]],
    ) -> RecordSetSummary:
        """COPY record vào staging và đối soát lại trước khi tiếp tục."""

        self._require_staging(ingestion_id)
        expected = summarize_record_set(
            records, business_columns=HMDA_BUSINESS_COLUMNS
        )
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                "SELECT COUNT(*) AS row_count FROM hmda_staging.hmda_record "
                "WHERE ingestion_id = %s",
                (ingestion_id,),
                operation="đếm record staging",
            )
            count_row = cursor.fetchone()
            existing_count = int(count_row["row_count"]) if count_row else 0
            if existing_count == 0:
                try:
                    with cursor.copy(_STAGING_COPY_SQL) as copy:
                        for record in records:
                            copy.write_row(
                                (
                                    ingestion_id,
                                    *(record[column] for column in _RECORD_COLUMNS),
                                )
                            )
                except psycopg.Error:
                    raise RepositoryError("PostgreSQL không thể COPY record staging") from None
        actual = self._summarize_query(
            _STAGING_RECORDS_SQL,
            (ingestion_id,),
            operation="đọc lại record staging",
        )
        require_reconciled_record_sets(expected, actual)
        return actual

    def promote_records(
        self,
        ingestion_id: str,
        expected: RecordSetSummary,
    ) -> RecordSetSummary:
        """Chuyển staging sang raw và đối soát nội dung trong cùng transaction."""

        ingestion = self._require_staging(ingestion_id)
        staged_summary = self._summarize_query(
            _STAGING_RECORDS_SQL,
            (ingestion_id,),
            operation="đọc record staging trước promote",
        )
        require_reconciled_record_sets(expected, staged_summary)
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                _PROMOTE_SQL,
                (ingestion_id,),
                operation="promote record sang raw",
            )
        raw_summary = self._summarize_query(
            _RAW_RECORDS_SQL,
            (ingestion.snapshot_id,),
            operation="đọc lại record raw",
        )
        require_reconciled_record_sets(expected, raw_summary)
        return raw_summary

    def read_promoted_records(
        self, ingestion_id: str
    ) -> tuple[dict[str, object], ...]:
        """Đọc record raw của ingestion STAGING để tạo file snapshot trước publish."""

        ingestion = self._require_staging(ingestion_id)
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                _RAW_RECORDS_SQL,
                (ingestion.snapshot_id,),
                operation="đọc record raw cho snapshot",
            )
            records = tuple(dict(row) for row in cursor.fetchall())
        summarize_record_set(records, business_columns=HMDA_BUSINESS_COLUMNS)
        return records

    def clear_staged_records(
        self,
        ingestion_id: str,
        expected_row_count: int,
    ) -> int:
        """Xóa staging sau đối soát, trong cùng transaction với publish READY."""

        self._require_staging(ingestion_id)
        if (
            isinstance(expected_row_count, bool)
            or not isinstance(expected_row_count, int)
            or expected_row_count < 1
        ):
            raise RepositoryError("expected_row_count phải là số nguyên dương")
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                "SELECT COUNT(*) AS row_count FROM hmda_staging.hmda_record "
                "WHERE ingestion_id = %s",
                (ingestion_id,),
                operation="đếm record staging trước cleanup",
            )
            row = cursor.fetchone()
            actual_count = int(row["row_count"]) if row else 0
            if actual_count != expected_row_count:
                raise RepositoryError("Staging row_count không khớp trước cleanup")
            self._execute(
                cursor,
                "DELETE FROM hmda_staging.hmda_record WHERE ingestion_id = %s",
                (ingestion_id,),
                operation="cleanup record staging",
            )
            if cursor.rowcount != expected_row_count:
                raise RepositoryError("Cleanup staging không xóa đúng số dòng dự kiến")
        return expected_row_count

    def save_quality_result(
        self, ingestion_id: str, validation: ValidationSummary
    ) -> None:
        self._require_staging(ingestion_id)
        metadata = dict(validation.metadata)
        issues = [_json_compatible(issue) for issue in validation.issues]
        reported_error_count = int(
            metadata.get("error_count", int(not validation.is_valid))
        )
        error_count = 0 if validation.is_valid else max(1, reported_error_count)
        warning_count = int(metadata.get("warning_count", 0))
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                """
                INSERT INTO hmda_audit.quality_result (
                    ingestion_id, is_valid, error_count, warning_count, metadata, issues
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (ingestion_id) DO UPDATE SET
                    is_valid = EXCLUDED.is_valid,
                    error_count = EXCLUDED.error_count,
                    warning_count = EXCLUDED.warning_count,
                    metadata = EXCLUDED.metadata,
                    issues = EXCLUDED.issues,
                    recorded_at = CURRENT_TIMESTAMP
                """,
                (
                    ingestion_id,
                    validation.is_valid,
                    error_count,
                    warning_count,
                    Jsonb(metadata),
                    Jsonb(issues),
                ),
                operation="lưu quality result",
            )

    def stage_snapshot(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None:
        ingestion = self._require_staging(ingestion_id)
        if snapshot.status is not SnapshotStatus.STAGING:
            raise RepositoryError("stage_snapshot yêu cầu descriptor STAGING")
        if (
            snapshot.snapshot_id != ingestion.snapshot_id
            or snapshot.source_id != ingestion.source_id
        ):
            raise RepositoryError("Snapshot không khớp ingestion identity")
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                """
                INSERT INTO hmda_audit.snapshot (
                    snapshot_id, ingestion_id, source_id, status, metadata
                ) VALUES (%s, %s, %s, 'STAGING', %s)
                ON CONFLICT (snapshot_id) DO NOTHING
                """,
                (
                    snapshot.snapshot_id,
                    ingestion_id,
                    snapshot.source_id,
                    Jsonb(dict(snapshot.metadata)),
                ),
                operation="stage snapshot",
            )
            self._execute(
                cursor,
                """
                SELECT snapshot_id, ingestion_id, source_id, status
                FROM hmda_audit.snapshot
                WHERE snapshot_id = %s
                """,
                (snapshot.snapshot_id,),
                operation="đọc staged snapshot",
            )
            staged = cursor.fetchone()
        expected = {
            "snapshot_id": snapshot.snapshot_id,
            "ingestion_id": ingestion_id,
            "source_id": snapshot.source_id,
            "status": "STAGING",
        }
        if staged is None or any(
            staged.get(key) != value for key, value in expected.items()
        ):
            raise RepositoryError("snapshot_id đã thuộc ingestion khác")

    def mark_failed(self, ingestion_id: str, *, reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise RepositoryError("Failure reason không được rỗng")
        self._require_staging(ingestion_id)
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                """
                UPDATE hmda_audit.ingestion_run
                SET status = 'FAILED', failure_reason = %s, updated_at = CURRENT_TIMESTAMP
                WHERE ingestion_id = %s AND status = 'STAGING'
                """,
                (reason, ingestion_id),
                operation="đánh dấu ingestion FAILED",
            )
            self._execute(
                cursor,
                """
                UPDATE hmda_audit.snapshot
                SET status = 'FAILED', updated_at = CURRENT_TIMESTAMP
                WHERE ingestion_id = %s AND status = 'STAGING'
                """,
                (ingestion_id,),
                operation="đánh dấu snapshot FAILED",
            )

    def publish_ready(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None:
        ingestion = self._require_staging(ingestion_id)
        if snapshot.status is not SnapshotStatus.READY:
            raise RepositoryError("publish_ready yêu cầu filesystem snapshot READY")
        if (
            snapshot.snapshot_id != ingestion.snapshot_id
            or snapshot.source_id != ingestion.source_id
        ):
            raise RepositoryError("READY snapshot không khớp ingestion identity")

        with self.connection.cursor() as cursor:
            expected_row_count = snapshot.metadata.get("row_count")
            if (
                isinstance(expected_row_count, bool)
                or not isinstance(expected_row_count, int)
                or expected_row_count < 1
            ):
                raise RepositoryError("READY snapshot phải có row_count dương")
            self._execute(
                cursor,
                """
                SELECT
                    quality.is_valid,
                    staged.status,
                    (
                        SELECT COUNT(*)
                        FROM hmda_raw.hmda_record AS records
                        WHERE records.snapshot_id = staged.snapshot_id
                    ) AS raw_row_count
                FROM hmda_audit.quality_result AS quality
                JOIN hmda_audit.snapshot AS staged
                    ON staged.ingestion_id = quality.ingestion_id
                WHERE quality.ingestion_id = %s
                """,
                (ingestion_id,),
                operation="kiểm điều kiện publish",
            )
            state = cursor.fetchone()
            if state is None or not state["is_valid"]:
                raise RepositoryError("Quality ERROR hoặc thiếu quality result chặn publish")
            if state["status"] != "STAGING":
                raise RepositoryError("Chưa có staged snapshot hợp lệ")
            if int(state["raw_row_count"]) != expected_row_count:
                raise RepositoryError("Raw row_count không khớp filesystem snapshot")

            self._execute(
                cursor,
                """
                UPDATE hmda_audit.snapshot
                SET status = 'READY', metadata = %s, updated_at = CURRENT_TIMESTAMP
                WHERE ingestion_id = %s AND status = 'STAGING'
                """,
                (Jsonb(dict(snapshot.metadata)), ingestion_id),
                operation="publish snapshot READY",
            )
            self._execute(
                cursor,
                """
                UPDATE hmda_audit.ingestion_run
                SET status = 'READY', updated_at = CURRENT_TIMESTAMP
                WHERE ingestion_id = %s AND status = 'STAGING'
                """,
                (ingestion_id,),
                operation="publish ingestion READY",
            )

    def commit(self) -> None:
        self._require_open()
        try:
            self.connection.commit()
        except psycopg.Error:
            raise RepositoryError("Commit PostgreSQL thất bại") from None
        finally:
            self.connection.close()
            self.closed = True

    def rollback(self) -> None:
        if self.closed:
            return
        try:
            self.connection.rollback()
        except psycopg.Error:
            raise RepositoryError("Rollback PostgreSQL thất bại") from None
        finally:
            self.connection.close()
            self.closed = True

    def _require_staging(self, ingestion_id: str) -> IngestionDescriptor:
        self._require_open()
        with self.connection.cursor() as cursor:
            self._execute(
                cursor,
                """
                SELECT ingestion_id, snapshot_id, idempotency_key, source_id, status
                FROM hmda_audit.ingestion_run
                WHERE ingestion_id = %s
                """,
                (ingestion_id,),
                operation="đọc trạng thái ingestion",
            )
            row = cursor.fetchone()
        if row is None:
            raise RepositoryError("Ingestion không tồn tại")
        descriptor = _ingestion_descriptor(row)
        if descriptor.status is not IngestionStatus.STAGING:
            raise RepositoryError("Ingestion không còn ở STAGING")
        return descriptor

    def _require_open(self) -> None:
        if self.closed:
            raise RepositoryError("Unit of work không còn mở")

    def _summarize_query(
        self,
        statement: str,
        params: tuple[Any, ...],
        *,
        operation: str,
    ) -> RecordSetSummary:
        """Stream record từ server để đối soát không nhân đôi toàn bộ dataset."""

        self._require_open()
        try:
            cursor_name = f"hmda_reconcile_{uuid4().hex}"
            with self.connection.cursor(name=cursor_name) as cursor:
                cursor.itersize = 10_000
                cursor.execute(statement, params)
                return summarize_record_set(
                    cursor,
                    business_columns=HMDA_BUSINESS_COLUMNS,
                )
        except psycopg.Error:
            raise RepositoryError(f"PostgreSQL không thể {operation}") from None

    def _execute(
        self,
        cursor: Any,
        statement: str,
        params: tuple[Any, ...],
        *,
        operation: str,
    ) -> None:
        self._require_open()
        try:
            cursor.execute(statement, params)
        except psycopg.Error:
            raise RepositoryError(f"PostgreSQL không thể {operation}") from None


def _ingestion_descriptor(row: Mapping[str, Any]) -> IngestionDescriptor:
    return IngestionDescriptor(
        ingestion_id=str(row["ingestion_id"]),
        snapshot_id=str(row["snapshot_id"]),
        idempotency_key=str(row["idempotency_key"]),
        source_id=str(row["source_id"]),
        status=IngestionStatus(str(row["status"])),
    )


def _snapshot_descriptor(row: Mapping[str, Any]) -> SnapshotDescriptor:
    return SnapshotDescriptor(
        snapshot_id=str(row["snapshot_id"]),
        status=SnapshotStatus(str(row["status"])),
        source_id=str(row["source_id"]),
        metadata=dict(row["metadata"] or {}),
    )


def _json_compatible(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_compatible(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_compatible(item) for item in value]
    return value
