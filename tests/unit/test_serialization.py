import csv

import pytest

from hmda.core.exceptions import SnapshotError
from hmda.data.contracts import DataBatch, SourceDescriptor, ValidationSummary
from hmda.data.snapshot import (
    AtomicSnapshotExporter,
    SnapshotSerialization,
    create_staging_manifest,
)


def _case(rows, serialization):
    checksum = "a" * 64
    batch = DataBatch(
        payload=tuple(rows),
        source=SourceDescriptor(
            "fixture-source", "v1", "memory://fixture", checksum
        ),
        metadata={"content_checksum": checksum},
    )
    validation = ValidationSummary(
        is_valid=True,
        metadata={"error_count": 0, "warning_count": 0},
    )
    manifest = create_staging_manifest(
        batch,
        validation,
        snapshot_id="fixture-serialization",
        schema_version="schema-v1",
        config_hash="b" * 64,
        code_version="code-v1",
        transform_version="transform-v1",
        serialization=serialization,
        created_at="2026-09-11T00:00:00+00:00",
    )
    return batch, validation, manifest


def test_serialization_uses_configured_order_delimiter_newline_and_null(tmp_path) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value", "note"),
        null_token="NULL-FIXTURE",
        delimiter=";",
        line_terminator="\r\n",
    )
    case = _case(
        (
            {"record_id": "r1", "value": "001", "note": None},
            {"record_id": "r2", "value": "a;b", "note": "kept"},
        ),
        serialization,
    )

    AtomicSnapshotExporter(tmp_path).export(*case, serialization)
    content = (tmp_path / "fixture-serialization" / "data.csv").read_bytes()

    assert content.startswith(b"record_id;value;note\r\n")
    assert b"r1;001;NULL-FIXTURE\r\n" in content
    assert b'r2;"a;b";kept\r\n' in content


def test_literal_equal_to_null_token_is_rejected_as_ambiguous(tmp_path) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value"),
        null_token="NULL-FIXTURE",
    )
    case = _case(
        ({"record_id": "r1", "value": "NULL-FIXTURE"},),
        serialization,
    )

    with pytest.raises(SnapshotError, match="mơ hồ"):
        AtomicSnapshotExporter(tmp_path).export(*case, serialization)
    assert list(tmp_path.iterdir()) == []


def test_readback_compares_content_by_record_id_not_only_file_hash(
    tmp_path, monkeypatch
) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value"),
        null_token="NULL-FIXTURE",
    )
    case = _case(({"record_id": "r1", "value": "original"},), serialization)

    def mismatched_readback(path, config):
        return ({"record_id": "r1", "value": "changed"},)

    monkeypatch.setattr(
        AtomicSnapshotExporter, "_read_csv", staticmethod(mismatched_readback)
    )
    with pytest.raises(SnapshotError, match="theo record_id"):
        AtomicSnapshotExporter(tmp_path).export(*case, serialization)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("record_id", [None, ""])
def test_readback_reconciliation_requires_nonempty_record_id(tmp_path, record_id) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value"),
        null_token="NULL-FIXTURE",
    )
    case = _case(({"record_id": record_id, "value": "x"},), serialization)

    with pytest.raises(SnapshotError, match="thiếu record_id"):
        AtomicSnapshotExporter(tmp_path).export(*case, serialization)


def test_readback_reconciliation_rejects_duplicate_record_id(tmp_path) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value"),
        null_token="NULL-FIXTURE",
    )
    case = _case(
        (
            {"record_id": "same", "value": "x"},
            {"record_id": "same", "value": "y"},
        ),
        serialization,
    )

    with pytest.raises(SnapshotError, match="trùng record_id"):
        AtomicSnapshotExporter(tmp_path).export(*case, serialization)


def test_exported_csv_can_be_read_with_standard_csv_contract(tmp_path) -> None:
    serialization = SnapshotSerialization(
        columns=("record_id", "value"),
        null_token="NULL-FIXTURE",
    )
    case = _case(({"record_id": "r1", "value": "001"},), serialization)
    AtomicSnapshotExporter(tmp_path).export(*case, serialization)

    with (tmp_path / "fixture-serialization" / "data.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [{"record_id": "r1", "value": "001"}]
