"""Tìm project root từ vị trí module, không phụ thuộc current working directory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from hmda.core.exceptions import ProjectRootNotFoundError


DEFAULT_MARKERS = ("pyproject.toml", "src/hmda")


def _start_directory(start: Path) -> Path:
    resolved = start.resolve()
    return resolved.parent if resolved.is_file() else resolved


def _has_markers(candidate: Path, markers: Iterable[str]) -> bool:
    return all((candidate / marker).exists() for marker in markers)


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Các đường dẫn chuẩn được neo tại project root đã xác minh."""

    root: Path

    @classmethod
    def discover(
        cls,
        start: str | Path | None = None,
        *,
        markers: tuple[str, ...] = DEFAULT_MARKERS,
    ) -> "ProjectPaths":
        if not markers or any(not marker.strip() for marker in markers):
            raise ProjectRootNotFoundError("Danh sách marker project không hợp lệ")

        anchor = Path(start) if start is not None else Path(__file__)
        current = _start_directory(anchor)
        for candidate in (current, *current.parents):
            if _has_markers(candidate, markers):
                return cls(candidate)

        marker_text = ", ".join(markers)
        raise ProjectRootNotFoundError(
            f"Không tìm thấy project root từ '{current}' với marker: {marker_text}"
        )

    def resolve(
        self,
        path: str | Path,
        *,
        must_exist: bool = False,
        allow_outside: bool = False,
    ) -> Path:
        raw_path = Path(path)
        candidate = raw_path.resolve() if raw_path.is_absolute() else (self.root / raw_path).resolve()

        if not allow_outside and candidate != self.root and self.root not in candidate.parents:
            raise ProjectRootNotFoundError(
                f"Đường dẫn nằm ngoài project root: {candidate}"
            )
        if must_exist and not candidate.exists():
            raise ProjectRootNotFoundError(f"Đường dẫn bắt buộc không tồn tại: {candidate}")
        return candidate

    @property
    def configs(self) -> Path:
        return self.root / "configs"

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def notebooks(self) -> Path:
        return self.root / "notebooks"
