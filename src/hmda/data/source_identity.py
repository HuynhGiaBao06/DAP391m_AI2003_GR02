"""Nhận dạng source và technical record ID từ đúng bytes đầu vào."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from hmda.core.exceptions import SourceIdentityError
from hmda.data.contracts import SourceDescriptor


SOURCE_IDENTITY_ALGORITHM = "sha256-source-v1"
RECORD_ID_ALGORITHM = "sha256-record-v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
EXTERNAL_URL_MODE = "EXTERNAL_URL"
OWNER_ATTESTED_MODE = "OWNER_ATTESTED_LOCAL_DERIVED"


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


def require_registered_source(data_config: Mapping[str, Any]) -> SourceDescriptor:
    """Tạo descriptor chỉ khi source config đã đủ điều kiện publish.

    Nguồn ngoài phải có URL đã xác minh. File dẫn xuất nội bộ có thể dùng owner
    attestation đầy đủ; guard không suy diễn upstream provenance từ checksum hoặc
    timestamp hệ thống.
    """

    if not isinstance(data_config, Mapping):
        raise SourceIdentityError("data config phải là mapping")
    source = data_config.get("source")
    cohort = data_config.get("cohort")
    if not isinstance(source, Mapping) or not isinstance(cohort, Mapping):
        raise SourceIdentityError("data config thiếu source hoặc cohort")

    raw_blockers = cohort.get("blocking_reasons", ())
    if isinstance(raw_blockers, (str, bytes)) or not isinstance(
        raw_blockers, (list, tuple)
    ):
        raise SourceIdentityError("blocking_reasons phải là danh sách")
    blockers = tuple(
        str(reason).strip() for reason in raw_blockers if str(reason).strip()
    )
    if cohort.get("publishable") is not True:
        detail = f": {'; '.join(blockers)}" if blockers else ""
        raise SourceIdentityError(f"Source chưa được phép publish{detail}")
    if blockers:
        raise SourceIdentityError("Source publishable không được còn blocking_reasons")

    version = source.get("version")
    if not isinstance(version, str) or not version.strip():
        raise SourceIdentityError("Source publishable phải có source version")
    if not _is_verified_status(source.get("version_status")):
        raise SourceIdentityError("Source publishable phải có version_status VERIFIED")

    raw_mode = source.get("identity_mode", EXTERNAL_URL_MODE)
    if not isinstance(raw_mode, str) or not raw_mode.strip():
        raise SourceIdentityError("Source publishable phải có identity_mode")
    identity_mode = raw_mode.strip().upper()
    if identity_mode == EXTERNAL_URL_MODE:
        _require_external_provenance(source)
    elif identity_mode == OWNER_ATTESTED_MODE:
        _require_owner_attestation(source)
    else:
        raise SourceIdentityError(f"identity_mode không hỗ trợ: {raw_mode}")

    source_id = source.get("source_id")
    location = source.get("local_path")
    checksum = source.get("sha256")
    if not isinstance(source_id, str) or not source_id.strip():
        raise SourceIdentityError("Source publishable phải có source_id")
    if not isinstance(location, str) or not location.strip():
        raise SourceIdentityError("Source publishable phải có local_path")
    if not isinstance(checksum, str) or not _SHA256_PATTERN.fullmatch(
        checksum.lower()
    ):
        raise SourceIdentityError("Source publishable phải có SHA-256 hợp lệ")

    return SourceDescriptor(
        source_id=source_id,
        version=version,
        location=location,
        checksum=checksum.lower(),
    )


def _is_verified_status(value: Any) -> bool:
    return isinstance(value, str) and value.upper().startswith("VERIFIED")


def _require_external_provenance(source: Mapping[str, Any]) -> None:
    provenance_url = source.get("provenance_url")
    if not isinstance(provenance_url, str) or not provenance_url.strip():
        raise SourceIdentityError("Source URL mode phải có provenance_url")
    parsed_provenance = urlparse(provenance_url)
    if (
        parsed_provenance.scheme not in {"http", "https"}
        or not parsed_provenance.netloc
    ):
        raise SourceIdentityError("provenance_url phải là URL HTTP(S) hợp lệ")
    if not _is_verified_status(source.get("provenance_status")):
        raise SourceIdentityError("Source URL mode phải có provenance_status VERIFIED")


def _require_owner_attestation(source: Mapping[str, Any]) -> None:
    if source.get("version_kind") != "INTERNAL_DERIVED_ASSET":
        raise SourceIdentityError(
            "Owner-attested source phải có version_kind INTERNAL_DERIVED_ASSET"
        )
    if source.get("provenance_status") != "NOT_APPLICABLE_OWNER_ATTESTED":
        raise SourceIdentityError(
            "Owner-attested source phải khai báo provenance_status phù hợp"
        )

    attestation = source.get("attestation")
    if not isinstance(attestation, Mapping):
        raise SourceIdentityError("Owner-attested source phải có attestation")
    if not _is_verified_status(attestation.get("status")):
        raise SourceIdentityError("Owner attestation phải có status VERIFIED")
    for field_name in ("owner", "data_admin"):
        value = attestation.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise SourceIdentityError(f"Owner attestation thiếu {field_name}")

    downloaded_on = attestation.get("downloaded_on")
    if not isinstance(downloaded_on, str):
        raise SourceIdentityError("Owner attestation thiếu downloaded_on")
    try:
        date.fromisoformat(downloaded_on)
    except ValueError as exc:
        raise SourceIdentityError(
            "Owner attestation downloaded_on phải theo YYYY-MM-DD"
        ) from exc

    transformations = attestation.get("transformations")
    if (
        isinstance(transformations, (str, bytes))
        or not isinstance(transformations, (list, tuple))
        or not transformations
        or any(
            not isinstance(value, str) or not value.strip()
            for value in transformations
        )
    ):
        raise SourceIdentityError(
            "Owner-attested source phải khai báo transformations"
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
