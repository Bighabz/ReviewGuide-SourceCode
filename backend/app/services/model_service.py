"""
Model Service with LangChain ChatOpenAI Integration
Provides model routing and generation. All observability is handled by Langfuse CallbackHandler.
"""
from app.core.centralized_logger import get_logger
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.core.config import settings
from app.core.colored_logging import get_colored_logger

logger = get_logger(__name__)
colored_logger = get_colored_logger(__name__)


class ModelService:
    """Service for LLM interactions. All observability handled by Langfuse CallbackHandler."""

    def __init__(self):
        pass

    def _convert_messages(self, messages: list[Dict[str, str]]):
        """Convert dict messages to LangChain message objects"""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:  # user or any other role
                converted.append(HumanMessage(content=content))

        return converted

    async def generate(
            self,
            messages: list[Dict[str, str]],
            model: str = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            stream: bool = False,
            agent_name: Optional[str] = None,
            session_id: Optional[str] = None,
            response_format: Optional[Dict[str, str]] = None,
            callbacks: Optional[list] = None,
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate completion with unified Langfuse tracing via callbacks.

        Langfuse tracing is handled automatically via the callbacks parameter.
        The langfuse_handler from chat.py is passed through LangGraph context,
        ensuring all LLM calls (from agents and tools) are traced in a single unified trace.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to settings.DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            agent_name: Name of the calling agent (for tracking)
            session_id: Session ID (for tracking)
            response_format: Response format (e.g., {"type": "json_object"})
            callbacks: LangChain callbacks (contains langfuse_handler for unified tracing)

        Returns:
            Generated text or async generator for streaming
        """
        try:
            # Use DEFAULT_MODEL from settings if model not specified
            if model is None:
                model = settings.DEFAULT_MODEL

            # Convert messages to LangChain format
            lc_messages = self._convert_messages(messages)

            # Build ChatOpenAI kwargs
            llm_kwargs = {
                "model": model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "streaming": stream,
            }

            # o3 models don't support temperature parameter
            if not model.startswith("o3"):
                llm_kwargs["temperature"] = temperature

            if max_tokens:
                llm_kwargs["max_tokens"] = max_tokens

            # Handle JSON mode
            if response_format and response_format.get("type") == "json_object":
                llm_kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

            # Create LLM instance
            llm = ChatOpenAI(**llm_kwargs)

            # Log API input (YELLOW)
            colored_logger.api_input(
                {
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "messages": [{"role": m.type, "content": m.content[:100] + "..." if len(m.content) > 100 else m.content} for m in lc_messages]
                },
                endpoint=f"OpenAI Chat ({model})",
                agent=agent_name or "unknown"
            )

            # Langfuse tracing is now handled automatically via callbacks
            # No need to manually create Langfuse client since we're in the same process
            # The langfuse_handler from chat.py will capture all LLM calls via callbacks
            logger.debug(f"[model_service] {agent_name or 'unknown'}: callbacks={len(callbacks) if callbacks else 0}")

            if stream:
                return self._stream_response(
                    llm, lc_messages, model, agent_name, session_id
                )
            else:
                # Make API call with callbacks (langfuse_handler will capture automatically)
                if callbacks:
                    response = await llm.ainvoke(lc_messages, config={"callbacks": callbacks})
                else:
                    # If no callbacks provided, call without config (will still be traced if in LangGraph context)
                    response = await llm.ainvoke(lc_messages)

                # Extract content
                content = response.content

                # Log API output (YELLOW) - token/cost details available in Langfuse
                colored_logger.api_output(
                    {
                        "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    },
                    endpoint=f"OpenAI Chat ({model})",
                    agent=agent_name or "unknown"
                )

                # Structured JSON logging
                logger.info(
                    json.dumps({
                        "event": "model_call",
                        "agent": agent_name or "unknown",
                        "model": model,
                        "session_id": session_id,
                    })
                )

                return content

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "model_error",
                    "agent": agent_name or "unknown",
                    "model": model,
                    "error": str(e),
                    "session_id": session_id,
                })
            )
            raise

    async def _stream_response(
            self,
            llm: ChatOpenAI,
            messages,
            model: str,
            agent_name: Optional[str] = None,
            session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens. Token/cost tracking handled by Langfuse CallbackHandler."""
        try:
            # Langfuse CallbackHandler is inherited from LangGraph context automatically
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield chunk.content

            logger.info(
                json.dumps({
                    "event": "model_stream_complete",
                    "agent": agent_name or "unknown",
                    "model": model,
                    "session_id": session_id,
                })
            )

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "streaming_error",
                    "agent": agent_name or "unknown",
                    "model": model,
                    "error": str(e),
                    "session_id": session_id,
                })
            )
            raise


# Global instance
model_service = ModelService()