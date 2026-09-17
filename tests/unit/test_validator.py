from copy import deepcopy

import pytest

from hmda.core.exceptions import DataValidationError
from hmda.data.contracts import DataBatch, SourceDescriptor
from hmda.data.validator import (
    ConfigurableDataValidator,
    QualityIssue,
    QualitySeverity,
    require_publishable,
)


def _batch(rows, checksum: str = "a" * 64):
    return DataBatch(
        payload=rows,
        source=SourceDescriptor("fixture-source", "v1", "memory://fixture", checksum),
        metadata={"content_checksum": checksum},
    )


def test_validator_reports_generic_quality_failures_without_mutation() -> None:
    rows = [
        {
            "record_id": "r1",
            "amount": 10,
            "token": "NA",
            "target": "1",
            "business_key": "duplicate",
        },
        {
            "record_id": "r2",
            "amount": "not-number",
            "token": "UNKNOWN",
            "target": "9",
            "business_key": "duplicate",
        },
        {
            "record_id": "r3",
            "amount": 30,
            "token": "Exempt",
            "target": "2",
            "business_key": "",
        },
    ]
    original = deepcopy(rows)
    config = {
        "sample_id_field": "record_id",
        "defaults": {"sample_limit": 1},
        "rules": [
            {
                "rule_id": "Q07_CHECKSUM",
                "type": "checksum_match",
                "layer": "raw",
                "severity": "ERROR",
                "version": "1",
                "params": {"expected": "b" * 64},
            },
            {
                "rule_id": "Q01_HEADER",
                "type": "required_columns",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"columns": ["expected_column"]},
            },
            {
                "rule_id": "Q02_TYPE",
                "type": "field_type",
                "layer": "parsed",
                "severity": "ERROR",
                "params": {"field": "amount", "expected": "integer"},
            },
            {
                "rule_id": "Q03_TOKEN",
                "type": "allowed_values",
                "layer": "raw",
                "severity": "WARNING",
                "params": {"field": "token", "values": ["NA", "Exempt", ""]},
            },
            {
                "rule_id": "Q04_TARGET",
                "type": "allowed_values",
                "layer": "cohort",
                "severity": "ERROR",
                "params": {"field": "target", "values": ["1", "2", "3"]},
            },
            {
                "rule_id": "Q05_DUPLICATE",
                "type": "duplicate_key",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"fields": ["business_key"]},
            },
            {
                "rule_id": "Q06_MISSING",
                "type": "missing_key",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"fields": ["business_key"]},
            },
        ],
    }

    result = ConfigurableDataValidator().validate(_batch(rows), config=config)

    assert rows == original
    assert result.is_valid is False
    assert [issue.rule_id for issue in result.issues] == [
        "Q01_HEADER",
        "Q02_TYPE",
        "Q03_TOKEN",
        "Q04_TARGET",
        "Q05_DUPLICATE",
        "Q06_MISSING",
        "Q07_CHECKSUM",
    ]
    assert all(isinstance(issue, QualityIssue) for issue in result.issues)
    assert all(len(issue.sample_ids) <= 1 for issue in result.issues)
    assert result.metadata == {
        "evaluated_rule_count": 7,
        "failed_rule_count": 7,
        "error_count": 6,
        "warning_count": 1,
    }
    with pytest.raises(DataValidationError, match="Q01_HEADER"):
        require_publishable(result)


def test_warning_is_retained_without_blocking_validity() -> None:
    config = {
        "sample_id_field": "record_id",
        "rules": [
            {
                "rule_id": "WARN_TOKEN",
                "type": "allowed_values",
                "layer": "raw",
                "severity": "WARNING",
                "version": "2",
                "params": {"field": "token", "values": ["known"]},
            }
        ],
    }

    result = ConfigurableDataValidator().validate(
        _batch(({"record_id": "r1", "token": "unknown"},)),
        config=config,
    )

    assert result.is_valid is True
    assert len(result.issues) == 1
    assert result.issues[0].severity is QualitySeverity.WARNING
    assert result.issues[0].rule_version == "2"
    require_publishable(result)


def test_clean_rules_return_valid_summary() -> None:
    config = {
        "rules": [
            {
                "rule_id": "KEY_PRESENT",
                "type": "missing_key",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"fields": ["key"]},
            }
        ]
    }

    result = ConfigurableDataValidator().validate(_batch(({"key": "a"},)), config=config)

    assert result.is_valid is True
    assert result.issues == ()


def test_raw_format_and_numeric_parse_rules_preserve_special_tokens() -> None:
    rows = (
        {"record_id": "r1", "county_code": "36001", "income": "10"},
        {"record_id": "r2", "county_code": "36001.0", "income": "bad"},
        {"record_id": "r3", "county_code": "", "income": "Exempt"},
        {"record_id": "r4", "county_code": "36003", "income": "NaN"},
    )
    config = {
        "sample_id_field": "record_id",
        "rules": [
            {
                "rule_id": "COUNTY_FORMAT",
                "type": "matches_pattern",
                "layer": "raw",
                "severity": "ERROR",
                "params": {
                    "field": "county_code",
                    "pattern": r"[0-9]{5}",
                    "ignore_values": [""],
                },
            },
            {
                "rule_id": "INCOME_PARSE",
                "type": "parseable_number",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"field": "income", "ignore_values": ["", "Exempt"]},
            },
        ],
    }

    result = ConfigurableDataValidator().validate(_batch(rows), config=config)

    assert result.is_valid is False
    assert [(issue.rule_id, issue.affected_count) for issue in result.issues] == [
        ("COUNTY_FORMAT", 1),
        ("INCOME_PARSE", 2),
    ]
    assert result.issues[0].sample_ids == ("r2",)


def test_invalid_pattern_rule_fails_explicitly() -> None:
    config = {
        "rules": [
            {
                "rule_id": "BAD_REGEX",
                "type": "matches_pattern",
                "layer": "raw",
                "params": {"field": "county_code", "pattern": "["},
            }
        ]
    }

    with pytest.raises(DataValidationError, match="Regex"):
        ConfigurableDataValidator().validate(_batch(()), config=config)


def test_shape_and_exact_row_excess_rules_use_batch_contract() -> None:
    rows = (
        {"record_id": "r1", "a": "1", "b": "x"},
        {"record_id": "r2", "a": "1", "b": "x"},
        {"record_id": "r3", "a": "2", "b": "y"},
    )
    batch = DataBatch(
        payload=rows,
        source=SourceDescriptor(
            "fixture-source", "v1", "memory://fixture", "a" * 64
        ),
        metadata={"content_checksum": "a" * 64, "columns": ("a", "b")},
    )
    config = {
        "sample_id_field": "record_id",
        "rules": [
            {
                "rule_id": "COLUMN_ORDER",
                "type": "exact_columns",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"columns": ["b", "a"]},
            },
            {
                "rule_id": "EXACT_ROW_EXCESS",
                "type": "duplicate_row_excess",
                "layer": "raw",
                "severity": "WARNING",
                "params": {"fields": ["a", "b"]},
            },
            {
                "rule_id": "ROW_COUNT",
                "type": "row_count",
                "layer": "raw",
                "severity": "ERROR",
                "params": {"expected": 4},
            },
        ],
    }

    result = ConfigurableDataValidator().validate(batch, config=config)

    assert [(issue.rule_id, issue.affected_count) for issue in result.issues] == [
        ("COLUMN_ORDER", 1),
        ("EXACT_ROW_EXCESS", 1),
        ("ROW_COUNT", 1),
    ]
    assert result.issues[1].sample_ids == ("r2",)
    assert result.metadata == {
        "evaluated_rule_count": 3,
        "failed_rule_count": 3,
        "error_count": 2,
        "warning_count": 1,
    }


@pytest.mark.parametrize(
    "rules, message",
    [
        (
            [
                {"rule_id": "DUP", "type": "missing_key", "layer": "raw", "params": {"fields": ["a"]}},
                {"rule_id": "DUP", "type": "missing_key", "layer": "raw", "params": {"fields": ["b"]}},
            ],
            "Duplicate quality rule_id",
        ),
        (
            [{"rule_id": "UNKNOWN", "type": "unknown", "layer": "raw"}],
            "Rule type không hỗ trợ",
        ),
    ],
)
def test_invalid_quality_config_fails_explicitly(rules, message: str) -> None:
    with pytest.raises(DataValidationError, match=message):
        ConfigurableDataValidator().validate(_batch(()), config={"rules": rules})
