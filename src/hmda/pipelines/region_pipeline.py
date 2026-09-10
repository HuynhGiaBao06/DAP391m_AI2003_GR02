"""Hợp đồng RegionDataPipeline; model nguồn được truyền vào và không refit."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import SourceDescriptor
from hmda.pipelines.contracts import PipelineDependencies, PipelineResult


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class RegionDataPipeline(Protocol[PayloadT]):
    dependencies: PipelineDependencies[PayloadT]

    def run(
        self,
        source: SourceDescriptor,
        *,
        config: Mapping[str, Any],
        model_bundle: object,
    ) -> PipelineResult[PayloadT]:
        """Transform/predict với model đã khóa; không fit lại trên vùng mới."""
        ...
