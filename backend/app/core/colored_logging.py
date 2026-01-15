"""
Colored logging utilities for the Travel application.

This module provides colored logging functionality:
- Agent titles and data: GREEN
- API inputs/outputs: YELLOW
- Errors: RED
- Info: DEFAULT
"""

import logging
from typing import Any, Dict, Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)


class ColorCodes:
    """ANSI color codes for terminal output."""
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
    DIM = Style.DIM


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages based on level and context."""

    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with appropriate colors."""
        # Store original format
        original_format = self._style._fmt

        # Get color based on level
        level_color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)

        # Colorize level name
        record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"

        # Format the message
        result = super().format(record)

        # Restore original format
        self._style._fmt = original_format

        return result


class ColoredLogger:
    """Wrapper class for colored logging with specific color schemes."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _format_dict(self, data: Dict[str, Any], indent: int = None) -> str:
        """Format dictionary for pretty printing."""
        import json
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(data)

    def agent_title(self, title: str, agent_name: Optional[str] = None, **kwargs):
        """Log agent title in GREEN."""
        if agent_name:
            message = f"{ColorCodes.GREEN}{ColorCodes.BOLD}[AGENT: {agent_name}] {title}{ColorCodes.RESET}"
        else:
            message = f"{ColorCodes.GREEN}{ColorCodes.BOLD}{title}{ColorCodes.RESET}"

        extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
        if extra_data:
            message += f" {ColorCodes.GREEN}{extra_data}{ColorCodes.RESET}"

        self.logger.info(message)

    def agent_data(self, data: Any, label: Optional[str] = None, **kwargs):
        """Log agent data in GREEN."""
        message_parts = []

        if label:
            message_parts.append(f"{ColorCodes.GREEN}{ColorCodes.BOLD}{label}:{ColorCodes.RESET}")

        if isinstance(data, dict):
            formatted_data = self._format_dict(data)
            message_parts.append(f"{ColorCodes.GREEN}{formatted_data}{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.GREEN}{data}{ColorCodes.RESET}")

        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message_parts.append(f"{ColorCodes.GREEN}{extra}{ColorCodes.RESET}")

        self.logger.info(" ".join(message_parts))

    def api_input(self, data: Any, endpoint: Optional[str] = None, **kwargs):
        """Log API input in YELLOW."""
        message_parts = []

        if endpoint:
            message_parts.append(f"{ColorCodes.YELLOW}{ColorCodes.BOLD}[API INPUT: {endpoint}]{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.YELLOW}{ColorCodes.BOLD}[API INPUT]{ColorCodes.RESET}")

        if isinstance(data, dict):
            formatted_data = self._format_dict(data)
            message_parts.append(f"{ColorCodes.YELLOW}{formatted_data}{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.YELLOW}{data}{ColorCodes.RESET}")

        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message_parts.append(f"{ColorCodes.YELLOW}{extra}{ColorCodes.RESET}")

        self.logger.info(" ".join(message_parts))

    def api_output(self, data: Any, endpoint: Optional[str] = None, **kwargs):
        """Log API output in YELLOW."""
        message_parts = []

        if endpoint:
            message_parts.append(f"{ColorCodes.YELLOW}{ColorCodes.BOLD}[API OUTPUT: {endpoint}]{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.YELLOW}{ColorCodes.BOLD}[API OUTPUT]{ColorCodes.RESET}")

        if isinstance(data, dict):
            formatted_data = self._format_dict(data)
            message_parts.append(f"{ColorCodes.YELLOW}{formatted_data}{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.YELLOW}{data}{ColorCodes.RESET}")

        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message_parts.append(f"{ColorCodes.YELLOW}{extra}{ColorCodes.RESET}")

        self.logger.info(" ".join(message_parts))

    def error(self, message: str, **kwargs):
        """Log error in RED."""
        full_message = f"{ColorCodes.RED}{ColorCodes.BOLD}[ERROR] {message}{ColorCodes.RESET}"
        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message += f" {ColorCodes.RED}{extra}{ColorCodes.RESET}"

        self.logger.error(full_message, exc_info=kwargs.get('exc_info', False))

    def info(self, message: str, **kwargs):
        """Log info message."""
        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message += f" | {extra}"

        self.logger.info(message)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message += f" | {extra}"

        self.logger.debug(message)

    def warning(self, message: str, **kwargs):
        """Log warning message in YELLOW."""
        full_message = f"{ColorCodes.YELLOW}[WARNING] {message}{ColorCodes.RESET}"
        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message += f" {ColorCodes.YELLOW}{extra}{ColorCodes.RESET}"

        self.logger.warning(full_message)

    def tool_call(self, tool_name: str, data: Any, **kwargs):
        """Log tool call in BLUE."""
        message_parts = []

        message_parts.append(f"{ColorCodes.BLUE}{ColorCodes.BOLD}[TOOL CALL: {tool_name}]{ColorCodes.RESET}")

        if isinstance(data, dict):
            formatted_data = self._format_dict(data)
            message_parts.append(f"{ColorCodes.BLUE}{formatted_data}{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.BLUE}{data}{ColorCodes.RESET}")

        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message_parts.append(f"{ColorCodes.BLUE}{extra}{ColorCodes.RESET}")

        self.logger.info(" ".join(message_parts))

    def tool_result(self, tool_name: str, data: Any, **kwargs):
        """Log tool result in BLUE."""
        message_parts = []

        message_parts.append(f"{ColorCodes.BLUE}{ColorCodes.BOLD}[TOOL RESULT: {tool_name}]{ColorCodes.RESET}")

        if isinstance(data, dict):
            formatted_data = self._format_dict(data)
            message_parts.append(f"{ColorCodes.BLUE}{formatted_data}{ColorCodes.RESET}")
        else:
            message_parts.append(f"{ColorCodes.BLUE}{data}{ColorCodes.RESET}")

        if kwargs:
            extra = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message_parts.append(f"{ColorCodes.BLUE}{extra}{ColorCodes.RESET}")

        self.logger.info(" ".join(message_parts))


def get_colored_logger(name: str) -> ColoredLogger:
    """
    Get a colored logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        ColoredLogger instance
    """
    logger = logging.getLogger(name)
    return ColoredLogger(logger)


# Convenience function for quick colored logging
def log_agent(logger_name: str, title: str, data: Optional[Any] = None, **kwargs):
    """Quick function to log agent title and optional data in GREEN."""
    logger = get_colored_logger(logger_name)
    logger.agent_title(title, **kwargs)
    if data is not None:
        logger.agent_data(data)


def log_api(logger_name: str, input_data: Optional[Any] = None, output_data: Optional[Any] = None, endpoint: Optional[str] = None):
    """Quick function to log API input/output in YELLOW."""
    logger = get_colored_logger(logger_name)
    if input_data is not None:
        logger.api_input(input_data, endpoint=endpoint)
    if output_data is not None:
        logger.api_output(output_data, endpoint=endpoint)
