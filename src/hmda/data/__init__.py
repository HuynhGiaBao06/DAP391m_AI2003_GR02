"""Data contracts độc lập schema; implementation vận hành thuộc Phase 2."""

from hmda.data.contracts import (
    DataBatch,
    FieldRoles,
    SnapshotDescriptor,
    SnapshotStatus,
    SourceDescriptor,
    ValidationSummary,
)
from hmda.data.loader import CSVBytesLoader
from hmda.data.postgres import (
    HMDA_BUSINESS_COLUMNS,
    PostgresMigrationRunner,
    PostgresRepository,
    PostgresSettings,
    PostgresUnitOfWork,
    make_connection_factory,
)
from hmda.data.repository import (
    DataRepository,
    IdempotencyIdentity,
    IngestionDescriptor,
    IngestionRequest,
    IngestionStatus,
    RecordSetSummary,
    RepositoryUnitOfWork,
    make_idempotency_key,
    require_reconciled_record_sets,
    summarize_record_set,
)
from hmda.data.snapshot import (
    AtomicSnapshotExporter,
    AtomicSnapshotManager,
    SnapshotManager,
    SnapshotManifest,
    SnapshotSerialization,
    create_staging_manifest,
)
from hmda.data.source_identity import (
    SourceIdentity,
    identify_source,
    make_record_id,
    require_registered_source,
)
from hmda.data.validator import (
    ConfigurableDataValidator,
    QualityIssue,
    QualitySeverity,
    require_publishable,
)

__all__ = [
    "DataBatch",
    "FieldRoles",
    "SnapshotDescriptor",
    "SnapshotStatus",
    "SourceDescriptor",
    "ValidationSummary",
    "CSVBytesLoader",
    "DataRepository",
    "HMDA_BUSINESS_COLUMNS",
    "PostgresMigrationRunner",
    "PostgresRepository",
    "PostgresSettings",
    "PostgresUnitOfWork",
    "ConfigurableDataValidator",
    "IdempotencyIdentity",
    "IngestionDescriptor",
    "IngestionRequest",
    "IngestionStatus",
    "QualityIssue",
    "QualitySeverity",
    "RecordSetSummary",
    "RepositoryUnitOfWork",
    "AtomicSnapshotExporter",
    "AtomicSnapshotManager",
    "SnapshotManager",
    "SnapshotManifest",
    "SnapshotSerialization",
    "SourceIdentity",
    "identify_source",
    "make_record_id",
    "require_registered_source",
    "require_reconciled_record_sets",
    "make_idempotency_key",
    "make_connection_factory",
    "create_staging_manifest",
    "require_publishable",
    "summarize_record_set",
]
