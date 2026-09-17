DO $roles$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hmda_migrator') THEN
        CREATE ROLE hmda_migrator NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hmda_ingest') THEN
        CREATE ROLE hmda_ingest NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hmda_reader') THEN
        CREATE ROLE hmda_reader NOLOGIN;
    END IF;
END
$roles$;

REVOKE ALL ON SCHEMA hmda_audit, hmda_staging, hmda_raw FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA hmda_audit, hmda_staging, hmda_raw FROM PUBLIC;

GRANT USAGE, CREATE ON SCHEMA hmda_audit, hmda_staging, hmda_raw TO hmda_migrator;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hmda_audit, hmda_staging, hmda_raw
    TO hmda_migrator;

GRANT USAGE ON SCHEMA hmda_audit, hmda_staging, hmda_raw TO hmda_ingest;
GRANT SELECT, INSERT, UPDATE
    ON hmda_audit.source_file,
       hmda_audit.ingestion_run,
       hmda_audit.quality_result,
       hmda_audit.snapshot
    TO hmda_ingest;
GRANT SELECT, INSERT, UPDATE, DELETE ON hmda_staging.hmda_record TO hmda_ingest;
GRANT SELECT, INSERT ON hmda_raw.hmda_record TO hmda_ingest;

GRANT USAGE ON SCHEMA hmda_audit, hmda_raw TO hmda_reader;
GRANT SELECT ON hmda_audit.ready_snapshot, hmda_raw.ready_hmda_record TO hmda_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA hmda_audit, hmda_staging, hmda_raw
    GRANT ALL PRIVILEGES ON TABLES TO hmda_migrator;

INSERT INTO hmda_audit.schema_migration (version)
VALUES ('002_hmda_phase2_permissions')
ON CONFLICT (version) DO NOTHING;
