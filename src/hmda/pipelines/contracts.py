"""Dependency bundle và kết quả chung cho các data pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, Protocol, TypeVar, runtime_checkable

from hmda.data.contracts import DataBatch, SnapshotDescriptor
from hmda.data.loader import DataLoader
from hmda.data.normalizer import DataNormalizer
from hmda.data.repository import DataRepository
from hmda.data.snapshot import SnapshotManager
from hmda.data.validator import DataValidator


PayloadT = TypeVar("PayloadT")


@runtime_checkable
class TrainOnlyTransformer(Protocol[PayloadT]):
    """Ranh giới cho biến đổi học trạng thái: fit chỉ nhận tập train."""

    def fit(self, train: DataBatch[PayloadT], *, config: Mapping[str, Any]) -> None:
        ...

    def transform(self, batch: DataBatch[PayloadT]) -> DataBatch[PayloadT]:
        ...


@dataclass(frozen=True, slots=True)
class PipelineDependencies(Generic[PayloadT]):
    loader: DataLoader[PayloadT]
    normalizer: DataNormalizer[PayloadT]
    validator: DataValidator[PayloadT]
    snapshots: SnapshotManager[PayloadT]
    repository: DataRepository[PayloadT] | None = None


@dataclass(frozen=True, slots=True)
class PipelineResult(Generic[PayloadT]):
    data: DataBatch[PayloadT]
    snapshot: SnapshotDescriptor | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
