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
    assert bundle.get("database.status") == "configured_pending_db_verification"
    assert bundle.get("database.connection.password") is None
    assert bundle.get("database.connection.sslmode") == "require"
    assert bundle.get("database.connection.channel_binding") == "require"
    assert bundle.get("preprocessing.status") == "pending_decision"
    assert bundle.get("data.cohort.filters.action_taken") == ["0", "1", "2"]
    assert bundle.get("schema.columns.action_taken.mapping_status") == (
        "VERIFIED_USER_CONFIRMED_2026_09_11"
    )
    action_rule = next(
        rule
        for rule in bundle.get("quality.rules")
        if rule["rule_id"] == "HMDA_FILTERED_004_ACTION_DOMAIN"
    )
    assert action_rule["params"]["values"] == ["0", "1", "2"]
    assert len(bundle.config_hash()) == 64


def test_local_env_is_loaded_and_process_environment_has_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_configs(tmp_path)
    (tmp_path / "local.env").write_text(
        "TEST_SECRET=file-secret\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TEST_SECRET", raising=False)

    from_file = _loader(tmp_path).load()
    assert from_file.get("project.secret_value") == "file-secret"
    assert from_file.redacted()["project"]["secret_value"] == REDACTED
    assert "file-secret" not in from_file.canonical_json()

    monkeypatch.setenv("TEST_SECRET", "process-secret")
    from_process = _loader(tmp_path).load()
    assert from_process.get("project.secret_value") == "process-secret"
    assert "process-secret" not in from_process.canonical_json()


def test_explicit_environment_does_not_read_local_env(tmp_path: Path) -> None:
    _write_configs(tmp_path)
    (tmp_path / "local.env").write_text(
        "TEST_SECRET=file-secret\n",
        encoding="utf-8",
    )

    with pytest.raises(MissingEnvironmentVariableError, match="TEST_SECRET"):
        _loader(tmp_path).load(environment={})


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("port", "not-a-port", "Port database"),
        ("sslmode", "disable", "SSL mode database"),
        ("channel_binding", "unknown", "Channel binding database"),
    ],
)
def test_invalid_database_connection_options_fail(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    files = dict(MINIMAL_FILES)
    files["database.yaml"] = f"""
connection:
  {field}: {value}
"""
    _write_configs(tmp_path, files)
    loader = ConfigLoader(
        ProjectPaths.discover(),
        config_dir=tmp_path,
        filenames=("project.yaml", "logging.yaml", "preprocessing.yaml", "database.yaml"),
    )

    with pytest.raises(ConfigurationError, match=message):
        loader.load(environment={"TEST_SECRET": "fixture-secret"})


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
