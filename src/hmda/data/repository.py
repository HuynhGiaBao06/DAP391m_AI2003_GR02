"""Repository/UoW contract và idempotency độc lập SQL vendor."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
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
_RECORD_ID_PATTERN = re.compile(r"[0-9a-f]{64}")
_TECHNICAL_RECORD_COLUMNS = (
    "record_id",
    "source_row_number",
    "source_line_number",
)


class IngestionStatus(StrEnum):
    STAGING = "STAGING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class RecordSetSummary:
    """Dấu vân tay nội dung record-level độc lập serialization CSV."""

    row_count: int
    columns: tuple[str, ...]
    distinct_record_id_count: int
    content_checksum: str


def summarize_record_set(
    records: Iterable[Mapping[str, object]],
    *,
    business_columns: Sequence[str],
) -> RecordSetSummary:
    """Kiểm contract và hash record theo đúng thứ tự dòng/column đã khóa."""

    resolved_business_columns = tuple(business_columns)
    if not resolved_business_columns or any(
        not isinstance(column, str) or not column.strip()
        for column in resolved_business_columns
    ):
        raise RepositoryError("business_columns phải là danh sách tên cột không rỗng")
    if len(set(resolved_business_columns)) != len(resolved_business_columns):
        raise RepositoryError("business_columns không được trùng")
    if set(_TECHNICAL_RECORD_COLUMNS).intersection(resolved_business_columns):
        raise RepositoryError("business_columns trùng technical column")
    columns = (*_TECHNICAL_RECORD_COLUMNS, *resolved_business_columns)
    expected_keys = set(columns)
    digest = sha256()
    record_ids: set[str] = set()
    previous_line_number = 1

    row_count = 0
    for expected_row_number, record in enumerate(records, start=1):
        row_count = expected_row_number
        if not isinstance(record, Mapping) or set(record) != expected_keys:
            raise RepositoryError("Record không khớp column contract")

        record_id = record["record_id"]
        if not isinstance(record_id, str) or not _RECORD_ID_PATTERN.fullmatch(
            record_id
        ):
            raise RepositoryError("record_id phải là SHA-256 lowercase")
        if record_id in record_ids:
            raise RepositoryError("Record set trùng record_id")
        record_ids.add(record_id)

        source_row_number = record["source_row_number"]
        if (
            isinstance(source_row_number, bool)
            or not isinstance(source_row_number, int)
            or source_row_number != expected_row_number
        ):
            raise RepositoryError("source_row_number phải liên tục từ 1")

        source_line_number = record["source_line_number"]
        if (
            isinstance(source_line_number, bool)
            or not isinstance(source_line_number, int)
            or source_line_number <= previous_line_number
        ):
            raise RepositoryError("source_line_number phải tăng và bắt đầu sau header")
        previous_line_number = source_line_number

        business_values = tuple(record[column] for column in resolved_business_columns)
        if any(not isinstance(value, str) for value in business_values):
            raise RepositoryError("Business token raw phải được giữ dưới dạng string")

        encoded = json.dumps(
            (record_id, source_row_number, source_line_number, *business_values),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)

    if row_count == 0:
        raise RepositoryError("Record set không được rỗng")

    return RecordSetSummary(
        row_count=row_count,
        columns=columns,
        distinct_record_id_count=len(record_ids),
        content_checksum=digest.hexdigest(),
    )


def require_reconciled_record_sets(
    expected: RecordSetSummary,
    actual: RecordSetSummary,
) -> None:
    """Từ chối mọi khác biệt về shape, key hoặc nội dung record-level."""

    if expected.columns != actual.columns:
        raise RepositoryError("Reconciliation không khớp thứ tự cột")
    if expected.row_count != actual.row_count:
        raise RepositoryError("Reconciliation không khớp số dòng")
    if expected.distinct_record_id_count != actual.distinct_record_id_count:
        raise RepositoryError("Reconciliation không khớp record_id")
    if expected.content_checksum != actual.content_checksum:
        raise RepositoryError("Reconciliation không khớp nội dung record")


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

    def stage_records(
        self,
        ingestion_id: str,
        records: Sequence[Mapping[str, object]],
    ) -> RecordSetSummary: ...

    def promote_records(
        self,
        ingestion_id: str,
        expected: RecordSetSummary,
    ) -> RecordSetSummary: ...

    def read_promoted_records(
        self,
        ingestion_id: str,
    ) -> Sequence[Mapping[str, object]]: ...

    def clear_staged_records(
        self,
        ingestion_id: str,
        expected_row_count: int,
    ) -> int:
        """Xóa đúng staging rows sau khi raw và snapshot đã được đối soát."""
        ...

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

    def get_ready_records(self, snapshot_id: str) -> PayloadT:
        """Chỉ trả record thuộc snapshot READY theo ID cụ thể."""
        ...
