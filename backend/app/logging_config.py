"""Structured logging configuration for the application.

This module configures structured JSON logging suitable for log aggregation
tools like Promtail/Loki. All logs include contextual information and are
formatted as JSON for easy parsing and filtering.
"""

import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context fields."""

    def add_fields(
        self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log records.

        Args:
            log_record: Dictionary to write log fields to
            record: Python logging record
            message_dict: Dictionary of message fields
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add process/thread info for debugging
        log_record["process_id"] = record.process
        log_record["thread_id"] = record.thread

        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)


def setup_logging(
    log_level: str = "INFO",
    uvicorn_access_log_level: str = "WARNING",
    uvicorn_error_log_level: str = "INFO",
    sqlalchemy_engine_log_level: str = "WARNING",
    apscheduler_log_level: str = "INFO",
) -> None:
    """Configure structured logging for the application.

    Sets up JSON-formatted logging to stdout, suitable for container
    environments where logs are collected by external tools like Promtail.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        uvicorn_access_log_level: Log level for uvicorn.access logger
        uvicorn_error_log_level: Log level for uvicorn.error logger
        sqlalchemy_engine_log_level: Log level for sqlalchemy.engine logger
        apscheduler_log_level: Log level for apscheduler logger
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create JSON formatter
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(logger)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add stdout handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Set levels for noisy third-party libraries (configurable via env vars)
    logging.getLogger("uvicorn.access").setLevel(
        getattr(logging, uvicorn_access_log_level.upper(), logging.WARNING)
    )
    logging.getLogger("uvicorn.error").setLevel(
        getattr(logging, uvicorn_error_log_level.upper(), logging.INFO)
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        getattr(logging, sqlalchemy_engine_log_level.upper(), logging.WARNING)
    )
    logging.getLogger("apscheduler").setLevel(
        getattr(logging, apscheduler_log_level.upper(), logging.INFO)
    )

    # Log configuration completion
    root_logger.info(
        "Structured logging configured",
        extra={"log_level": log_level, "formatter": "json", "output": "stdout"},
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
