"""Hợp đồng validator không mutate dữ liệu đầu vào."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch, ValidationSummary


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class DataValidator(Protocol[PayloadT]):
    def validate(
        self, batch: DataBatch[PayloadT], *, config: Mapping[str, Any]
    ) -> ValidationSummary:
        """Trả report; không tự sửa dữ liệu để vượt quality gate."""
        ...
