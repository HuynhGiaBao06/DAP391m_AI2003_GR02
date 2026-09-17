import os
from pathlib import Path

import psycopg
import pytest


pytestmark = pytest.mark.integration


def test_migrations_and_reader_acl_on_explicit_test_database() -> None:
    required_variables = (
        "HMDA_TEST_DB_HOST",
        "HMDA_TEST_DB_PORT",
        "HMDA_TEST_DB_NAME",
        "HMDA_TEST_DB_USER",
        "HMDA_TEST_DB_PASSWORD",
    )
    missing = [name for name in required_variables if not os.environ.get(name)]
    allow_ddl = os.environ.get("HMDA_TEST_ALLOW_DDL")
    if missing or allow_ddl != "YES":
        pytest.skip(
            "Cần đủ HMDA_TEST_DB_* và HMDA_TEST_ALLOW_DDL=YES cho DB test tách biệt"
        )

    project_root = Path(__file__).resolve().parents[2]
    migration_dir = project_root / "sql" / "migrations"
    up_paths = sorted(migration_dir.glob("*.up.sql"))
    down_paths = sorted(migration_dir.glob("*.down.sql"), reverse=True)

    try:
        connection = psycopg.connect(
            host=os.environ["HMDA_TEST_DB_HOST"],
            port=int(os.environ["HMDA_TEST_DB_PORT"]),
            dbname=os.environ["HMDA_TEST_DB_NAME"],
            user=os.environ["HMDA_TEST_DB_USER"],
            password=os.environ["HMDA_TEST_DB_PASSWORD"],
            sslmode=os.environ.get("HMDA_TEST_DB_SSLMODE", "require"),
            channel_binding=os.environ.get(
                "HMDA_TEST_DB_CHANNEL_BINDING", "require"
            ),
            connect_timeout=10,
            autocommit=False,
        )
    except psycopg.Error as exc:
        safe_message = str(exc).replace(
            os.environ["HMDA_TEST_DB_PASSWORD"], "***REDACTED***"
        )
        pytest.fail(
            f"Không thể kết nối PostgreSQL test: {safe_message}",
            pytrace=False,
        )

    with connection:
        try:
            with connection.cursor() as cursor:
                for path in up_paths:
                    cursor.execute(path.read_text(encoding="utf-8"))

                cursor.execute("SELECT to_regclass('hmda_raw.hmda_record')")
                assert cursor.fetchone()[0] == "hmda_raw.hmda_record"
                cursor.execute(
                    """
                    INSERT INTO hmda_audit.source_file (
                        source_id, source_version, checksum, byte_size,
                        identity_algorithm
                    ) VALUES ('acl-fixture', 'v1', %s, 1, 'fixture')
                    """,
                    ("a" * 64,),
                )
                cursor.execute(
                    """
                    INSERT INTO hmda_audit.ingestion_run (
                        ingestion_id, snapshot_id, idempotency_key,
                        source_id, source_version, source_checksum,
                        schema_version, config_hash, transform_version, status
                    ) VALUES
                        (
                            'acl-ingestion-staging', 'acl-snapshot-staging', %s,
                            'acl-fixture', 'v1', %s,
                            'fixture', %s, 'fixture', 'STAGING'
                        ),
                        (
                            'acl-ingestion-ready', 'acl-snapshot-ready', %s,
                            'acl-fixture', 'v1', %s,
                            'fixture', %s, 'fixture', 'READY'
                        )
                    """,
                    ("b" * 64, "a" * 64, "c" * 64, "d" * 64, "a" * 64, "e" * 64),
                )
                cursor.execute(
                    """
                    INSERT INTO hmda_audit.snapshot (
                        snapshot_id, ingestion_id, source_id, status
                    ) VALUES
                        (
                            'acl-snapshot-staging', 'acl-ingestion-staging',
                            'acl-fixture', 'STAGING'
                        ),
                        (
                            'acl-snapshot-ready', 'acl-ingestion-ready',
                            'acl-fixture', 'READY'
                        )
                    """
                )
                cursor.execute(
                    "SELECT snapshot_id FROM hmda_audit.ready_snapshot ORDER BY snapshot_id"
                )
                assert cursor.fetchall() == [("acl-snapshot-ready",)]
                cursor.execute(
                    """
                    SELECT
                        has_table_privilege(
                            'hmda_reader',
                            'hmda_raw.ready_hmda_record',
                            'SELECT'
                        ),
                        has_table_privilege(
                            'hmda_reader',
                            'hmda_raw.hmda_record',
                            'SELECT'
                        )
                    """
                )
                can_read_view, can_read_table = cursor.fetchone()
                assert can_read_view
                assert not can_read_table

                for path in down_paths:
                    cursor.execute(path.read_text(encoding="utf-8"))
                cursor.execute("SELECT to_regnamespace('hmda_raw')")
                assert cursor.fetchone()[0] is None
        finally:
            connection.rollback()
