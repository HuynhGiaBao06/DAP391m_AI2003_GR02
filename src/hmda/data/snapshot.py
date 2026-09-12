"""Snapshot lifecycle và atomic CSV export độc lập schema/DB cụ thể."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import csv
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Protocol, TypeVar, runtime_checkable

from hmda.core.exceptions import SnapshotError
from hmda.data.contracts import (
    DataBatch,
    SnapshotDescriptor,
    SnapshotStatus,
    ValidationSummary,
)
from hmda.data.source_identity import sha256_bytes
from hmda.data.validator import require_publishable


PayloadT = TypeVar("PayloadT")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_SAFE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


@runtime_checkable
class SnapshotManager(Protocol[PayloadT]):
    def create(
        self,
        batch: DataBatch[PayloadT],
        validation: ValidationSummary,
        *,
        metadata: Mapping[str, Any],
    ) -> SnapshotDescriptor:
        """Tạo và chỉ công bố descriptor READY sau khi export được xác minh."""
        ...


@dataclass(frozen=True, slots=True)
class SnapshotSerialization:
    """Cấu hình serialization tường minh; không chọn token riêng cho HMDA."""

    columns: tuple[str, ...]
    null_token: str
    encoding: str = "utf-8"
    delimiter: str = ","
    line_terminator: str = "\n"
    record_id_field: str = "record_id"

    def __post_init__(self) -> None:
        if not self.columns or any(
            not isinstance(column, str) or not column for column in self.columns
        ):
            raise SnapshotError("columns phải là danh sách tên cột không rỗng")
        if len(set(self.columns)) != len(self.columns):
            raise SnapshotError("columns không được trùng")
        if self.record_id_field not in self.columns:
            raise SnapshotError("record_id_field phải nằm trong columns")
        if not isinstance(self.null_token, str):
            raise SnapshotError("null_token phải là chuỗi được cấu hình tường minh")
        if not isinstance(self.encoding, str) or not self.encoding.strip():
            raise SnapshotError("encoding không được rỗng")
        if not isinstance(self.delimiter, str) or len(self.delimiter) != 1:
            raise SnapshotError("delimiter phải gồm đúng một ký tự")
        if self.delimiter in {"\r", "\n"}:
            raise SnapshotError("delimiter không được là ký tự xuống dòng")
        if self.line_terminator not in {"\n", "\r\n"}:
            raise SnapshotError("line_terminator chỉ hỗ trợ LF hoặc CRLF")


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    """Manifest bất biến mô tả lineage, version, counts và trạng thái snapshot."""

    snapshot_id: str
    status: SnapshotStatus
    source_id: str
    source_version: str
    source_checksum: str
    schema_version: str
    config_hash: str
    code_version: str
    transform_version: str
    row_count: int
    column_count: int
    columns: tuple[str, ...]
    created_at: str
    encoding: str
    delimiter: str
    line_terminator: str
    null_token: str
    record_id_field: str
    quality_error_count: int
    quality_warning_count: int
    data_checksum: str | None = None
    parent_snapshot_id: str | None = None
    protocol_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, SnapshotStatus):
            raise SnapshotError("status phải là SnapshotStatus")
        _validate_identifier(self.snapshot_id, "snapshot_id")
        _require_text(self.source_id, "source_id")
        _require_text(self.source_version, "source_version")
        _require_sha256(self.source_checksum, "source_checksum")
        _require_sha256(self.config_hash, "config_hash")
        for field_name, value in (
            ("schema_version", self.schema_version),
            ("code_version", self.code_version),
            ("transform_version", self.transform_version),
            ("created_at", self.created_at),
        ):
            _require_text(value, field_name)
        if self.parent_snapshot_id is not None:
            _validate_identifier(self.parent_snapshot_id, "parent_snapshot_id")
        if self.protocol_version is not None:
            _require_text(self.protocol_version, "protocol_version")
        if not self.columns or len(set(self.columns)) != len(self.columns):
            raise SnapshotError("Manifest columns phải không rỗng và duy nhất")
        if self.column_count != len(self.columns):
            raise SnapshotError("column_count không khớp columns")
        SnapshotSerialization(
            columns=self.columns,
            null_token=self.null_token,
            encoding=self.encoding,
            delimiter=self.delimiter,
            line_terminator=self.line_terminator,
            record_id_field=self.record_id_field,
        )
        for field_name, value in (
            ("row_count", self.row_count),
            ("column_count", self.column_count),
            ("quality_error_count", self.quality_error_count),
            ("quality_warning_count", self.quality_warning_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise SnapshotError(f"{field_name} phải là số nguyên không âm")
        try:
            parsed_time = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise SnapshotError("created_at phải là ISO-8601 hợp lệ") from exc
        if parsed_time.tzinfo is None:
            raise SnapshotError("created_at phải kèm timezone")
        if self.data_checksum is not None:
            _require_sha256(self.data_checksum, "data_checksum")
        if self.status is SnapshotStatus.READY:
            if self.quality_error_count != 0:
                raise SnapshotError("Snapshot READY không được còn quality ERROR")
            if self.data_checksum is None:
                raise SnapshotError("Snapshot READY phải có data_checksum")

    def transition(
        self,
        status: SnapshotStatus,
        *,
        data_checksum: str | None = None,
    ) -> "SnapshotManifest":
        """Chỉ cho phép STAGING chuyển một lần sang READY hoặc FAILED."""

        if self.status is not SnapshotStatus.STAGING:
            raise SnapshotError("Snapshot đã kết thúc vòng đời và không thể sửa")
        if status not in {SnapshotStatus.READY, SnapshotStatus.FAILED}:
            raise SnapshotError("STAGING chỉ được chuyển sang READY hoặc FAILED")
        return replace(self, status=status, data_checksum=data_checksum)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["columns"] = list(self.columns)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SnapshotManifest":
        try:
            values = dict(payload)
            values["status"] = SnapshotStatus(values["status"])
            values["columns"] = tuple(values["columns"])
            return cls(**values)
        except (KeyError, TypeError, ValueError) as exc:
            raise SnapshotError("Manifest snapshot không đúng hợp đồng") from exc

    def to_descriptor(self) -> SnapshotDescriptor:
        return SnapshotDescriptor(
            snapshot_id=self.snapshot_id,
            status=self.status,
            source_id=self.source_id,
            metadata=self.to_dict(),
        )


def create_staging_manifest(
    batch: DataBatch[Sequence[Mapping[str, Any]]],
    validation: ValidationSummary,
    *,
    snapshot_id: str,
    schema_version: str,
    config_hash: str,
    code_version: str,
    transform_version: str,
    serialization: SnapshotSerialization,
    created_at: str | None = None,
    parent_snapshot_id: str | None = None,
    protocol_version: str | None = None,
) -> SnapshotManifest:
    """Tạo manifest STAGING từ batch/quality thật, không tự sinh snapshot ID."""

    source_checksum = batch.source.checksum or batch.metadata.get("content_checksum")
    if not isinstance(source_checksum, str):
        raise SnapshotError("Batch phải có source checksum đã resolve")
    error_count = validation.metadata.get("error_count", int(not validation.is_valid))
    warning_count = validation.metadata.get("warning_count", 0)
    resolved_columns = serialization.columns
    return SnapshotManifest(
        snapshot_id=snapshot_id,
        status=SnapshotStatus.STAGING,
        source_id=batch.source.source_id,
        source_version=batch.source.version,
        source_checksum=source_checksum,
        schema_version=schema_version,
        config_hash=config_hash,
        code_version=code_version,
        transform_version=transform_version,
        row_count=len(batch.payload),
        column_count=len(resolved_columns),
        columns=resolved_columns,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        encoding=serialization.encoding,
        delimiter=serialization.delimiter,
        line_terminator=serialization.line_terminator,
        null_token=serialization.null_token,
        record_id_field=serialization.record_id_field,
        quality_error_count=_nonnegative_count(error_count, "error_count"),
        quality_warning_count=_nonnegative_count(warning_count, "warning_count"),
        parent_snapshot_id=parent_snapshot_id,
        protocol_version=protocol_version,
    )


class AtomicSnapshotExporter:
    """Ghi snapshot trong staging dir rồi publish bằng một directory rename."""

    def __init__(
        self,
        root: str | Path,
        *,
        publish_directory: Callable[[Path, Path], None] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self._publish_directory = publish_directory or os.replace

    def export(
        self,
        batch: DataBatch[Sequence[Mapping[str, Any]]],
        validation: ValidationSummary,
        manifest: SnapshotManifest,
        serialization: SnapshotSerialization,
    ) -> SnapshotDescriptor:
        """Export, fsync, checksum, readback theo khóa rồi mới công bố READY."""

        self._validate_export_input(batch, manifest, serialization)
        require_publishable(validation)
        self.root.mkdir(parents=True, exist_ok=True)
        final_dir = self.root / manifest.snapshot_id
        if final_dir.exists():
            existing = self.load_ready(manifest.snapshot_id)
            if self._same_identity(existing, manifest, serialization):
                readback = self._read_csv(final_dir / "data.csv", serialization)
                self._assert_readback(batch.payload, readback, serialization)
                return existing.to_descriptor()
            raise SnapshotError("snapshot_id đã thuộc một identity READY khác")

        staging_dir = Path(
            tempfile.mkdtemp(prefix=f".{manifest.snapshot_id}.", dir=self.root)
        )
        try:
            data_path = staging_dir / "data.csv"
            self._write_csv(data_path, batch.payload, serialization)
            data_checksum = sha256_bytes(data_path.read_bytes())
            readback = self._read_csv(data_path, serialization)
            self._assert_readback(batch.payload, readback, serialization)
            ready = manifest.transition(
                SnapshotStatus.READY,
                data_checksum=data_checksum,
            )
            self._write_manifest(staging_dir / "manifest.json", ready)
            self._publish_directory(staging_dir, final_dir)
            return ready.to_descriptor()
        except Exception as exc:
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            if isinstance(exc, SnapshotError):
                raise
            raise SnapshotError("Atomic snapshot export thất bại") from exc

    def load_ready(self, snapshot_id: str) -> SnapshotManifest:
        """Đọc snapshot cụ thể và từ chối trạng thái/chứng cứ không toàn vẹn."""

        _validate_identifier(snapshot_id, "snapshot_id")
        snapshot_dir = self.root / snapshot_id
        manifest_path = snapshot_dir / "manifest.json"
        data_path = snapshot_dir / "data.csv"
        if not manifest_path.is_file() or not data_path.is_file():
            raise SnapshotError("Snapshot chưa có đủ manifest và data")
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SnapshotError("Không thể đọc manifest snapshot") from exc
        if not isinstance(payload, Mapping):
            raise SnapshotError("Manifest snapshot phải là JSON object")
        manifest = SnapshotManifest.from_dict(payload)
        if manifest.snapshot_id != snapshot_id or manifest.status is not SnapshotStatus.READY:
            raise SnapshotError(
                "Reader chỉ chấp nhận snapshot ID cụ thể ở trạng thái READY"
            )
        actual_checksum = sha256_bytes(data_path.read_bytes())
        if actual_checksum != manifest.data_checksum:
            raise SnapshotError("Checksum data.csv không khớp manifest")
        serialization = SnapshotSerialization(
            columns=manifest.columns,
            null_token=manifest.null_token,
            encoding=manifest.encoding,
            delimiter=manifest.delimiter,
            line_terminator=manifest.line_terminator,
            record_id_field=manifest.record_id_field,
        )
        readback = self._read_csv(data_path, serialization)
        if len(readback) != manifest.row_count:
            raise SnapshotError("Readback row_count không khớp manifest")
        _index_unique(readback, serialization.record_id_field, "readback")
        return manifest

    @staticmethod
    def _validate_export_input(batch, manifest, serialization) -> None:
        if manifest.status is not SnapshotStatus.STAGING:
            raise SnapshotError("Export chỉ nhận manifest STAGING")
        if batch.source.source_id != manifest.source_id:
            raise SnapshotError("Batch source không khớp manifest")
        if len(batch.payload) != manifest.row_count:
            raise SnapshotError("Batch row_count không khớp manifest")
        if manifest.columns != serialization.columns:
            raise SnapshotError("Serialization columns không khớp manifest")
        if (
            manifest.encoding,
            manifest.delimiter,
            manifest.line_terminator,
            manifest.null_token,
            manifest.record_id_field,
        ) != (
            serialization.encoding,
            serialization.delimiter,
            serialization.line_terminator,
            serialization.null_token,
            serialization.record_id_field,
        ):
            raise SnapshotError("Serialization config không khớp manifest")
        if any(not isinstance(row, Mapping) for row in batch.payload):
            raise SnapshotError("Snapshot payload phải gồm các record dạng mapping")
        expected = set(serialization.columns)
        if any(set(row.keys()) != expected for row in batch.payload):
            raise SnapshotError("Mỗi record phải có đúng column contract")

    @staticmethod
    def _write_csv(
        path: Path,
        rows: Sequence[Mapping[str, Any]],
        serialization: SnapshotSerialization,
    ) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            with temp_path.open(
                "w", encoding=serialization.encoding, newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=serialization.columns,
                    delimiter=serialization.delimiter,
                    lineterminator=serialization.line_terminator,
                    extrasaction="raise",
                )
                writer.writeheader()
                for row in rows:
                    writer.writerow(
                        {
                            column: _serialize_value(row[column], serialization.null_token)
                            for column in serialization.columns
                        }
                    )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _read_csv(
        path: Path,
        serialization: SnapshotSerialization,
    ) -> tuple[dict[str, str | None], ...]:
        try:
            with path.open("r", encoding=serialization.encoding, newline="") as handle:
                reader = csv.DictReader(handle, delimiter=serialization.delimiter)
                if tuple(reader.fieldnames or ()) != serialization.columns:
                    raise SnapshotError("Readback column order không khớp")
                return tuple(
                    {
                        column: None if value == serialization.null_token else value
                        for column, value in row.items()
                    }
                    for row in reader
                )
        except (OSError, UnicodeError, csv.Error) as exc:
            raise SnapshotError("Không thể readback data.csv") from exc

    @staticmethod
    def _assert_readback(
        source_rows: Sequence[Mapping[str, Any]],
        readback_rows: Sequence[Mapping[str, Any]],
        serialization: SnapshotSerialization,
    ) -> None:
        key = serialization.record_id_field

        def normalized(row: Mapping[str, Any]) -> dict[str, str | None]:
            return {
                column: (
                    None
                    if row[column] is None
                    else _serialize_value(row[column], serialization.null_token)
                )
                for column in serialization.columns
            }

        expected = tuple(normalized(row) for row in source_rows)
        expected_by_key = _index_unique(expected, key, "input")
        actual_by_key = _index_unique(readback_rows, key, "readback")
        if expected_by_key != actual_by_key:
            raise SnapshotError("Readback không khớp nội dung input theo record_id")

    @staticmethod
    def _write_manifest(path: Path, manifest: SnapshotManifest) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        content = json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            with temp_path.open("wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _same_identity(
        existing: SnapshotManifest,
        candidate: SnapshotManifest,
        serialization: SnapshotSerialization,
    ) -> bool:
        return (
            existing.snapshot_id,
            existing.source_id,
            existing.source_version,
            existing.source_checksum,
            existing.schema_version,
            existing.config_hash,
            existing.code_version,
            existing.transform_version,
            existing.row_count,
            existing.columns,
            existing.encoding,
            existing.delimiter,
            existing.line_terminator,
            existing.null_token,
            existing.record_id_field,
        ) == (
            candidate.snapshot_id,
            candidate.source_id,
            candidate.source_version,
            candidate.source_checksum,
            candidate.schema_version,
            candidate.config_hash,
            candidate.code_version,
            candidate.transform_version,
            candidate.row_count,
            serialization.columns,
            serialization.encoding,
            serialization.delimiter,
            serialization.line_terminator,
            serialization.null_token,
            serialization.record_id_field,
        )


class AtomicSnapshotManager:
    """Adapter SnapshotManager lấy metadata version tường minh từ caller."""

    def __init__(self, exporter: AtomicSnapshotExporter) -> None:
        self.exporter = exporter

    def create(
        self,
        batch: DataBatch[Sequence[Mapping[str, Any]]],
        validation: ValidationSummary,
        *,
        metadata: Mapping[str, Any],
    ) -> SnapshotDescriptor:
        serialization = metadata.get("serialization")
        if not isinstance(serialization, SnapshotSerialization):
            raise SnapshotError("metadata.serialization phải là SnapshotSerialization")
        manifest = create_staging_manifest(
            batch,
            validation,
            snapshot_id=_metadata_text(metadata, "snapshot_id"),
            schema_version=_metadata_text(metadata, "schema_version"),
            config_hash=_metadata_text(metadata, "config_hash"),
            code_version=_metadata_text(metadata, "code_version"),
            transform_version=_metadata_text(metadata, "transform_version"),
            serialization=serialization,
            created_at=metadata.get("created_at"),
            parent_snapshot_id=metadata.get("parent_snapshot_id"),
            protocol_version=metadata.get("protocol_version"),
        )
        return self.exporter.export(batch, validation, manifest, serialization)


def _serialize_value(value: Any, null_token: str) -> str:
    if value is None:
        return null_token
    if not isinstance(value, (str, int, float, bool)):
        raise SnapshotError("CSV snapshot chỉ hỗ trợ scalar string/number/boolean/None")
    serialized = str(value)
    if serialized == null_token:
        raise SnapshotError("Giá trị chuỗi trùng null_token gây serialization mơ hồ")
    return serialized


def _index_unique(
    rows: Sequence[Mapping[str, Any]], key: str, label: str
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            raise SnapshotError(f"{label} thiếu record_id để đối soát")
        text_value = str(value)
        if text_value in indexed:
            raise SnapshotError(f"{label} trùng record_id khi đối soát")
        indexed[text_value] = row
    return indexed


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{field_name} không được rỗng")
    return value


def _metadata_text(metadata: Mapping[str, Any], field_name: str) -> str:
    return _require_text(metadata.get(field_name), f"metadata.{field_name}")


def _require_sha256(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value.lower()):
        raise SnapshotError(f"{field_name} phải là SHA-256 hexadecimal")
    return value.lower()


def _validate_identifier(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID_PATTERN.fullmatch(value):
        raise SnapshotError(f"{field_name} không phải identifier an toàn")
    return value


def _nonnegative_count(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SnapshotError(f"quality {field_name} phải là số nguyên không âm")
    return value
