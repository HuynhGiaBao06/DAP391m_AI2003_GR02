import pytest

from hmda.core.exceptions import DataLoadError, SourceIdentityError
from hmda.data.contracts import SourceDescriptor
from hmda.data.loader import CSVBytesLoader
from hmda.data.source_identity import sha256_bytes


def _source(location: str = "memory://fixture", checksum: str | None = None):
    return SourceDescriptor("fixture-source", "v1", location, checksum)


def test_loader_reads_once_and_preserves_raw_tokens_on_retry() -> None:
    content = b"code,note\n01,NA\n02,Exempt\n03,\n"
    calls: list[str] = []

    def reader(location: str) -> bytes:
        calls.append(location)
        return content

    loader = CSVBytesLoader(read_bytes=reader)
    first = loader.load(_source())
    retry = loader.load(_source())

    assert calls == ["memory://fixture", "memory://fixture"]
    assert first == retry
    assert first.source.checksum == sha256_bytes(content)
    assert [record["code"] for record in first.payload] == ["01", "02", "03"]
    assert [record["note"] for record in first.payload] == ["NA", "Exempt", ""]
    assert [record["source_row_number"] for record in first.payload] == [1, 2, 3]
    assert len({record["record_id"] for record in first.payload}) == 3


def test_default_loader_reads_a_file_source(tmp_path) -> None:
    source_path = tmp_path / "source.csv"
    source_path.write_bytes(b"code,value\n001,kept\n")

    batch = CSVBytesLoader().load(_source(str(source_path)))

    assert batch.metadata["row_count"] == 1
    assert batch.payload[0]["code"] == "001"
    assert batch.source.checksum == sha256_bytes(source_path.read_bytes())


def test_line_order_changes_checksum_and_record_identity() -> None:
    first = CSVBytesLoader(read_bytes=lambda _: b"value\na\nb\n").load(_source())
    reordered = CSVBytesLoader(read_bytes=lambda _: b"value\nb\na\n").load(_source())

    assert first.source.checksum != reordered.source.checksum
    assert [row["record_id"] for row in first.payload] != [
        row["record_id"] for row in reordered.payload
    ]


def test_loader_rejects_changed_source_before_parse() -> None:
    expected = sha256_bytes(b"value\noriginal\n")
    loader = CSVBytesLoader(read_bytes=lambda _: b"value\nchanged\n")

    with pytest.raises(SourceIdentityError, match="đã thay đổi"):
        loader.load(_source(checksum=expected))


def test_loader_wraps_encoding_and_csv_parse_failures() -> None:
    with pytest.raises(DataLoadError, match="decode"):
        CSVBytesLoader(read_bytes=lambda _: b"\xff").load(_source())

    with pytest.raises(DataLoadError, match="CSV parse"):
        CSVBytesLoader(read_bytes=lambda _: b'column\n"unterminated\n').load(_source())


@pytest.mark.parametrize(
    "content, message",
    [
        (b"a,a\n1,2\n", "Header CSV bị trùng"),
        (b"record_id,value\nx,1\n", "technical field"),
        (b"a,b\n1\n", "không khớp header"),
    ],
)
def test_loader_rejects_ambiguous_or_malformed_rows(content: bytes, message: str) -> None:
    with pytest.raises(DataLoadError, match=message):
        CSVBytesLoader(read_bytes=lambda _: content).load(_source())


def test_loader_detects_duplicate_generated_record_ids(monkeypatch) -> None:
    monkeypatch.setattr("hmda.data.loader.make_record_id", lambda identity, row_number: "same")

    with pytest.raises(DataLoadError, match="duplicate technical"):
        CSVBytesLoader(read_bytes=lambda _: b"value\na\nb\n").load(_source())
