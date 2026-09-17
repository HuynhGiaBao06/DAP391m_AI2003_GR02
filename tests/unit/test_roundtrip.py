from pathlib import Path

import pytest

from hmda.core.exceptions import RepositoryError
from hmda.data.contracts import ValidationSummary
from hmda.data.roundtrip import _recover_pending_snapshot, _require_same_quality
from hmda.data.validator import QualityIssue, QualitySeverity


def _validation(affected_count: int = 1) -> ValidationSummary:
    return ValidationSummary(
        is_valid=True,
        issues=(
            QualityIssue(
                rule_id="FIXTURE_WARNING",
                layer="raw",
                severity=QualitySeverity.WARNING,
                affected_count=affected_count,
                denominator=2,
                sample_ids=("r1",),
            ),
        ),
        metadata={"error_count": 0, "warning_count": 1},
    )


def test_quality_must_remain_identical_through_roundtrip() -> None:
    _require_same_quality(_validation(), _validation())

    with pytest.raises(RepositoryError, match="Quality result thay đổi"):
        _require_same_quality(_validation(), _validation(2))


def test_pending_snapshot_is_atomically_recovered_after_db_ready(tmp_path: Path) -> None:
    pending = tmp_path / ".pending" / "fixture-snapshot"
    final = tmp_path / "fixture-snapshot"
    pending.mkdir(parents=True)
    (pending / "manifest.json").write_text("{}", encoding="utf-8")

    _recover_pending_snapshot(pending, final)

    assert final.is_dir()
    assert (final / "manifest.json").is_file()
    assert not pending.exists()


def test_missing_pending_snapshot_is_not_silently_accepted(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError, match="thiếu pending/final"):
        _recover_pending_snapshot(
            tmp_path / ".pending" / "fixture-snapshot",
            tmp_path / "fixture-snapshot",
        )
