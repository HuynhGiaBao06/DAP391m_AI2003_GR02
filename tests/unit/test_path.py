from pathlib import Path

import pytest

from hmda.core.exceptions import ProjectRootNotFoundError
from hmda.core.path import ProjectPaths


def test_discover_uses_module_location_when_cwd_is_outside_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = ProjectPaths.discover()
    monkeypatch.chdir(canonical.root.parent)

    paths = ProjectPaths.discover()

    assert paths.root == canonical.root
    assert paths.configs == paths.root / "configs"


def test_discover_from_notebooks_directory_returns_same_root() -> None:
    canonical = ProjectPaths.discover()

    discovered = ProjectPaths.discover(canonical.notebooks)

    assert discovered.root == canonical.root


def test_discover_from_test_file_returns_same_root() -> None:
    canonical = ProjectPaths.discover()

    discovered = ProjectPaths.discover(Path(__file__))

    assert discovered.root == canonical.root


def test_missing_markers_raise_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ProjectRootNotFoundError, match="Không tìm thấy project root"):
        ProjectPaths.discover(tmp_path, markers=("marker-that-does-not-exist",))


def test_resolve_rejects_escape_by_default() -> None:
    paths = ProjectPaths.discover()
    outside = paths.root.parent / "outside-project-fixture"

    with pytest.raises(ProjectRootNotFoundError, match="ngoài project root"):
        paths.resolve(outside)

    assert paths.resolve(outside, allow_outside=True) == outside.resolve()
