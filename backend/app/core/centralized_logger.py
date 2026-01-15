"""
Centralized Logger Factory

This module provides a single entry point for all logging in the application.
All modules should use get_logger() to obtain their logger instance.

Usage:
    from app.core.centralized_logger import get_logger

    logger = get_logger(__name__)
    logger.info("This is a log message")
"""
import logging
from typing import Optional
from app.core.logging_config import is_logging_enabled


class CentralizedLogger(logging.Logger):
    """
    Custom logger that respects the global LOG_ENABLED flag.
    All log methods check if logging is enabled before proceeding.
    """

    def _log_if_enabled(self, level, msg, args, **kwargs):
        """Internal method that checks if logging is enabled before logging"""
        if is_logging_enabled():
            super()._log(level, msg, args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Log debug message if logging is enabled"""
        if is_logging_enabled():
            super().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log info message if logging is enabled"""
        if is_logging_enabled():
            super().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log warning message if logging is enabled"""
        if is_logging_enabled():
            super().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log error message if logging is enabled"""
        if is_logging_enabled():
            super().error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log critical message if logging is enabled"""
        if is_logging_enabled():
            super().critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Log exception if logging is enabled"""
        if is_logging_enabled():
            super().exception(msg, *args, **kwargs)


# Set the custom logger class
logging.setLoggerClass(CentralizedLogger)


def get_logger(name: Optional[str] = None) -> CentralizedLogger:
    """
    Get a centralized logger instance.

    This is the single entry point for all logging in the application.
    The logger respects the global LOG_ENABLED configuration.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        CentralizedLogger instance

    Example:
        from app.core.centralized_logger import get_logger

        logger = get_logger(__name__)
        logger.info("Application started")
        logger.error("Something went wrong", exc_info=True)
    """
    return logging.getLogger(name)


# Export public API
__all__ = ["get_logger", "CentralizedLogger"]
