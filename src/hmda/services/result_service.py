"""Hợp đồng đọc kết quả nghiên cứu đã công bố."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@runtime_checkable
class ResultService(Protocol):
    def get_metrics(self, *, run_id: str, split: str) -> Sequence[Mapping[str, Any]]:
        ...

    def get_global_explanations(
        self, *, run_id: str, model_version: str, class_code: str
    ) -> Sequence[Mapping[str, Any]]:
        ...

    def get_fairness(
        self, *, run_id: str, model_version: str, class_code: str, county: str | None = None
    ) -> Sequence[Mapping[str, Any]]:
        ...
