"""
Base Tool Class
Provides common functionality for all tools including error handling and logging
"""
from app.core.centralized_logger import get_logger
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from app.core.colored_logging import get_colored_logger
from app.core.error_manager import log_and_raise_tool_error

logger = get_logger(__name__)


class BaseTool(ABC):
    """
    Base class for all tools with standardized error handling and logging

    Features:
    - Standardized error handling and logging
    - Common patterns for tool execution
    """

    def __init__(self, tool_name: str):
        """
        Initialize base tool

        Args:
            tool_name: Name of the tool (for logging and error tracking)
        """
        self.tool_name = tool_name
        self.logger = get_logger(f"tool.{tool_name}")
        self.colored_logger = get_colored_logger(f"tool.{tool_name}")

    def handle_error(
        self,
        error: Exception,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[dict] = None
    ):
        """
        Standardized error handling for tools - logs and raises ToolError

        Args:
            error: Original exception
            message: Human-readable error message
            session_id: Session ID for tracking
            context: Additional context about the error
        """
        log_and_raise_tool_error(
            logger=self.logger,
            source=self.tool_name,
            message=message,
            original_error=error,
            session_id=session_id,
            extra_context=context
        )

    def log_input(self, **kwargs):
        """Log tool input for debugging"""
        self.colored_logger.agent_data(kwargs, label=f"{self.tool_name} INPUT")

    def log_output(self, output: Any):
        """Log tool output for debugging"""
        self.colored_logger.agent_data(output, label=f"{self.tool_name} OUTPUT")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Main tool logic - must be implemented by subclasses

        Returns:
            Tool execution result
        """
        pass
