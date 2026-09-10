"""Hợp đồng TrainingDataPipeline; chưa triển khai train/preprocessing."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import SourceDescriptor
from hmda.pipelines.contracts import PipelineDependencies, PipelineResult


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class TrainingDataPipeline(Protocol[PayloadT]):
    dependencies: PipelineDependencies[PayloadT]

    def run(
        self,
        source: SourceDescriptor,
        *,
        config: Mapping[str, Any],
        split_manifest: object | None = None,
    ) -> PipelineResult[PayloadT]:
        """Chuẩn bị dữ liệu train; transformer học dữ liệu phải fit trên train."""
        ...
