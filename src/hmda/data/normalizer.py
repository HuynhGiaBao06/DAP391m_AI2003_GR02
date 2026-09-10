"""Hợp đồng normalizer cho biến đổi cố định, không học từ dữ liệu."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class DataNormalizer(Protocol[PayloadT]):
    def normalize(
        self, batch: DataBatch[PayloadT], *, config: Mapping[str, Any]
    ) -> DataBatch[PayloadT]:
        """Áp dụng chuẩn hóa cố định được cấu hình và giữ lineage."""
        ...
