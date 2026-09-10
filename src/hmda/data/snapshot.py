"""Hợp đồng snapshot manager; vòng đời thật được triển khai ở Phase 2."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch, SnapshotDescriptor, ValidationSummary


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class SnapshotManager(Protocol[PayloadT]):
    def create(
        self,
        batch: DataBatch[PayloadT],
        validation: ValidationSummary,
        *,
        metadata: Mapping[str, Any],
    ) -> SnapshotDescriptor:
        """Tạo descriptor từ input đã định danh; không mặc định công bố READY."""
        ...
