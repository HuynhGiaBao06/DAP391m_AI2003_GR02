from io import StringIO
import logging

import pytest

from hmda.core.exceptions import ConfigurationError
from hmda.core.logging_config import bind_context, configure_logging, log_event


def _clean_logger(name: str) -> None:
    logger = logging.getLogger(name)
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def test_configure_logging_is_idempotent() -> None:
    name = "hmda.tests.idempotent"
    stream = StringIO()
    try:
        first = configure_logging({"level": "INFO"}, logger_name=name, stream=stream)
        second = configure_logging({"level": "DEBUG"}, logger_name=name, stream=stream)

        assert first is second
        assert len(first.handlers) == 1
        assert first.level == logging.DEBUG
    finally:
        _clean_logger(name)


def test_context_is_included_and_missing_fields_are_safe() -> None:
    name = "hmda.tests.context"
    stream = StringIO()
    config = {
        "level": "INFO",
        "format": "%(levelname)s|%(run_id)s|%(snapshot_id)s|%(message)s",
        "context_fields": ["run_id", "snapshot_id"],
    }
    try:
        logger = configure_logging(config, logger_name=name, stream=stream)
        bind_context(logger, run_id="run-fixture").info("started")

        assert "INFO|run-fixture|-|started" in stream.getvalue()
    finally:
        _clean_logger(name)


def test_secret_is_redacted_from_message_and_exception() -> None:
    name = "hmda.tests.redaction"
    stream = StringIO()
    secret = "fixture-password"
    try:
        logger = configure_logging(
            {"level": "ERROR", "format": "%(message)s"},
            logger_name=name,
            stream=stream,
            secret_values=(secret,),
        )
        try:
            raise RuntimeError(f"connection failed for {secret}")
        except RuntimeError:
            logger.exception("cannot connect using %s", secret)

        rendered = stream.getvalue()
        assert secret not in rendered
        assert rendered.count("***REDACTED***") >= 2
    finally:
        _clean_logger(name)


def test_invalid_logging_level_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="logging.level"):
        configure_logging({"level": "VERBOSE"}, logger_name="hmda.tests.invalid")


def test_log_event_requires_explicit_status_and_does_not_invent_run_id() -> None:
    name = "hmda.tests.event"
    stream = StringIO()
    try:
        logger = configure_logging(
            {"level": "INFO", "format": "%(run_id)s|%(message)s"},
            logger_name=name,
            stream=stream,
        )
        log_event(logger, "config_loaded", status="SUCCEEDED")

        assert "-|event=config_loaded status=SUCCEEDED" in stream.getvalue()
        with pytest.raises(ConfigurationError, match="logging.event_status"):
            log_event(logger, "config_loaded", status="DONE")
    finally:
        _clean_logger(name)
