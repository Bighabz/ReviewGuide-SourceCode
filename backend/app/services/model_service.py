"""
Model Service with LangChain ChatOpenAI Integration
Provides model routing and generation. All observability is handled by Langfuse CallbackHandler.
"""
from app.core.centralized_logger import get_logger
import asyncio
import hashlib
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

# Known model context window sizes (used to normalize max_tokens in cache keys)
_MODEL_DEFAULTS: dict[str, int] = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
}
_DEFAULT_MAX_TOKENS = 128000  # fallback for unknown models


class ModelService:
    """Service for LLM interactions. All observability handled by Langfuse CallbackHandler."""

    # Type annotations only — no default assignment at class level.
    # asyncio.Semaphore must not be instantiated at import time (before an
    # event loop exists).  Each instance owns its own semaphores; because
    # the application uses a single global ``model_service`` singleton the
    # concurrency limits are still effectively process-wide.
    _streaming_semaphore: asyncio.Semaphore
    _sync_semaphore: asyncio.Semaphore

    def __init__(self):
        self._llm_cache: dict = {}
        # Separate semaphores for streaming vs non-streaming to prevent
        # head-of-line blocking.  Created here (not at class level) so that
        # no Semaphore is instantiated before an event loop is running.
        self._streaming_semaphore = asyncio.Semaphore(10)   # max 10 concurrent streaming calls
        self._sync_semaphore = asyncio.Semaphore(25)        # max 25 concurrent non-streaming calls

    @property
    def _api_key_fingerprint(self) -> str:
        """Return first 8 hex chars of SHA-256 of the current API key.

        Embedding this in the cache key ensures that rotating the API key
        forces all cached ChatOpenAI instances (which hold the old key) to
        be evicted and recreated with the new credential.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
        return hashlib.sha256(api_key.encode()).hexdigest()[:8]

    @staticmethod
    def _canonical_key(
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        json_mode: bool,
        stream: bool,
        api_key_fingerprint: str,
    ) -> tuple:
        """Build a normalized cache key that avoids spurious misses.

        Normalizations applied:
        - ``max_tokens``: if the caller passes ``None`` *or* the model's own
          default context length, both collapse to ``None`` — same instance.
        - ``temperature``: rounded to one decimal place so ``0.7`` and ``0.70``
          resolve to the same bucket.
        - ``api_key_fingerprint``: invalidates the entry on key rotation.
        """
        model_default = _MODEL_DEFAULTS.get(model, _DEFAULT_MAX_TOKENS)
        effective_max = max_tokens if (max_tokens is not None and max_tokens > 0 and max_tokens < model_default) else None
        effective_temp = round(temperature, 1)
        return (model, effective_temp, effective_max, json_mode, stream, api_key_fingerprint)

    def _get_llm(
        self,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        json_mode: bool,
        stream: bool,
    ) -> ChatOpenAI:
        """Get or create a cached ChatOpenAI instance.

        Instances are cached by a canonical key (model, temperature, max_tokens,
        json_mode, stream, api_key_fingerprint) so HTTP connections are reused
        via the underlying httpx.AsyncClient.
        """
        fingerprint = self._api_key_fingerprint
        cache_key = self._canonical_key(model, temperature, max_tokens, json_mode, stream, fingerprint)
        if cache_key not in self._llm_cache:
            kwargs: dict = {
                "model": model,
                "openai_api_key": settings.OPENAI_API_KEY,
                "streaming": stream,
                "request_timeout": 12,    # Hard cap: no single LLM call waits > 12s
                "max_retries": 1,         # One retry on transient failure (12s × 2 = 24s worst case, fits 15s tool timeout on first attempt)
            }
            # o3 models don't support temperature parameter
            if not model.startswith("o3"):
                kwargs["temperature"] = temperature
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            if json_mode:
                kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            self._llm_cache[cache_key] = ChatOpenAI(**kwargs)
            logger.info(f"[model_service] Created new ChatOpenAI instance (cache size: {len(self._llm_cache)})")
        return self._llm_cache[cache_key]

    def invalidate_cache(self, reason: str = "manual") -> int:
        """Clear all cached LLM instances.

        Returns:
            Number of instances that were evicted.
        """
        count = len(self._llm_cache)
        self._llm_cache.clear()
        logger.info(f"[model_service] Cache invalidated: {count} instances cleared, reason={reason}")
        return count

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

        Streaming calls acquire ``_streaming_semaphore`` (limit 10 concurrent).
        Non-streaming calls acquire ``_sync_semaphore`` (limit 25 concurrent).

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

            # Get cached LLM instance (enables HTTP connection pooling)
            json_mode = bool(response_format and response_format.get("type") == "json_object")
            llm = self._get_llm(model, temperature, max_tokens, json_mode, stream)

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
                # Acquire the non-streaming concurrency semaphore before calling the API
                async with self._sync_semaphore:
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
        """Stream response tokens. Token/cost tracking handled by Langfuse CallbackHandler.

        Acquires ``_streaming_semaphore`` for the full duration of the stream to
        cap concurrent open HTTP/SSE connections.
        """
        async with self._streaming_semaphore:
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
