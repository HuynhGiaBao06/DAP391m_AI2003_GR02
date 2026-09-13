"""Nạp, kiểm và đóng băng cấu hình mà không làm lộ secret."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping, MutableMapping

from dotenv import dotenv_values
import yaml

from hmda.core.exceptions import (
    ConfigurationError,
    MissingEnvironmentVariableError,
)
from hmda.core.path import ProjectPaths


DEFAULT_CONFIG_FILES = (
    "project.yaml",
    "database.yaml",
    "data.yaml",
    "schema.yaml",
    "quality.yaml",
    "preprocessing.yaml",
    "training.yaml",
    "evaluation.yaml",
    "logging.yaml",
)
REDACTED = "***REDACTED***"
_SENSITIVE_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "credential",
    "api_key",
    "connection_uri",
    "dsn",
)


def _is_sensitive(path: tuple[str, ...]) -> bool:
    joined = ".".join(path).lower()
    return any(fragment in joined for fragment in _SENSITIVE_FRAGMENTS)


def _redact(values: Any, secret_paths: frozenset[tuple[str, ...]], path: tuple[str, ...] = ()) -> Any:
    if path in secret_paths or _is_sensitive(path):
        return REDACTED if values is not None else None
    if isinstance(values, Mapping):
        return {
            str(key): _redact(value, secret_paths, (*path, str(key)))
            for key, value in values.items()
        }
    if isinstance(values, list):
        return [_redact(value, secret_paths, (*path, str(index))) for index, value in enumerate(values)]
    return deepcopy(values)


@dataclass(frozen=True, slots=True)
class ConfigBundle:
    """Cấu hình đã resolve cùng nguồn và vị trí secret."""

    values: Mapping[str, Any]
    sources: tuple[Path, ...]
    secret_paths: frozenset[tuple[str, ...]] = frozenset()

    def get(self, dotted_path: str, default: Any = None) -> Any:
        current: Any = self.values
        for part in dotted_path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current

    def redacted(self) -> dict[str, Any]:
        return _redact(self.values, self.secret_paths)

    def canonical_json(self) -> str:
        return json.dumps(
            self.redacted(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    def config_hash(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def secret_values(self) -> tuple[str, ...]:
        found: list[str] = []
        for path in self.secret_paths:
            current: Any = self.values
            for part in path:
                if not isinstance(current, Mapping) or part not in current:
                    current = None
                    break
                current = current[part]
            if current not in (None, ""):
                found.append(str(current))
        return tuple(found)


class ConfigLoader:
    """Nạp các YAML theo tên file, resolve env reference và kiểm core contract."""

    def __init__(
        self,
        paths: ProjectPaths | None = None,
        *,
        config_dir: str | Path | None = None,
        filenames: tuple[str, ...] = DEFAULT_CONFIG_FILES,
    ) -> None:
        self.paths = paths or ProjectPaths.discover()
        self.config_dir = (
            self.paths.configs
            if config_dir is None
            else self.paths.resolve(config_dir, allow_outside=True)
        )
        self.filenames = filenames

    def load(
        self,
        *,
        overrides: Mapping[str, Any] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> ConfigBundle:
        values: dict[str, Any] = {}
        sources: list[Path] = []
        for filename in self.filenames:
            path = self.config_dir / filename
            if not path.is_file():
                raise ConfigurationError("Thiếu file cấu hình bắt buộc", field_path=filename)
            try:
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, yaml.YAMLError) as exc:
                raise ConfigurationError(
                    "Không thể đọc YAML hợp lệ", field_path=filename
                ) from exc
            if document is None:
                document = {}
            if not isinstance(document, Mapping):
                raise ConfigurationError("Root YAML phải là mapping", field_path=filename)
            values[path.stem] = deepcopy(dict(document))
            sources.append(path)

        self._apply_overrides(values, overrides or {})
        secret_paths: set[tuple[str, ...]] = set()
        runtime_environment = (
            self._load_runtime_environment()
            if environment is None
            else environment
        )
        resolved = self._resolve_environment(
            values,
            runtime_environment,
            secret_paths,
        )
        self._validate(resolved)
        return ConfigBundle(resolved, tuple(sources), frozenset(secret_paths))

    def _load_runtime_environment(self) -> dict[str, str]:
        """Nạp local.env nếu có; biến process luôn có quyền ưu tiên cao hơn."""

        runtime_environment: dict[str, str] = {}
        local_env_path = self.config_dir / "local.env"
        if local_env_path.is_file():
            try:
                local_values = dotenv_values(
                    dotenv_path=local_env_path,
                    encoding="utf-8",
                    interpolate=False,
                )
            except (OSError, UnicodeError) as exc:
                raise ConfigurationError(
                    "Không thể đọc file môi trường local",
                    field_path="local.env",
                ) from exc
            runtime_environment.update(
                {
                    str(key): str(value)
                    for key, value in local_values.items()
                    if value is not None
                }
            )
        runtime_environment.update(os.environ)
        return runtime_environment

    @staticmethod
    def _apply_overrides(values: MutableMapping[str, Any], overrides: Mapping[str, Any]) -> None:
        for dotted_path, replacement in overrides.items():
            parts = dotted_path.split(".")
            if not parts or any(not part for part in parts):
                raise ConfigurationError("Override path không hợp lệ", field_path=dotted_path)
            current: MutableMapping[str, Any] = values
            for part in parts[:-1]:
                next_value = current.get(part)
                if not isinstance(next_value, MutableMapping):
                    raise ConfigurationError("Override path không tồn tại", field_path=dotted_path)
                current = next_value
            leaf = parts[-1]
            if leaf not in current:
                raise ConfigurationError("Override path không tồn tại", field_path=dotted_path)
            current[leaf] = deepcopy(replacement)

    def _resolve_environment(
        self,
        value: Any,
        environment: Mapping[str, str],
        secret_paths: set[tuple[str, ...]],
        path: tuple[str, ...] = (),
    ) -> Any:
        if isinstance(value, Mapping) and "env" in value:
            allowed = {"env", "required", "secret", "default"}
            unknown = set(value) - allowed
            if unknown:
                raise ConfigurationError(
                    f"Environment reference có key không hỗ trợ: {sorted(unknown)}",
                    field_path=".".join(path),
                )
            variable = value.get("env")
            if not isinstance(variable, str) or not variable.strip():
                raise ConfigurationError("Tên biến môi trường không hợp lệ", field_path=".".join(path))
            is_secret = bool(value.get("secret", False)) or _is_sensitive(path)
            if is_secret:
                secret_paths.add(path)
            if variable in environment and environment[variable] != "":
                return environment[variable]
            if "default" in value:
                return deepcopy(value["default"])
            if bool(value.get("required", False)):
                raise MissingEnvironmentVariableError(
                    f"Thiếu biến môi trường bắt buộc '{variable}'",
                    field_path=".".join(path),
                )
            return None
        if isinstance(value, Mapping):
            return {
                str(key): self._resolve_environment(
                    child, environment, secret_paths, (*path, str(key))
                )
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [
                self._resolve_environment(child, environment, secret_paths, (*path, str(index)))
                for index, child in enumerate(value)
            ]
        return deepcopy(value)

    @staticmethod
    def _validate(values: Mapping[str, Any]) -> None:
        project = values.get("project", {})
        markers = project.get("root_markers")
        if not isinstance(markers, list) or not markers or any(
            not isinstance(marker, str) or not marker.strip() for marker in markers
        ):
            raise ConfigurationError(
                "Phải là danh sách marker không rỗng", field_path="project.root_markers"
            )

        paths = project.get("paths")
        if not isinstance(paths, Mapping) or not paths:
            raise ConfigurationError("Thiếu mapping đường dẫn", field_path="project.paths")
        for name, raw_path in paths.items():
            if not isinstance(raw_path, str) or not raw_path.strip() or Path(raw_path).is_absolute():
                raise ConfigurationError(
                    "Đường dẫn project phải là chuỗi tương đối không rỗng",
                    field_path=f"project.paths.{name}",
                )

        logging_config = values.get("logging", {})
        level = logging_config.get("level")
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level not in allowed_levels:
            raise ConfigurationError(
                f"Level phải thuộc {sorted(allowed_levels)}", field_path="logging.level"
            )

        preprocessing = values.get("preprocessing", {})
        if preprocessing.get("status") == "pending_decision" and preprocessing.get("method") is not None:
            raise ConfigurationError(
                "Không được đặt method khi preprocessing còn pending",
                field_path="preprocessing.method",
            )

        connection = values.get("database", {}).get("connection", {})
        if isinstance(connection, Mapping):
            port = connection.get("port")
            if port is not None:
                try:
                    port_number = int(port)
                except (TypeError, ValueError) as exc:
                    raise ConfigurationError(
                        "Port database phải là số nguyên",
                        field_path="database.connection.port",
                    ) from exc
                if not 1 <= port_number <= 65535:
                    raise ConfigurationError(
                        "Port database phải nằm trong khoảng 1..65535",
                        field_path="database.connection.port",
                    )

            sslmode = connection.get("sslmode")
            if sslmode not in {None, "require", "verify-ca", "verify-full"}:
                raise ConfigurationError(
                    "SSL mode database không được hỗ trợ",
                    field_path="database.connection.sslmode",
                )

            channel_binding = connection.get("channel_binding")
            if channel_binding not in {None, "require", "prefer", "disable"}:
                raise ConfigurationError(
                    "Channel binding database không được hỗ trợ",
                    field_path="database.connection.channel_binding",
                )
