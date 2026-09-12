REVOKE SELECT ON hmda_audit.ready_snapshot, hmda_raw.ready_hmda_record
    FROM hmda_reader;
REVOKE USAGE ON SCHEMA hmda_audit, hmda_raw FROM hmda_reader;

REVOKE SELECT, INSERT ON hmda_raw.hmda_record FROM hmda_ingest;
REVOKE SELECT, INSERT, UPDATE, DELETE ON hmda_staging.hmda_record FROM hmda_ingest;
REVOKE SELECT, INSERT, UPDATE
    ON hmda_audit.source_file,
       hmda_audit.ingestion_run,
       hmda_audit.quality_result,
       hmda_audit.snapshot
    FROM hmda_ingest;
REVOKE USAGE ON SCHEMA hmda_audit, hmda_staging, hmda_raw FROM hmda_ingest;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA hmda_audit, hmda_staging, hmda_raw
    FROM hmda_migrator;
REVOKE USAGE, CREATE ON SCHEMA hmda_audit, hmda_staging, hmda_raw
    FROM hmda_migrator;

DELETE FROM hmda_audit.schema_migration
WHERE version = '002_hmda_phase2_permissions';

-- Các group role NOLOGIN được giữ lại để tránh phá membership ngoài migration.
