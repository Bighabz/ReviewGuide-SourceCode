"""
Structured JSON Logging Configuration
Provides JSON-formatted logs for better observability
"""
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Global flag to control logging
_LOGGING_ENABLED = True


def set_logging_enabled(enabled: bool):
    """
    Globally enable or disable all logging.

    Args:
        enabled: True to enable logging, False to disable
    """
    global _LOGGING_ENABLED
    _LOGGING_ENABLED = enabled


def is_logging_enabled() -> bool:
    """Check if logging is globally enabled"""
    return _LOGGING_ENABLED


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "agent"):
            log_data["agent"] = record.agent

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add any custom fields from extra parameter
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "session_id",
                "request_id",
                "agent",
                "user_id",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    use_json: bool = True,
    use_colors: bool = True,
    enabled: bool = True,
    use_stderr: bool = False
):
    """
    Setup application logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatter (True for production)
        use_colors: Whether to use colored output (True for development)
        enabled: Whether logging is enabled globally
        use_stderr: Whether to output to stderr instead of stdout (required for MCP servers)
    """
    # Set global logging flag
    set_logging_enabled(enabled)

    # If logging is disabled, set everything to CRITICAL to suppress all logs
    if not enabled:
        logging.disable(logging.CRITICAL)
        return

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler - use stderr for MCP servers to avoid interfering with JSON-RPC
    output_stream = sys.stderr if use_stderr else sys.stdout
    console_handler = logging.StreamHandler(output_stream)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        # Use standard formatter for development with optional colors
        if use_colors:
            from app.core.colored_logging import ColoredFormatter
            formatter = ColoredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)  # Suppress LiteLLM verbose logs

    # Suppress FastAPI internal HTTP logging (http send/receive)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("starlette").setLevel(logging.WARNING)
    logging.getLogger("starlette.routing").setLevel(logging.WARNING)
    logging.getLogger("starlette.middleware").setLevel(logging.WARNING)
    logging.getLogger("starlette.responses").setLevel(logging.WARNING)
    logging.getLogger("asgi").setLevel(logging.WARNING)

    # Suppress HTTP protocol logs
    logging.getLogger("http").setLevel(logging.WARNING)
    logging.getLogger("http.client").setLevel(logging.WARNING)

    logging.info(f"Logging configured: level={log_level}, json={use_json}, enabled={enabled}")


class StructuredLogger:
    """
    Helper class for structured logging with consistent fields
    """

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def log(
        self,
        level: str,
        message: str,
        session_id: str = None,
        request_id: str = None,
        agent: str = None,
        **kwargs,
    ):
        """
        Log with structured fields

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            session_id: Optional session ID
            request_id: Optional request ID
            agent: Optional agent name
            **kwargs: Additional fields to include
        """
        extra = {}

        if session_id:
            extra["session_id"] = session_id

        if request_id:
            extra["request_id"] = request_id

        if agent:
            extra["agent"] = agent

        # Add any additional fields
        extra.update(kwargs)

        log_func = getattr(self.logger, level.lower())
        log_func(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log("debug", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.log("critical", message, **kwargs)


# Export public API
__all__ = ["JSONFormatter", "setup_logging", "StructuredLogger", "set_logging_enabled", "is_logging_enabled"]
