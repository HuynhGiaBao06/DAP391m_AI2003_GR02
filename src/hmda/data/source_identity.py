"""Nhận dạng source và technical record ID từ đúng bytes đầu vào."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from hmda.core.exceptions import SourceIdentityError
from hmda.data.contracts import SourceDescriptor


SOURCE_IDENTITY_ALGORITHM = "sha256-source-v1"
RECORD_ID_ALGORITHM = "sha256-record-v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def sha256_bytes(content: bytes) -> str:
    """Tính SHA-256 trên đúng chuỗi bytes sẽ được parse."""

    if not isinstance(content, bytes):
        raise SourceIdentityError("Nội dung source phải là bytes")
    return sha256(content).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    """Danh tính source đã resolve từ namespace, version và content bytes."""

    source_id: str
    version: str
    checksum: str
    byte_size: int
    algorithm: str = SOURCE_IDENTITY_ALGORITHM

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise SourceIdentityError("source_id không được rỗng")
        if not isinstance(self.version, str) or not self.version.strip():
            raise SourceIdentityError("source version không được rỗng")
        if not isinstance(self.checksum, str) or not _SHA256_PATTERN.fullmatch(
            self.checksum.lower()
        ):
            raise SourceIdentityError("checksum phải là SHA-256 dạng hexadecimal")
        if (
            isinstance(self.byte_size, bool)
            or not isinstance(self.byte_size, int)
            or self.byte_size < 0
        ):
            raise SourceIdentityError("byte_size không được âm")


def identify_source(source: SourceDescriptor, content: bytes) -> SourceIdentity:
    """Resolve identity và phát hiện source đổi bytes so với checksum đã đăng ký."""

    text_fields = (source.source_id, source.version, source.location)
    if any(not isinstance(value, str) or not value.strip() for value in text_fields):
        raise SourceIdentityError("source_id, version và location không được rỗng")

    actual_checksum = sha256_bytes(content)
    if source.checksum is not None:
        expected_checksum = source.checksum.lower()
        if not _SHA256_PATTERN.fullmatch(expected_checksum):
            raise SourceIdentityError("checksum đã đăng ký không phải SHA-256 hợp lệ")
        if expected_checksum != actual_checksum:
            raise SourceIdentityError("Source bytes đã thay đổi so với checksum đã đăng ký")

    return SourceIdentity(
        source_id=source.source_id,
        version=source.version,
        checksum=actual_checksum,
        byte_size=len(content),
    )


def make_record_id(identity: SourceIdentity, source_row_number: int) -> str:
    """Sinh record ID ổn định theo source identity và số thứ tự dòng gốc."""

    if (
        isinstance(source_row_number, bool)
        or not isinstance(source_row_number, int)
        or source_row_number < 1
    ):
        raise SourceIdentityError("source_row_number phải là số nguyên dương")
    payload = json.dumps(
        [
            RECORD_ID_ALGORITHM,
            identity.source_id,
            identity.version,
            identity.checksum,
            source_row_number,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()
