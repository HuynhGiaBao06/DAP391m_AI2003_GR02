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
    RepositoryUnitOfWork,
    make_idempotency_key,
)
from hmda.data.snapshot import (
    AtomicSnapshotExporter,
    AtomicSnapshotManager,
    SnapshotManager,
    SnapshotManifest,
    SnapshotSerialization,
    create_staging_manifest,
)
from hmda.data.source_identity import SourceIdentity, identify_source, make_record_id
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
    "RepositoryUnitOfWork",
    "AtomicSnapshotExporter",
    "AtomicSnapshotManager",
    "SnapshotManager",
    "SnapshotManifest",
    "SnapshotSerialization",
    "SourceIdentity",
    "identify_source",
    "make_record_id",
    "make_idempotency_key",
    "make_connection_factory",
    "create_staging_manifest",
    "require_publishable",
]
