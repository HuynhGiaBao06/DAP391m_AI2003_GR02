"""Cấu hình logging tập trung, idempotent và có redaction."""

from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping, MutableMapping, TextIO

from hmda.core.exceptions import ConfigurationError


DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "run=%(run_id)s | snapshot=%(snapshot_id)s | %(message)s"
)
DEFAULT_CONTEXT_FIELDS = ("run_id", "snapshot_id", "pipeline", "step")
_MANAGED_HANDLER_ATTRIBUTE = "_hmda_managed_handler"


class ContextDefaultsFilter(logging.Filter):
    """Bổ sung giá trị mặc định để formatter không lỗi khi thiếu context."""

    def __init__(self, fields: Iterable[str] = DEFAULT_CONTEXT_FIELDS) -> None:
        super().__init__()
        self.fields = tuple(fields)

    def filter(self, record: logging.LogRecord) -> bool:
        for field in self.fields:
            if not hasattr(record, field):
                setattr(record, field, "-")
        return True


class RedactingFormatter(logging.Formatter):
    """Che các giá trị secret trong cả message và traceback đã format."""

    def __init__(self, fmt: str, *, secret_values: Iterable[str] = ()) -> None:
        super().__init__(fmt)
        self.secret_values = tuple(
            sorted(
                {str(value) for value in secret_values if value not in (None, "")},
                key=len,
                reverse=True,
            )
        )

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        for secret in self.secret_values:
            rendered = rendered.replace(secret, "***REDACTED***")
        return rendered


class RunContextAdapter(logging.LoggerAdapter):
    """Gắn context có cấu trúc mà không thay đổi message của caller."""

    def process(
        self, msg: object, kwargs: MutableMapping[str, Any]
    ) -> tuple[object, MutableMapping[str, Any]]:
        supplied = kwargs.get("extra", {})
        kwargs["extra"] = {**self.extra, **supplied}
        return msg, kwargs


def _managed_handler(logger: logging.Logger) -> logging.Handler | None:
    return next(
        (
            handler
            for handler in logger.handlers
            if getattr(handler, _MANAGED_HANDLER_ATTRIBUTE, False)
        ),
        None,
    )


def configure_logging(
    config: Mapping[str, Any] | None = None,
    *,
    logger_name: str = "hmda",
    stream: TextIO | None = None,
    secret_values: Iterable[str] = (),
) -> logging.Logger:
    """Tạo hoặc cập nhật đúng một console handler do package quản lý."""

    settings = dict(config or {})
    level_name = str(settings.get("level", "INFO")).upper()
    level = logging.getLevelName(level_name)
    if not isinstance(level, int):
        raise ConfigurationError("Logging level không hợp lệ", field_path="logging.level")

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    handler = _managed_handler(logger)
    if handler is None:
        handler = logging.StreamHandler(stream)
        setattr(handler, _MANAGED_HANDLER_ATTRIBUTE, True)
        logger.addHandler(handler)
    elif stream is not None and isinstance(handler, logging.StreamHandler):
        handler.setStream(stream)

    handler.setLevel(level)
    context_fields = settings.get("context_fields", DEFAULT_CONTEXT_FIELDS)
    if not isinstance(context_fields, list | tuple) or any(
        not isinstance(field, str) or not field for field in context_fields
    ):
        raise ConfigurationError(
            "context_fields phải là danh sách chuỗi", field_path="logging.context_fields"
        )

    handler.filters.clear()
    handler.addFilter(ContextDefaultsFilter(context_fields))
    handler.setFormatter(
        RedactingFormatter(
            str(settings.get("format", DEFAULT_FORMAT)),
            secret_values=secret_values,
        )
    )
    return logger


def bind_context(logger: logging.Logger, **context: object) -> RunContextAdapter:
    """Tạo adapter chỉ giữ các context field có giá trị thật."""

    clean_context = {key: value for key, value in context.items() if value is not None}
    return RunContextAdapter(logger, clean_context)


def log_event(
    logger: logging.Logger | logging.LoggerAdapter,
    event: str,
    *,
    status: str,
    level: int = logging.INFO,
    **context: object,
) -> None:
    """Ghi sự kiện có trạng thái tường minh, không tự tạo run/snapshot ID."""

    allowed_statuses = {"STARTED", "SUCCEEDED", "FAILED"}
    normalized_status = status.upper()
    if normalized_status not in allowed_statuses:
        raise ConfigurationError(
            f"Event status phải thuộc {sorted(allowed_statuses)}",
            field_path="logging.event_status",
        )
    logger.log(
        level,
        "event=%s status=%s",
        event,
        normalized_status,
        extra={key: value for key, value in context.items() if value is not None},
    )
