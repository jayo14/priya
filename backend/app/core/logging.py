"""Structured logging configuration for Priya."""

import logging
import sys


class StructuredFormatter(logging.Formatter):
    """Formats log records as structured text with standardized fields."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z")
        message = record.getMessage()
        exc = ""
        if record.exc_info:
            exc = f"\n{self.formatException(record.exc_info)}"
        return f"[{timestamp}] [{record.levelname:<7}] [{record.name}]: {message}{exc}"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root and application loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if re-called
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)

    logger = logging.getLogger("priya")
    logger.setLevel(level)
    return logger
