from collections import Counter
from pathlib import Path

import pytest

from hmda.core.config import ConfigLoader
from hmda.data.contracts import SourceDescriptor
from hmda.data.loader import CSVBytesLoader
from hmda.data.postgres import HMDA_BUSINESS_COLUMNS
from hmda.data.repository import summarize_record_set
from hmda.data.source_identity import require_registered_source
from hmda.data.validator import ConfigurableDataValidator, require_publishable


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_owner_attested_hmda_source_runs_transport_quality_contract() -> None:
    bundle = ConfigLoader().load(environment={})
    data_config = bundle.get("data")
    schema_config = bundle.get("schema")
    quality_config = bundle.get("quality")
    source = data_config["source"]
    source_path = PROJECT_ROOT / source["local_path"]
    if not source_path.is_file():
        pytest.skip("HMDA source is intentionally not stored in Git")

    assert set(quality_config["framework"]["supported_rule_types"]) == (
        ConfigurableDataValidator.SUPPORTED_RULE_TYPES
    )

    registered_descriptor = require_registered_source(data_config)
    assert registered_descriptor.source_id == source["source_id"]
    assert registered_descriptor.version == source["version"]
    assert registered_descriptor.checksum == source["sha256"]
    assert source["identity_mode"] == "OWNER_ATTESTED_LOCAL_DERIVED"
    assert source["attestation"]["owner"] == "BaoHG"
    assert source["attestation"]["data_admin"] == "BaoHG"
    assert source["attestation"]["downloaded_on"] == "2026-09-13"
    assert data_config["cohort"]["publish_scope"] == "TRANSPORT_SNAPSHOT_ONLY"
    assert data_config["cohort"]["analysis_ready"] is False

    # Resolve đường dẫn tương đối từ config tại biên I/O; identity và checksum giữ nguyên.
    resolved_descriptor = SourceDescriptor(
        source_id=registered_descriptor.source_id,
        version=registered_descriptor.version,
        location=str(source_path),
        checksum=registered_descriptor.checksum,
    )
    batch = CSVBytesLoader(
        encoding=source["encoding"], delimiter=source["delimiter"]
    ).load(resolved_descriptor)
    validation = ConfigurableDataValidator().validate(batch, config=quality_config)
    transport_summary = summarize_record_set(
        batch.payload,
        business_columns=HMDA_BUSINESS_COLUMNS,
    )

    assert batch.metadata["byte_size"] == source["byte_size"]
    assert batch.metadata["content_checksum"] == source["sha256"]
    assert batch.metadata["row_count"] == source["row_count"]
    assert list(batch.metadata["columns"]) == schema_config["column_order"]
    assert all(
        row["source_row_number"] >= 1 and row["source_line_number"] >= 2
        for row in batch.payload
    )
    assert len({row["record_id"] for row in batch.payload}) == source["row_count"]
    assert transport_summary.row_count == source["row_count"]
    assert transport_summary.distinct_record_id_count == source["row_count"]
    assert transport_summary.columns == (
        "record_id",
        "source_row_number",
        "source_line_number",
        *tuple(schema_config["column_order"]),
    )

    action_counts = Counter(str(row["action_taken"]) for row in batch.payload)
    sex_counts = Counter(str(row["applicant_sex"]) for row in batch.payload)
    assert dict(action_counts) == data_config["cohort"]["observed_source"][
        "action_taken"
    ]
    assert dict(sex_counts) == data_config["cohort"]["observed_source"][
        "applicant_sex"
    ]

    evidence = quality_config["observed_evidence"]
    assert evidence["evidence_kind"] == "profiled_observation_not_validation_summary"
    assert evidence["generated_by_validator"] is False
    assert quality_config["framework"]["gate_policy"] == {
        "ready_scope": "TRANSPORT_SNAPSHOT_ONLY",
        "blocking_severity": "ERROR",
        "analytical_findings_are_reported": True,
    }
    assert source["row_count"] == evidence["source_rows"]
    issues = {issue.rule_id: issue for issue in validation.issues}
    assert set(issues) == {
        "HMDA_RAW_008_COUNTY_FORMAT",
        "HMDA_RAW_009_COUNTY_MISSING",
        "HMDA_RAW_024_EXACT_ROW_EXCESS",
    }
    assert issues["HMDA_RAW_008_COUNTY_FORMAT"].affected_count == evidence[
        "county_float_style_nonblank"
    ]["affected_count"]
    assert issues["HMDA_RAW_009_COUNTY_MISSING"].affected_count == evidence[
        "county_missing"
    ]["affected_count"]
    assert issues["HMDA_RAW_024_EXACT_ROW_EXCESS"].affected_count == evidence[
        "exact_row_excess_duplicates"
    ]["affected_count"]
    assert issues["HMDA_RAW_008_COUNTY_FORMAT"].severity == "WARNING"
    assert issues["HMDA_RAW_008_COUNTY_FORMAT"].layer == "analytical_readiness"
    assert issues["HMDA_RAW_009_COUNTY_MISSING"].severity == "WARNING"
    assert issues["HMDA_RAW_009_COUNTY_MISSING"].layer == "analytical_readiness"
    assert validation.metadata == {
        "evaluated_rule_count": 25,
        "failed_rule_count": 3,
        "error_count": 0,
        "warning_count": 3,
    }
    assert validation.is_valid is True
    require_publishable(validation)
