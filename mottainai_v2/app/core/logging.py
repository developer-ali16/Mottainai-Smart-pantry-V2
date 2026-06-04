"""
Structured logging configuration.

Outputs JSON in production for log aggregation tools (Datadog, CloudWatch).
Outputs human-readable format in development.
"""
import logging
import sys
from typing import Any, Dict

from app.core.config import settings


class _JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter — no external dependencies required."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        import traceback

        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        # Include any extra fields passed to the logger
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "message", "module",
                "msecs", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "exc_info", "exc_text",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """
    Configure the root logger and the `mottainai` application logger.
    Called once at application startup.
    """
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Choose formatter based on environment
    if settings.is_production:
        formatter = _JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure the application logger
    app_logger = logging.getLogger("mottainai")
    app_logger.setLevel(log_level)
    app_logger.handlers.clear()
    app_logger.addHandler(console_handler)
    app_logger.propagate = False

    # Quiet noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the mottainai namespace."""
    return logging.getLogger(f"mottainai.{name}")
