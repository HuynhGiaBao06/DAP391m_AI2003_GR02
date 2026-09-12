CREATE SCHEMA IF NOT EXISTS hmda_audit;
CREATE SCHEMA IF NOT EXISTS hmda_staging;
CREATE SCHEMA IF NOT EXISTS hmda_raw;

CREATE TABLE IF NOT EXISTS hmda_audit.schema_migration (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hmda_audit.source_file (
    source_id TEXT PRIMARY KEY,
    source_version TEXT NOT NULL,
    checksum CHAR(64) NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    identity_algorithm TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_source_file_identity
        UNIQUE (source_id, source_version, checksum),
    CONSTRAINT ck_source_file_checksum
        CHECK (checksum ~ '^[0-9a-f]{64}$')
);

CREATE TABLE IF NOT EXISTS hmda_audit.ingestion_run (
    ingestion_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL UNIQUE,
    idempotency_key CHAR(64) NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_version TEXT NOT NULL,
    source_checksum CHAR(64) NOT NULL,
    schema_version TEXT NOT NULL,
    config_hash CHAR(64) NOT NULL,
    transform_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'STAGING',
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ingestion_source
        FOREIGN KEY (source_id, source_version, source_checksum)
        REFERENCES hmda_audit.source_file (source_id, source_version, checksum),
    CONSTRAINT ck_ingestion_idempotency_key
        CHECK (idempotency_key ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ingestion_config_hash
        CHECK (config_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_ingestion_status
        CHECK (status IN ('STAGING', 'READY', 'FAILED')),
    CONSTRAINT ck_ingestion_failure_reason
        CHECK (
            (status = 'FAILED' AND NULLIF(BTRIM(failure_reason), '') IS NOT NULL)
            OR (status <> 'FAILED' AND failure_reason IS NULL)
        )
);

CREATE TABLE IF NOT EXISTS hmda_audit.quality_result (
    ingestion_id TEXT PRIMARY KEY
        REFERENCES hmda_audit.ingestion_run (ingestion_id),
    is_valid BOOLEAN NOT NULL,
    error_count INTEGER NOT NULL CHECK (error_count >= 0),
    warning_count INTEGER NOT NULL CHECK (warning_count >= 0),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    issues JSONB NOT NULL DEFAULT '[]'::JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_quality_validity
        CHECK (is_valid = (error_count = 0))
);

CREATE TABLE IF NOT EXISTS hmda_audit.snapshot (
    snapshot_id TEXT PRIMARY KEY,
    ingestion_id TEXT NOT NULL UNIQUE
        REFERENCES hmda_audit.ingestion_run (ingestion_id),
    source_id TEXT NOT NULL REFERENCES hmda_audit.source_file (source_id),
    status TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_snapshot_status
        CHECK (status IN ('STAGING', 'READY', 'FAILED'))
);

CREATE TABLE IF NOT EXISTS hmda_staging.hmda_record (
    ingestion_id TEXT NOT NULL
        REFERENCES hmda_audit.ingestion_run (ingestion_id),
    record_id CHAR(64) NOT NULL,
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 0),
    source_line_number INTEGER NOT NULL CHECK (source_line_number > 1),
    income TEXT NOT NULL,
    loan_amount TEXT NOT NULL,
    combined_loan_to_value_ratio TEXT NOT NULL,
    property_value TEXT NOT NULL,
    loan_term TEXT NOT NULL,
    debt_to_income_ratio TEXT NOT NULL,
    loan_type TEXT NOT NULL,
    loan_purpose TEXT NOT NULL,
    lien_status TEXT NOT NULL,
    occupancy_type TEXT NOT NULL,
    construction_method TEXT NOT NULL,
    total_units TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    applicant_sex TEXT NOT NULL,
    state_code TEXT NOT NULL,
    county_code TEXT NOT NULL,
    lei TEXT NOT NULL,
    activity_year TEXT NOT NULL,
    PRIMARY KEY (ingestion_id, record_id),
    CONSTRAINT uq_staging_source_row
        UNIQUE (ingestion_id, source_row_number),
    CONSTRAINT ck_staging_record_id
        CHECK (record_id ~ '^[0-9a-f]{64}$')
);

CREATE TABLE IF NOT EXISTS hmda_raw.hmda_record (
    snapshot_id TEXT NOT NULL
        REFERENCES hmda_audit.snapshot (snapshot_id),
    record_id CHAR(64) NOT NULL,
    source_row_number INTEGER NOT NULL CHECK (source_row_number > 0),
    source_line_number INTEGER NOT NULL CHECK (source_line_number > 1),
    income TEXT NOT NULL,
    loan_amount TEXT NOT NULL,
    combined_loan_to_value_ratio TEXT NOT NULL,
    property_value TEXT NOT NULL,
    loan_term TEXT NOT NULL,
    debt_to_income_ratio TEXT NOT NULL,
    loan_type TEXT NOT NULL,
    loan_purpose TEXT NOT NULL,
    lien_status TEXT NOT NULL,
    occupancy_type TEXT NOT NULL,
    construction_method TEXT NOT NULL,
    total_units TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    applicant_sex TEXT NOT NULL,
    state_code TEXT NOT NULL,
    county_code TEXT NOT NULL,
    lei TEXT NOT NULL,
    activity_year TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, record_id),
    CONSTRAINT uq_raw_source_row
        UNIQUE (snapshot_id, source_row_number),
    CONSTRAINT ck_raw_record_id
        CHECK (record_id ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_raw_action_taken
        CHECK (action_taken IN ('0', '1', '2')),
    CONSTRAINT ck_raw_applicant_sex
        CHECK (applicant_sex IN ('1', '2', '3', '4', '6')),
    CONSTRAINT ck_raw_state
        CHECK (state_code = 'NY'),
    CONSTRAINT ck_raw_activity_year
        CHECK (activity_year = '2024')
);

CREATE INDEX IF NOT EXISTS ix_ingestion_run_status
    ON hmda_audit.ingestion_run (status);
CREATE INDEX IF NOT EXISTS ix_snapshot_status
    ON hmda_audit.snapshot (status);
CREATE INDEX IF NOT EXISTS ix_staging_ingestion_row
    ON hmda_staging.hmda_record (ingestion_id, source_row_number);
CREATE INDEX IF NOT EXISTS ix_raw_snapshot_row
    ON hmda_raw.hmda_record (snapshot_id, source_row_number);

CREATE OR REPLACE VIEW hmda_audit.ready_snapshot AS
SELECT snapshot_id, ingestion_id, source_id, status, metadata, created_at, updated_at
FROM hmda_audit.snapshot
WHERE status = 'READY';

CREATE OR REPLACE VIEW hmda_raw.ready_hmda_record AS
SELECT records.*
FROM hmda_raw.hmda_record AS records
JOIN hmda_audit.ready_snapshot AS snapshots
    ON snapshots.snapshot_id = records.snapshot_id;

INSERT INTO hmda_audit.schema_migration (version)
VALUES ('001_hmda_phase2_schema')
ON CONFLICT (version) DO NOTHING;
