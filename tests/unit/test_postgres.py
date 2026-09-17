from pathlib import Path

import pytest
import yaml

from hmda.core.config import ConfigBundle
from hmda.core.exceptions import RepositoryError
from hmda.data.contracts import SnapshotDescriptor, SnapshotStatus
from hmda.data.postgres import (
    HMDA_BUSINESS_COLUMNS,
    PostgresMigrationRunner,
    PostgresRepository,
    PostgresSettings,
    PostgresUnitOfWork,
    make_connection_factory,
)
from hmda.data.repository import (
    IdempotencyIdentity,
    IngestionRequest,
    summarize_record_set,
)


class ScriptedCopy:
    def __init__(self, connection, statement) -> None:
        self.connection = connection
        self.statement = str(statement)

    def __enter__(self):
        self.connection.copy_statements.append(self.statement)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def write_row(self, row) -> None:
        self.connection.copied_rows.append(tuple(row))


class ScriptedCursor:
    def __init__(self, connection) -> None:
        self.connection = connection
        self.rows = []
        self.rowcount = -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __iter__(self):
        return iter(self.rows)

    def execute(self, statement, params=()) -> None:
        self.connection.statements.append((str(statement), params))
        self.rows = self.connection.responses.pop(0) if self.connection.responses else []
        self.rowcount = (
            self.connection.rowcounts.pop(0)
            if self.connection.rowcounts
            else len(self.rows)
        )

    def copy(self, statement):
        return ScriptedCopy(self.connection, statement)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class ScriptedConnection:
    def __init__(self, responses=None, rowcounts=None) -> None:
        self.responses = list(responses or [])
        self.rowcounts = list(rowcounts or [])
        self.statements = []
        self.copy_statements = []
        self.copied_rows = []
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, *args, **kwargs):
        return ScriptedCursor(self)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


def _settings_bundle() -> ConfigBundle:
    return ConfigBundle(
        values={
            "database": {
                "connection": {
                    "host": "fixture.neon.tech",
                    "port": "5432",
                    "database": "fixture",
                    "username": "fixture_user",
                    "password": "fixture-secret",
                    "sslmode": "require",
                    "channel_binding": "require",
                }
            }
        },
        sources=(),
        secret_paths=frozenset({("database", "connection", "password")}),
    )


def _request() -> IngestionRequest:
    identity = IdempotencyIdentity(
        source_id="fixture-source",
        source_version="v1",
        source_checksum="a" * 64,
        schema_version="schema-v1",
        config_hash="b" * 64,
        transform_version="transform-v1",
    )
    return IngestionRequest.create(
        ingestion_id="fixture-ingestion",
        snapshot_id="fixture-snapshot",
        identity=identity,
    )


def _records():
    records = []
    for number in (1, 2):
        record = {
            "record_id": f"{number:064x}",
            "source_row_number": number,
            "source_line_number": number + 1,
        }
        record.update(
            {column: f"{column}-{number}" for column in HMDA_BUSINESS_COLUMNS}
        )
        records.append(record)
    return tuple(records)


def _staging_descriptor():
    request = _request()
    return {
        "ingestion_id": request.ingestion_id,
        "snapshot_id": request.snapshot_id,
        "idempotency_key": request.idempotency_key,
        "source_id": request.identity.source_id,
        "status": "STAGING",
    }


def test_postgres_settings_keep_password_out_of_repr_and_factory_is_lazy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = PostgresSettings.from_config(_settings_bundle())
    calls = []
    sentinel = object()

    def fake_connect(**kwargs):
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr("hmda.data.postgres.psycopg.connect", fake_connect)
    factory = make_connection_factory(settings)

    assert calls == []
    assert "fixture-secret" not in repr(settings)
    assert factory() is sentinel
    assert calls[0]["password"] == "fixture-secret"
    assert calls[0]["sslmode"] == "require"
    assert calls[0]["channel_binding"] == "require"
    assert calls[0]["connect_timeout"] == 10


def test_migration_runner_discovers_only_forward_files_and_records_version(
    tmp_path: Path,
) -> None:
    (tmp_path / "002_second.up.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "001_first.up.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "001_first.down.sql").write_text("SELECT 0;", encoding="utf-8")
    connection = ScriptedConnection(responses=[[], [], [], []])
    runner = PostgresMigrationRunner(lambda: connection, tmp_path)

    assert [path.name for path in runner.discover()] == [
        "001_first.up.sql",
        "002_second.up.sql",
    ]
    assert runner.apply_all() == ("001_first", "002_second")
    assert connection.committed
    assert connection.closed
    executed = "\n".join(statement for statement, _ in connection.statements)
    assert "SELECT 1;" in executed
    assert "SELECT 2;" in executed


def test_ready_reader_uses_ready_view_and_closes_connection() -> None:
    connection = ScriptedConnection(
        responses=[
            [
                {
                    "snapshot_id": "fixture-snapshot",
                    "status": "READY",
                    "source_id": "fixture-source",
                    "metadata": {"row_count": 3},
                }
            ]
        ]
    )
    repository = PostgresRepository(lambda: connection)

    snapshot = repository.get_ready("fixture-snapshot")

    assert snapshot.status is SnapshotStatus.READY
    assert snapshot.metadata == {"row_count": 3}
    assert connection.closed
    assert "hmda_audit.ready_snapshot" in connection.statements[0][0]


def test_get_ingestion_by_key_returns_status_or_none() -> None:
    request = _request()
    found_connection = ScriptedConnection(responses=[[_staging_descriptor()]])
    found_repository = PostgresRepository(lambda: found_connection)

    found = found_repository.get_ingestion_by_key(request.idempotency_key)

    assert found is not None
    assert found.ingestion_id == request.ingestion_id
    assert found.status.value == "STAGING"
    assert found_connection.closed

    missing_connection = ScriptedConnection(responses=[[]])
    missing_repository = PostgresRepository(lambda: missing_connection)
    assert missing_repository.get_ingestion_by_key(request.idempotency_key) is None
    assert missing_connection.closed


def test_ready_record_reader_uses_ready_view_and_preserves_order() -> None:
    records = _records()
    connection = ScriptedConnection(responses=[[{"exists": 1}], list(records)])
    repository = PostgresRepository(lambda: connection)

    readback = repository.get_ready_records("fixture-snapshot")

    assert readback == records
    assert connection.closed
    assert "hmda_raw.ready_hmda_record" in connection.statements[1][0]
    assert "ORDER BY source_row_number" in connection.statements[1][0]


def test_stage_records_copies_and_reconciles_readback() -> None:
    records = _records()
    connection = ScriptedConnection(
        responses=[[_staging_descriptor()], [{"row_count": 0}], list(records)]
    )
    unit = PostgresUnitOfWork(connection)

    summary = unit.stage_records("fixture-ingestion", records)
    unit.rollback()

    assert summary.row_count == 2
    assert len(connection.copy_statements) == 1
    assert len(connection.copied_rows) == 2
    assert connection.copied_rows[0][0] == "fixture-ingestion"
    assert len(connection.copied_rows[0]) == 22


def test_stage_records_retry_reconciles_without_copying_again() -> None:
    records = _records()
    connection = ScriptedConnection(
        responses=[[_staging_descriptor()], [{"row_count": 2}], list(records)]
    )
    unit = PostgresUnitOfWork(connection)

    summary = unit.stage_records("fixture-ingestion", records)
    unit.rollback()

    assert summary.row_count == 2
    assert connection.copy_statements == []
    assert connection.copied_rows == []


def test_promote_records_reconciles_staging_and_raw() -> None:
    records = _records()
    expected = summarize_record_set(
        records, business_columns=HMDA_BUSINESS_COLUMNS
    )
    connection = ScriptedConnection(
        responses=[[_staging_descriptor()], list(records), [], list(records)]
    )
    unit = PostgresUnitOfWork(connection)

    summary = unit.promote_records("fixture-ingestion", expected)
    unit.rollback()

    assert summary == expected
    executed = "\n".join(statement for statement, _ in connection.statements)
    assert "INSERT INTO hmda_raw.hmda_record" in executed
    assert "ON CONFLICT (snapshot_id, record_id) DO NOTHING" in executed


def test_clear_staged_records_deletes_exact_expected_count() -> None:
    connection = ScriptedConnection(
        responses=[[_staging_descriptor()], [{"row_count": 2}], []],
        rowcounts=[1, 1, 2],
    )
    unit = PostgresUnitOfWork(connection)

    deleted = unit.clear_staged_records("fixture-ingestion", 2)
    unit.rollback()

    assert deleted == 2
    assert "DELETE FROM hmda_staging.hmda_record" in connection.statements[-1][0]


def test_cleanup_ready_staging_is_scoped_and_idempotent() -> None:
    ready_state = {"status": "READY", "staging_row_count": 2}
    cleanup_connection = ScriptedConnection(
        responses=[[ready_state], []],
        rowcounts=[1, 2],
    )
    repository = PostgresRepository(lambda: cleanup_connection)

    assert repository.cleanup_ready_staging("fixture-ingestion", 2) == 2
    assert cleanup_connection.committed
    assert cleanup_connection.closed

    empty_connection = ScriptedConnection(
        responses=[[{"status": "READY", "staging_row_count": 0}]],
    )
    repository = PostgresRepository(lambda: empty_connection)
    assert repository.cleanup_ready_staging("fixture-ingestion", 2) == 0
    assert empty_connection.rolled_back
    assert empty_connection.closed


def test_publish_ready_rejects_raw_row_count_mismatch() -> None:
    connection = ScriptedConnection(
        responses=[
            [_staging_descriptor()],
            [{"is_valid": True, "status": "STAGING", "raw_row_count": 1}],
        ]
    )
    unit = PostgresUnitOfWork(connection)

    with pytest.raises(RepositoryError, match="Raw row_count"):
        unit.publish_ready(
            "fixture-ingestion",
            SnapshotDescriptor(
                snapshot_id="fixture-snapshot",
                source_id="fixture-source",
                status=SnapshotStatus.READY,
                metadata={"row_count": 2},
            ),
        )
    unit.rollback()


def test_retry_uses_existing_idempotent_ingestion() -> None:
    request = _request()
    connection = ScriptedConnection(
        responses=[
            [],
            [
                {
                    "ingestion_id": request.ingestion_id,
                    "snapshot_id": request.snapshot_id,
                    "idempotency_key": request.idempotency_key,
                    "source_id": request.identity.source_id,
                    "status": "STAGING",
                }
            ],
        ]
    )
    unit = PostgresUnitOfWork(connection)

    descriptor = unit.begin_ingestion(request)
    unit.rollback()

    assert descriptor.ingestion_id == request.ingestion_id
    assert connection.rolled_back
    assert connection.closed
    assert not any(
        "INSERT INTO hmda_audit.ingestion_run" in statement
        for statement, _ in connection.statements
    )


def test_phase2_sql_matches_raw_contract_and_reader_is_ready_only() -> None:
    project_root = Path(__file__).resolve().parents[2]
    schema = yaml.safe_load(
        (project_root / "configs" / "schema.yaml").read_text(encoding="utf-8")
    )
    schema_sql = (
        project_root / "sql" / "migrations" / "001_hmda_phase2_schema.up.sql"
    ).read_text(encoding="utf-8")
    permission_sql = (
        project_root / "sql" / "migrations" / "002_hmda_phase2_permissions.up.sql"
    ).read_text(encoding="utf-8")

    for column in schema["column_order"]:
        assert f"    {column} TEXT NOT NULL" in schema_sql
    assert tuple(schema["column_order"]) == HMDA_BUSINESS_COLUMNS
    assert "action_taken IN ('0', '1', '2')" in schema_sql
    assert "WHERE status = 'READY'" in schema_sql
    assert "GRANT SELECT ON hmda_audit.ready_snapshot" in permission_sql
    assert "GRANT SELECT ON hmda_raw.hmda_record TO hmda_reader" not in permission_sql
    assert "postgresql://" not in (schema_sql + permission_sql).lower()


def test_stage_snapshot_rejects_snapshot_id_owned_by_another_ingestion() -> None:
    request = _request()
    connection = ScriptedConnection(
        responses=[
            [
                {
                    "ingestion_id": request.ingestion_id,
                    "snapshot_id": request.snapshot_id,
                    "idempotency_key": request.idempotency_key,
                    "source_id": request.identity.source_id,
                    "status": "STAGING",
                }
            ],
            [],
            [
                {
                    "snapshot_id": request.snapshot_id,
                    "ingestion_id": "other-ingestion",
                    "source_id": request.identity.source_id,
                    "status": "STAGING",
                }
            ],
        ]
    )
    unit = PostgresUnitOfWork(connection)

    with pytest.raises(RepositoryError, match="đã thuộc ingestion khác"):
        unit.stage_snapshot(
            request.ingestion_id,
            snapshot=SnapshotDescriptor(
                snapshot_id=request.snapshot_id,
                source_id=request.identity.source_id,
                status=SnapshotStatus.STAGING,
            ),
        )
    unit.rollback()
