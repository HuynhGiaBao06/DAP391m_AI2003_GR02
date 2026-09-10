"""Hợp đồng prediction service; API chỉ gọi package/service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PredictionResult:
    model_version: str
    prediction_code: str
    probabilities: Mapping[str, float]
    warnings: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class PredictionService(Protocol):
    def predict(
        self,
        features: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> PredictionResult:
        """Dự đoán bằng model bundle đã nạp; không train hoặc fit theo request."""
        ...
