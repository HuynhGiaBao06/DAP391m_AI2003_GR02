from pathlib import Path

import pytest

from hmda.core.config import ConfigLoader, REDACTED
from hmda.core.exceptions import ConfigurationError, MissingEnvironmentVariableError
from hmda.core.path import ProjectPaths


MINIMAL_FILES = {
    "project.yaml": """
name: test-project
root_markers: [pyproject.toml, src/hmda]
paths:
  data: data
secret_value:
  env: TEST_SECRET
  required: true
  secret: true
""",
    "logging.yaml": """
level: INFO
format: '%(message)s'
context_fields: [run_id]
""",
    "preprocessing.yaml": """
status: pending_decision
method: null
""",
}


def _write_configs(directory: Path, files: dict[str, str] | None = None) -> None:
    for filename, content in (files or MINIMAL_FILES).items():
        (directory / filename).write_text(content.strip() + "\n", encoding="utf-8")


def _loader(directory: Path) -> ConfigLoader:
    return ConfigLoader(
        ProjectPaths.discover(),
        config_dir=directory,
        filenames=("project.yaml", "logging.yaml", "preprocessing.yaml"),
    )


def test_repository_configs_load_without_real_database_credentials() -> None:
    bundle = ConfigLoader().load(environment={})

    assert bundle.get("project.name") == "hmda-project"
    assert bundle.get("database.status") == "pending_connection"
    assert bundle.get("database.connection.password") is None
    assert bundle.get("preprocessing.status") == "pending_decision"
    assert len(bundle.config_hash()) == 64


def test_secret_is_resolved_but_redacted_from_serialized_evidence(tmp_path: Path) -> None:
    _write_configs(tmp_path)

    bundle = _loader(tmp_path).load(environment={"TEST_SECRET": "fixture-secret"})

    assert bundle.get("project.secret_value") == "fixture-secret"
    assert bundle.redacted()["project"]["secret_value"] == REDACTED
    assert "fixture-secret" not in bundle.canonical_json()
    assert bundle.secret_values() == ("fixture-secret",)


def test_missing_required_environment_variable_fails_without_secret_value(tmp_path: Path) -> None:
    _write_configs(tmp_path)

    with pytest.raises(MissingEnvironmentVariableError, match="TEST_SECRET"):
        _loader(tmp_path).load(environment={})


def test_override_only_updates_existing_path(tmp_path: Path) -> None:
    _write_configs(tmp_path)
    loader = _loader(tmp_path)

    bundle = loader.load(
        environment={"TEST_SECRET": "fixture-secret"},
        overrides={"logging.level": "DEBUG"},
    )
    assert bundle.get("logging.level") == "DEBUG"

    with pytest.raises(ConfigurationError, match="Override path không tồn tại"):
        loader.load(
            environment={"TEST_SECRET": "fixture-secret"},
            overrides={"logging.unknown": True},
        )


def test_pending_preprocessing_cannot_hide_a_method(tmp_path: Path) -> None:
    files = dict(MINIMAL_FILES)
    files["preprocessing.yaml"] = "status: pending_decision\nmethod: median"
    _write_configs(tmp_path, files)

    with pytest.raises(ConfigurationError, match="preprocessing.method"):
        _loader(tmp_path).load(environment={"TEST_SECRET": "fixture-secret"})


def test_missing_required_config_file_fails(tmp_path: Path) -> None:
    _write_configs(tmp_path, {"project.yaml": MINIMAL_FILES["project.yaml"]})

    with pytest.raises(ConfigurationError, match="logging.yaml"):
        _loader(tmp_path).load(environment={"TEST_SECRET": "fixture-secret"})


def test_invalid_yaml_is_chained_without_exposing_file_system_path(tmp_path: Path) -> None:
    files = dict(MINIMAL_FILES)
    files["logging.yaml"] = "level: ["
    _write_configs(tmp_path, files)

    with pytest.raises(ConfigurationError, match="logging.yaml") as captured:
        _loader(tmp_path).load(environment={"TEST_SECRET": "fixture-secret"})

    assert captured.value.__cause__ is not None
    assert str(tmp_path) not in str(captured.value)


def test_absolute_project_path_is_rejected(tmp_path: Path) -> None:
    files = dict(MINIMAL_FILES)
    files["project.yaml"] = f"""
name: test-project
root_markers: [pyproject.toml, src/hmda]
paths:
  data: '{tmp_path.as_posix()}'
secret_value:
  env: TEST_SECRET
  required: true
  secret: true
"""
    _write_configs(tmp_path, files)

    with pytest.raises(ConfigurationError, match="project.paths.data"):
        _loader(tmp_path).load(environment={"TEST_SECRET": "fixture-secret"})
