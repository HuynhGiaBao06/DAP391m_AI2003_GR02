from typing import Any, Mapping, Sequence

import pytest

from hmda.data.contracts import (
    DataBatch,
    FieldRoles,
    SnapshotDescriptor,
    SnapshotStatus,
    SourceDescriptor,
    ValidationSummary,
)
from hmda.data.loader import DataLoader
from hmda.data.normalizer import DataNormalizer
from hmda.data.repository import DataRepository
from hmda.data.snapshot import SnapshotManager
from hmda.data.validator import DataValidator
from hmda.core.exceptions import DataContractError
from hmda.pipelines.contracts import PipelineDependencies, TrainOnlyTransformer
from hmda.pipelines.eda_pipeline import EDADataPipeline
from hmda.services.prediction_service import PredictionResult, PredictionService
from hmda.services.result_service import ResultService


class FakeLoader:
    def load(self, source: SourceDescriptor) -> DataBatch[list[dict[str, object]]]:
        return DataBatch([{"source_line": 1}], source)


class FakeNormalizer:
    def normalize(
        self,
        batch: DataBatch[list[dict[str, object]]],
        *,
        config: Mapping[str, Any],
    ) -> DataBatch[list[dict[str, object]]]:
        return batch


class FakeValidator:
    def validate(
        self,
        batch: DataBatch[list[dict[str, object]]],
        *,
        config: Mapping[str, Any],
    ) -> ValidationSummary:
        return ValidationSummary(is_valid=True)


class FakeSnapshots:
    def create(
        self,
        batch: DataBatch[list[dict[str, object]]],
        validation: ValidationSummary,
        *,
        metadata: Mapping[str, Any],
    ) -> SnapshotDescriptor:
        return SnapshotDescriptor(
            snapshot_id="fixture-snapshot",
            status=SnapshotStatus.STAGING,
            source_id=batch.source.source_id,
        )


class FakeRepository:
    def __init__(self) -> None:
        self.snapshot: SnapshotDescriptor | None = None

    def transaction(self):
        return object()

    def get_ready(self, snapshot_id: str) -> SnapshotDescriptor:
        assert self.snapshot is not None
        return self.snapshot

    def get_ready_records(self, snapshot_id: str):
        self.get_ready(snapshot_id)
        return []


class FakeEDAPipeline:
    def __init__(self, dependencies: PipelineDependencies[list[dict[str, object]]]) -> None:
        self.dependencies = dependencies

    def run(self, source: SourceDescriptor, *, config: Mapping[str, Any]):
        batch = self.dependencies.loader.load(source)
        normalized = self.dependencies.normalizer.normalize(batch, config=config)
        validation = self.dependencies.validator.validate(normalized, config=config)
        snapshot = self.dependencies.snapshots.create(normalized, validation, metadata={})
        from hmda.pipelines.contracts import PipelineResult

        return PipelineResult(normalized, snapshot)


class FakePredictionService:
    def predict(
        self,
        features: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> PredictionResult:
        return PredictionResult("fixture-model", "1", {"p1": 1.0, "p2": 0.0, "p3": 0.0})


class FakeResultService:
    def get_metrics(self, *, run_id: str, split: str) -> Sequence[Mapping[str, Any]]:
        return []

    def get_global_explanations(
        self, *, run_id: str, model_version: str, class_code: str
    ) -> Sequence[Mapping[str, Any]]:
        return []

    def get_fairness(
        self, *, run_id: str, model_version: str, class_code: str, county: str | None = None
    ) -> Sequence[Mapping[str, Any]]:
        return []


class FakeTrainOnlyTransformer:
    def fit(self, train: DataBatch[list[dict[str, object]]], *, config: Mapping[str, Any]) -> None:
        self.was_fitted = True

    def transform(
        self, batch: DataBatch[list[dict[str, object]]]
    ) -> DataBatch[list[dict[str, object]]]:
        return batch


def test_component_protocols_compose_without_real_data_or_database() -> None:
    dependencies = PipelineDependencies(
        loader=FakeLoader(),
        normalizer=FakeNormalizer(),
        validator=FakeValidator(),
        snapshots=FakeSnapshots(),
        repository=FakeRepository(),
    )
    pipeline = FakeEDAPipeline(dependencies)
    source = SourceDescriptor("fixture-source", "v1", "memory://fixture")

    result = pipeline.run(source, config={})

    assert isinstance(dependencies.loader, DataLoader)
    assert isinstance(dependencies.normalizer, DataNormalizer)
    assert isinstance(dependencies.validator, DataValidator)
    assert isinstance(dependencies.snapshots, SnapshotManager)
    assert isinstance(dependencies.repository, DataRepository)
    assert isinstance(pipeline, EDADataPipeline)
    assert result.snapshot is not None
    assert result.snapshot.status is SnapshotStatus.STAGING


def test_service_protocols_do_not_require_api_or_model_runtime() -> None:
    prediction_service = FakePredictionService()
    result_service = FakeResultService()

    assert isinstance(prediction_service, PredictionService)
    assert isinstance(result_service, ResultService)
    assert prediction_service.predict({}).prediction_code == "1"


def test_train_only_transformer_exposes_fit_and_transform_boundary() -> None:
    transformer = FakeTrainOnlyTransformer()

    assert isinstance(transformer, TrainOnlyTransformer)


def test_field_roles_reject_overlap_between_model_audit_and_ids() -> None:
    roles = FieldRoles(
        features=("feature_a", "feature_b"),
        target="target",
        audit_fields=("audit_group",),
        technical_ids=("record_id",),
    )

    assert roles.target == "target"
    with pytest.raises(DataContractError, match="đồng thời thuộc"):
        FieldRoles(
            features=("feature_a",),
            target="target",
            audit_fields=("feature_a",),
        )
