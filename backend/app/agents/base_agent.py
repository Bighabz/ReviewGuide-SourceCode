"""
Base Agent Class
Provides common functionality for all agents including error handling and model service integration
"""
from app.core.centralized_logger import get_logger
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from app.services.model_service import model_service
from app.core.colored_logging import get_colored_logger
from app.core.config import settings
from app.core.error_manager import log_and_raise_agent_error

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents with standardized error handling and model service access

    Features:
    - Standardized error handling and logging
    - Model service integration (decoupled from OpenAI)
    - Common patterns for LLM calls
    - Retry logic
    """

    def __init__(self, agent_name: str, on_chain_start_message: Optional[str] = None):
        """
        Initialize base agent

        Args:
            agent_name: Name of the agent (for logging and tracing)
            on_chain_start_message: Optional status message to show when agent starts
        """
        self.agent_name = agent_name
        self.on_chain_start_message = on_chain_start_message
        self.logger = get_logger(f"agent.{agent_name}")
        self.colored_logger = get_colored_logger(f"agent.{agent_name}")
        self.settings = settings

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate completion using model service with error handling

        Args:
            messages: List of message dicts
            model: Model identifier (defaults to settings.DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Response format (e.g., {"type": "json_object"})
            session_id: Session ID for tracking
            max_retries: Maximum retry attempts

        Returns:
            Generated text

        Raises:
            AgentError: If generation fails after retries
        """
        try:
            # Use DEFAULT_MODEL from settings if model not specified
            if model is None:
                model = self.settings.DEFAULT_MODEL

            return await model_service.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                agent_name=self.agent_name,
                session_id=session_id,
            )
        except Exception as e:
            error_msg = f"Model generation failed: {str(e)}"
            log_and_raise_agent_error(
                logger=self.logger,
                source=self.agent_name,
                message=error_msg,
                original_error=e,
                session_id=session_id,
                extra_context={"operation": "generate", "model": model}
            )

    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Standardized error handling

        Args:
            error: Exception that occurred
            context: Additional context about where error occurred

        Returns:
            Error response dict
        """
        error_type = type(error).__name__
        error_msg = str(error)

        self.colored_logger.error(
            f"Error in {self.agent_name}" + (f" ({context})" if context else ""),
            exc_info=True
        )

        return {
            "error": True,
            "error_type": error_type,
            "error_message": error_msg,
            "agent": self.agent_name,
            "context": context
        }

    def log_input(self, **kwargs):
        """Log agent input for debugging in GREEN"""
        self.colored_logger.agent_data(kwargs, label=f"{self.agent_name} INPUT")

    def log_output(self, output: Any):
        """Log agent output for debugging in GREEN"""
        self.colored_logger.agent_data(output, label=f"{self.agent_name} OUTPUT")

    @abstractmethod
    async def run(self, state: Any) -> Any:
        """
        Main agent logic - must be implemented by subclasses

        Args:
            state: Current graph state

        Returns:
            Updated state or agent output
        """
        pass
