import csv
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.mark.integration
def test_provisional_hmda_source_matches_recorded_contract() -> None:
    data_config = yaml.safe_load(
        (PROJECT_ROOT / "configs" / "data.yaml").read_text(encoding="utf-8")
    )
    schema_config = yaml.safe_load(
        (PROJECT_ROOT / "configs" / "schema.yaml").read_text(encoding="utf-8")
    )
    quality_config = yaml.safe_load(
        (PROJECT_ROOT / "configs" / "quality.yaml").read_text(encoding="utf-8")
    )
    source = data_config["source"]
    source_path = PROJECT_ROOT / source["local_path"]
    if not source_path.is_file():
        pytest.skip("HMDA source is intentionally not stored in Git")

    assert source_path.stat().st_size == source["byte_size"]
    assert _sha256_file(source_path) == source["sha256"]

    action_counts: Counter[str] = Counter()
    sex_counts: Counter[str] = Counter()
    county_missing = 0
    county_bad_format = 0
    row_count = 0
    with source_path.open(encoding=source["encoding"], newline="") as stream:
        reader = csv.DictReader(stream, delimiter=source["delimiter"], strict=True)
        assert reader.fieldnames == schema_config["column_order"]
        for row in reader:
            row_count += 1
            action_counts[row["action_taken"]] += 1
            sex_counts[row["applicant_sex"]] += 1
            county_code = row["county_code"]
            county_missing += county_code == ""
            county_bad_format += bool(county_code) and re.fullmatch(
                r"[0-9]{5}", county_code
            ) is None

    evidence = quality_config["observed_evidence"]
    action_rule = next(
        rule
        for rule in quality_config["rules"]
        if rule["rule_id"] == "HMDA_FILTERED_004_ACTION_DOMAIN"
    )
    allowed_actions = set(action_rule["params"]["values"])
    assert row_count == source["row_count"] == evidence["source_rows"]
    assert dict(action_counts) == data_config["cohort"]["observed_source"]["action_taken"]
    assert dict(sex_counts) == data_config["cohort"]["observed_source"]["applicant_sex"]
    assert county_missing == evidence["county_missing"]["affected_count"]
    assert county_bad_format == evidence["county_float_style_nonblank"]["affected_count"]
    assert set(action_counts) == allowed_actions == set(
        data_config["cohort"]["filters"]["action_taken"]
    )
    assert sum(count for token, count in action_counts.items() if token not in allowed_actions) == (
        evidence["action_outside_internal_domain"]["affected_count"]
    )
