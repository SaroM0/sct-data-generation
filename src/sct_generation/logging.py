"""Logging configuration."""

import logging
import sys
from typing import Optional

from .config import settings


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to settings.log_level.
        format_string: Custom format string for log messages.
    """
    log_level = level or settings.log_level

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=format_string,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Set specific loggers
    logger = logging.getLogger("sct_generation")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from external libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger, typically __name__.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
