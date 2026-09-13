import pytest

from hmda.core.exceptions import SourceIdentityError
from hmda.data.contracts import SourceDescriptor
from hmda.data.source_identity import identify_source, make_record_id, sha256_bytes


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
