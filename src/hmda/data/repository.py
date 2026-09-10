"""Hợp đồng repository; PostgreSQL adapter thuộc TASK-022."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch, SnapshotDescriptor


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class DataRepository(Protocol[PayloadT]):
    def stage(self, batch: DataBatch[PayloadT]) -> str:
        """Lưu staging cô lập và trả ingestion identity."""
        ...

    def publish(self, snapshot: SnapshotDescriptor) -> None:
        """Công bố snapshot bằng transaction implementation cụ thể."""
        ...

    def get_ready(self, snapshot_id: str) -> SnapshotDescriptor:
        """Chỉ trả snapshot READY theo ID cụ thể."""
        ...
