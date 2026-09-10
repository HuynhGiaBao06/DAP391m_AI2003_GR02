"""Hợp đồng loader; implementation nguồn thật thuộc Phase 2."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch, SourceDescriptor


PayloadT = TypeVar("PayloadT", covariant=True)


@runtime_checkable
class DataLoader(Protocol[PayloadT]):
    def load(self, source: SourceDescriptor) -> DataBatch[PayloadT]:
        """Đọc một source đã định danh mà không tự lọc cohort hoặc sửa token."""
        ...
