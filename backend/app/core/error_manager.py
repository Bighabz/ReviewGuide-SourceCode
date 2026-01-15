"""
Centralized Error Classes
Simple error classes for agents and tools
"""
from typing import Optional, Callable, Any, Dict
import logging
from functools import wraps


class BaseError(Exception):
    """Base error class for all application errors"""

    def __init__(
        self,
        source: str,  # agent name or tool name
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None
    ):
        self.source = source
        self.message = message
        self.original_error = original_error
        self.context = context or {}
        super().__init__(f"[{source}] {message}")

    def to_dict(self) -> dict:
        """Convert error to dictionary for API responses"""
        return {
            "error": self.message,
            "source": self.source,
            "context": self.context
        }


class AgentError(BaseError):
    """Error raised by agents"""
    pass


class ToolError(BaseError):
    """Error raised by tools"""
    pass


def log_and_raise_agent_error(
    logger: logging.Logger,
    source: str,
    message: str,
    original_error: Exception,
    session_id: Optional[str] = None,
    extra_context: Optional[dict] = None
):
    """
    Log error and raise AgentError in one call

    Args:
        logger: Logger instance
        source: Agent name
        message: Error message
        original_error: Original exception
        session_id: Session ID
        extra_context: Additional context
    """
    extra = {"session_id": session_id}
    if extra_context:
        extra.update(extra_context)

    logger.error(
        f"Error in {source}: {message}",
        exc_info=True,
        extra=extra
    )

    raise AgentError(
        source=source,
        message=message,
        original_error=original_error,
        context=extra_context or {}
    )


def log_and_raise_tool_error(
    logger: logging.Logger,
    source: str,
    message: str,
    original_error: Exception,
    session_id: Optional[str] = None,
    extra_context: Optional[dict] = None
):
    """
    Log error and raise ToolError in one call

    Args:
        logger: Logger instance
        source: Tool name
        message: Error message
        original_error: Original exception
        session_id: Session ID
        extra_context: Additional context
    """
    extra = {"session_id": session_id}
    if extra_context:
        extra.update(extra_context)

    logger.error(
        f"Error in {source}: {message}",
        exc_info=True,
        extra=extra
    )

    raise ToolError(
        source=source,
        message=message,
        original_error=original_error,
        context=extra_context or {}
    )


def tool_error_handler(tool_name: str, error_message: str = "Tool execution failed"):
    """
    Decorator for function-based tools to handle errors automatically

    Usage:
        @tool_error_handler(tool_name="travel_compose", error_message="Failed to format travel response")
        async def travel_compose(state: Dict[str, Any]) -> Dict[str, Any]:
            # tool code here
            pass

    Args:
        tool_name: Name of the tool (for logging)
        error_message: Error message to log
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            from app.core.centralized_logger import get_logger
            logger = get_logger(tool_name)

            try:
                return await func(state)
            except Exception as e:
                log_and_raise_tool_error(
                    logger=logger,
                    source=tool_name,
                    message=error_message,
                    original_error=e,
                    session_id=state.get("session_id"),
                    extra_context={"state_keys": list(state.keys())}
                )
        return wrapper
    return decorator
