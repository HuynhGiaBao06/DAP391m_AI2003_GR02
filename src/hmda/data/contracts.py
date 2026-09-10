"""Kiểu dữ liệu tối thiểu dùng để nối các component mà không khóa schema HMDA."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Generic, Mapping, TypeVar

from hmda.core.exceptions import DataContractError


PayloadT = TypeVar("PayloadT")


class SnapshotStatus(StrEnum):
    STAGING = "STAGING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class FieldRoles:
    """Tên trường theo vai trò; không chứa schema/cohort cụ thể."""

    features: tuple[str, ...]
    target: str
    audit_fields: tuple[str, ...] = ()
    technical_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        groups = {
            "features": self.features,
            "target": (self.target,),
            "audit_fields": self.audit_fields,
            "technical_ids": self.technical_ids,
        }
        if not self.target or any(not field for fields in groups.values() for field in fields):
            raise DataContractError("Tên field theo vai trò không được rỗng")
        seen: dict[str, str] = {}
        for role, fields in groups.items():
            for field in fields:
                if field in seen:
                    raise DataContractError(
                        f"Field '{field}' đồng thời thuộc {seen[field]} và {role}"
                    )
                seen[field] = role


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    source_id: str
    version: str
    location: str
    checksum: str | None = None


@dataclass(frozen=True, slots=True)
class DataBatch(Generic[PayloadT]):
    payload: PayloadT
    source: SourceDescriptor
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ValidationSummary:
    is_valid: bool
    issues: tuple[object, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SnapshotDescriptor:
    snapshot_id: str
    status: SnapshotStatus
    source_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
