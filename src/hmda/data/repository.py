"""Repository/UoW contract và idempotency độc lập SQL vendor."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
import re
from types import TracebackType
from typing import Protocol, TypeVar, runtime_checkable

from hmda.core.exceptions import RepositoryError
from hmda.data.contracts import SnapshotDescriptor, ValidationSummary
from hmda.data.source_identity import SourceIdentity


PayloadT = TypeVar("PayloadT")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class IngestionStatus(StrEnum):
    STAGING = "STAGING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class IdempotencyIdentity:
    """Logical input identity; đổi bất kỳ version nào sẽ tạo key mới."""

    source_id: str
    source_version: str
    source_checksum: str
    schema_version: str
    config_hash: str
    transform_version: str

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "source_version",
            "schema_version",
            "transform_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise RepositoryError(f"{field_name} không được rỗng")
        for field_name in ("source_checksum", "config_hash"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value.lower()):
                raise RepositoryError(f"{field_name} phải là SHA-256 hexadecimal")


def make_idempotency_key(identity: IdempotencyIdentity) -> str:
    """Hash canonical từ source/schema/config/transform identity."""

    payload = json.dumps(
        [
            "hmda-ingestion-idempotency-v1",
            identity.source_id,
            identity.source_version,
            identity.source_checksum.lower(),
            identity.schema_version,
            identity.config_hash.lower(),
            identity.transform_version,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class IngestionRequest:
    """Yêu cầu ingestion có ID do caller cấp và logical key kiểm được."""

    ingestion_id: str
    snapshot_id: str
    identity: IdempotencyIdentity
    idempotency_key: str

    def __post_init__(self) -> None:
        for field_name in ("ingestion_id", "snapshot_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise RepositoryError(f"{field_name} không được rỗng")
        expected = make_idempotency_key(self.identity)
        if self.idempotency_key != expected:
            raise RepositoryError("idempotency_key không khớp logical identity")

    @classmethod
    def create(
        cls,
        *,
        ingestion_id: str,
        snapshot_id: str,
        identity: IdempotencyIdentity,
    ) -> "IngestionRequest":
        return cls(
            ingestion_id=ingestion_id,
            snapshot_id=snapshot_id,
            identity=identity,
            idempotency_key=make_idempotency_key(identity),
        )


@dataclass(frozen=True, slots=True)
class IngestionDescriptor:
    ingestion_id: str
    snapshot_id: str
    idempotency_key: str
    source_id: str
    status: IngestionStatus


@runtime_checkable
class RepositoryUnitOfWork(Protocol):
    """Transaction boundary mà PostgreSQL adapter TASK-022 phải hiện thực."""

    def __enter__(self) -> "RepositoryUnitOfWork": ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def register_source(self, source: SourceIdentity) -> None: ...

    def begin_ingestion(self, request: IngestionRequest) -> IngestionDescriptor:
        """Retry cùng key phải trả cùng logical ingestion, không tạo bản sao."""
        ...

    def save_quality_result(
        self, ingestion_id: str, validation: ValidationSummary
    ) -> None: ...

    def stage_snapshot(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None: ...

    def mark_failed(self, ingestion_id: str, *, reason: str) -> None: ...

    def publish_ready(
        self, ingestion_id: str, snapshot: SnapshotDescriptor
    ) -> None:
        """Chỉ publish descriptor READY sau khi filesystem export thành công."""
        ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


@runtime_checkable
class DataRepository(Protocol[PayloadT]):
    """Reader + transaction factory; không chứa SQL/PostgreSQL chi tiết."""

    def transaction(self) -> RepositoryUnitOfWork:
        """Mở unit of work; caller commit rõ ràng, exception phải rollback."""
        ...

    def get_ready(self, snapshot_id: str) -> SnapshotDescriptor:
        """Chỉ trả snapshot READY theo ID cụ thể."""
        ...
