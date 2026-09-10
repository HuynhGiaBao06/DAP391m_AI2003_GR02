"""Hợp đồng EDADataPipeline gần raw; implementation thuộc Phase 2–3."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import SourceDescriptor
from hmda.pipelines.contracts import PipelineDependencies, PipelineResult


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class EDADataPipeline(Protocol[PayloadT]):
    dependencies: PipelineDependencies[PayloadT]

    def run(
        self, source: SourceDescriptor, *, config: Mapping[str, Any]
    ) -> PipelineResult[PayloadT]:
        """Tạo dữ liệu gần raw; không fit preprocessing cho model."""
        ...
