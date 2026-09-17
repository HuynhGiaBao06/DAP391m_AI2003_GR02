from typing import Any

import pytest

from hmda.core.exceptions import SourceIdentityError
from hmda.data.contracts import SourceDescriptor
from hmda.data.source_identity import (
    identify_source,
    make_record_id,
    require_registered_source,
    sha256_bytes,
)


def _source(*, source_id: str = "fixture-source", checksum: str | None = None):
    return SourceDescriptor(source_id, "v1", "memory://fixture", checksum)


def test_source_identity_is_deterministic_and_namespaced() -> None:
    content = b"a,b\n1,2\n"
    first = identify_source(_source(), content)
    retry = identify_source(_source(), content)
    other_namespace = identify_source(_source(source_id="other-source"), content)

    assert first == retry
    assert first.checksum == sha256_bytes(content)
    assert make_record_id(first, 1) == make_record_id(retry, 1)
    assert make_record_id(first, 1) != make_record_id(first, 2)
    assert make_record_id(first, 1) != make_record_id(other_namespace, 1)


def test_changed_bytes_fail_against_registered_checksum() -> None:
    original = b"a\n1\n"
    registered = _source(checksum=sha256_bytes(original))

    with pytest.raises(SourceIdentityError, match="đã thay đổi"):
        identify_source(registered, b"a\n2\n")


@pytest.mark.parametrize("checksum", ["short", "z" * 64])
def test_registered_checksum_must_be_sha256(checksum: str) -> None:
    with pytest.raises(SourceIdentityError, match="SHA-256"):
        identify_source(_source(checksum=checksum), b"content")


def test_registered_source_guard_rejects_provisional_config_without_guessing() -> None:
    config = {
        "source": {
            "source_id": "provisional",
            "version": None,
            "version_status": "PENDING",
            "provenance_url": None,
            "provenance_status": "PENDING",
            "local_path": "data/raw/source.csv",
            "sha256": "a" * 64,
        },
        "cohort": {
            "publishable": False,
            "blocking_reasons": ["source version is unknown"],
        },
    }

    with pytest.raises(SourceIdentityError, match="chưa được phép publish"):
        require_registered_source(config)


def test_registered_source_guard_returns_descriptor_only_for_verified_source() -> None:
    config = {
        "source": {
            "source_id": "registered-source",
            "version": "2024-release",
            "version_status": "VERIFIED",
            "provenance_url": "https://example.test/source.csv",
            "provenance_status": "VERIFIED",
            "local_path": "data/raw/source.csv",
            "sha256": "A" * 64,
        },
        "cohort": {"publishable": True, "blocking_reasons": []},
    }

    descriptor = require_registered_source(config)

    assert descriptor == SourceDescriptor(
        "registered-source", "2024-release", "data/raw/source.csv", "a" * 64
    )


def _owner_attested_config() -> dict[str, Any]:
    return {
        "source": {
            "source_id": "owner-source",
            "version": "owner-derived-v1",
            "version_kind": "INTERNAL_DERIVED_ASSET",
            "version_status": "VERIFIED_INTERNAL",
            "identity_mode": "OWNER_ATTESTED_LOCAL_DERIVED",
            "provenance_url": None,
            "provenance_status": "NOT_APPLICABLE_OWNER_ATTESTED",
            "attestation": {
                "status": "VERIFIED_USER_CONFIRMED",
                "owner": "BaoHG",
                "data_admin": "BaoHG",
                "downloaded_on": "2026-09-13",
                "transformations": ["select_18_columns", "map_action_taken"],
            },
            "local_path": "data/raw/source.csv",
            "sha256": "b" * 64,
        },
        "cohort": {"publishable": True, "blocking_reasons": []},
    }


def test_registered_source_guard_accepts_complete_owner_attestation_without_url() -> None:
    descriptor = require_registered_source(_owner_attested_config())

    assert descriptor == SourceDescriptor(
        "owner-source", "owner-derived-v1", "data/raw/source.csv", "b" * 64
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "PENDING", "status VERIFIED"),
        ("owner", "", "owner"),
        ("data_admin", None, "data_admin"),
        ("downloaded_on", "13/09/2026", "YYYY-MM-DD"),
        ("transformations", [], "transformations"),
    ],
)
def test_owner_attested_source_requires_complete_attestation(
    field: str, value: object, message: str
) -> None:
    config = _owner_attested_config()
    config["source"]["attestation"][field] = value

    with pytest.raises(SourceIdentityError, match=message):
        require_registered_source(config)


def test_registered_source_guard_rejects_unknown_identity_mode() -> None:
    config = _owner_attested_config()
    config["source"]["identity_mode"] = "TRUST_ME"

    with pytest.raises(SourceIdentityError, match="identity_mode không hỗ trợ"):
        require_registered_source(config)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("cohort", "blocking_reasons"), ["county format"], "blocking_reasons"),
        (("source", "version"), None, "source version"),
        (("source", "version_status"), "PENDING", "version_status"),
        (("source", "provenance_url"), None, "provenance_url"),
        (("source", "provenance_url"), "not-a-url", "URL HTTP"),
        (("source", "provenance_status"), "PENDING", "provenance_status"),
    ],
)
def test_registered_source_guard_rejects_inconsistent_publishable_config(
    path: tuple[str, str], value: object, message: str
) -> None:
    config = {
        "source": {
            "source_id": "registered-source",
            "version": "2024-release",
            "version_status": "VERIFIED",
            "provenance_url": "https://example.test/source.csv",
            "provenance_status": "VERIFIED",
            "local_path": "data/raw/source.csv",
            "sha256": "a" * 64,
        },
        "cohort": {"publishable": True, "blocking_reasons": []},
    }
    config[path[0]][path[1]] = value

    with pytest.raises(SourceIdentityError, match=message):
        require_registered_source(config)
