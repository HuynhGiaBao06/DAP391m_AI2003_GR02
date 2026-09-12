"""Hợp đồng loader và CSV bytes loader độc lập schema HMDA."""

from __future__ import annotations

import csv
from dataclasses import replace
from io import StringIO
from pathlib import Path
from typing import Callable, Mapping, Protocol, TypeAlias, TypeVar, runtime_checkable

from hmda.core.exceptions import DataLoadError
from hmda.data.contracts import DataBatch, SourceDescriptor
from hmda.data.source_identity import (
    RECORD_ID_ALGORITHM,
    identify_source,
    make_record_id,
)


PayloadT = TypeVar("PayloadT", covariant=True)


@runtime_checkable
class DataLoader(Protocol[PayloadT]):
    def load(self, source: SourceDescriptor) -> DataBatch[PayloadT]:
        """Đọc một source đã định danh mà không tự lọc cohort hoặc sửa token."""
        ...


RawRecord: TypeAlias = Mapping[str, object]
ByteReader: TypeAlias = Callable[[str], bytes]


def _read_file_bytes(location: str) -> bytes:
    return Path(location).read_bytes()


class CSVBytesLoader:
    """Đọc bytes đúng một lần, xác minh identity rồi parse token CSV nguyên trạng."""

    def __init__(
        self,
        *,
        encoding: str = "utf-8",
        delimiter: str = ",",
        record_id_field: str = "record_id",
        row_number_field: str = "source_row_number",
        line_number_field: str = "source_line_number",
        read_bytes: ByteReader | None = None,
    ) -> None:
        if not encoding.strip():
            raise DataLoadError("encoding không được rỗng")
        if len(delimiter) != 1:
            raise DataLoadError("delimiter phải có đúng một ký tự")
        technical_fields = (record_id_field, row_number_field, line_number_field)
        if any(not field.strip() for field in technical_fields):
            raise DataLoadError("Tên technical field không được rỗng")
        if len(set(technical_fields)) != len(technical_fields):
            raise DataLoadError("Tên technical field phải khác nhau")

        self.encoding = encoding
        self.delimiter = delimiter
        self.record_id_field = record_id_field
        self.row_number_field = row_number_field
        self.line_number_field = line_number_field
        self._read_bytes = read_bytes or _read_file_bytes

    def load(self, source: SourceDescriptor) -> DataBatch[tuple[RawRecord, ...]]:
        try:
            content = self._read_bytes(source.location)
        except OSError as exc:
            raise DataLoadError("Không thể đọc source bytes") from exc
        if not isinstance(content, bytes):
            raise DataLoadError("Byte reader phải trả về bytes")

        identity = identify_source(source, content)
        try:
            text = content.decode(self.encoding)
        except (LookupError, UnicodeError) as exc:
            raise DataLoadError("Không thể decode source bằng encoding đã cấu hình") from exc

        reader = csv.DictReader(
            StringIO(text, newline=""),
            delimiter=self.delimiter,
            strict=True,
        )
        try:
            headers = tuple(reader.fieldnames or ())
            self._validate_headers(headers)
            records: list[RawRecord] = []
            record_ids: set[str] = set()
            for source_row_number, row in enumerate(reader, start=1):
                if None in row or any(value is None for value in row.values()):
                    raise DataLoadError(
                        f"Số field không khớp header tại source row {source_row_number}"
                    )
                record_id = make_record_id(identity, source_row_number)
                if record_id in record_ids:
                    raise DataLoadError("Phát hiện duplicate technical record_id")
                record_ids.add(record_id)
                raw_record: dict[str, object] = dict(row)
                raw_record[self.record_id_field] = record_id
                raw_record[self.row_number_field] = source_row_number
                raw_record[self.line_number_field] = reader.line_num
                records.append(raw_record)
        except csv.Error as exc:
            raise DataLoadError("CSV parse thất bại") from exc

        resolved_source = replace(source, checksum=identity.checksum)
        return DataBatch(
            payload=tuple(records),
            source=resolved_source,
            metadata={
                "content_checksum": identity.checksum,
                "byte_size": identity.byte_size,
                "encoding": self.encoding,
                "delimiter": self.delimiter,
                "columns": headers,
                "row_count": len(records),
                "source_identity_algorithm": identity.algorithm,
                "record_id_algorithm": RECORD_ID_ALGORITHM,
            },
        )

    def _validate_headers(self, headers: tuple[str, ...]) -> None:
        if not headers:
            raise DataLoadError("CSV phải có header")
        if any(not header.strip() for header in headers):
            raise DataLoadError("Header CSV không được rỗng")
        if len(set(headers)) != len(headers):
            raise DataLoadError("Header CSV bị trùng")
        reserved = {
            self.record_id_field,
            self.row_number_field,
            self.line_number_field,
        }
        conflicts = reserved.intersection(headers)
        if conflicts:
            raise DataLoadError(
                f"Header CSV trùng technical field: {sorted(conflicts)}"
            )
