# backend/app/services/tiered_router/parallel_fetcher.py
"""Parallel Fetcher - Concurrent API calls with circuit breaker."""

import asyncio
import time
import logging
from typing import Optional

from app.core.config import settings
from app.services.tiered_router.api_registry import API_REGISTRY, get_api_config
from app.services.tiered_router.circuit_breaker import CircuitBreaker, get_circuit_breaker
from app.services.tiered_router.api_logger import log_api_usage

logger = logging.getLogger(__name__)


class ParallelFetcher:
    """Fetch from multiple APIs concurrently with circuit breaker protection.

    Args:
        circuit_breaker: CircuitBreaker instance (uses singleton if not provided)
    """

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self.circuit_breaker = circuit_breaker or get_circuit_breaker()

    async def fetch_tier(
        self,
        apis: list[str],
        query: str,
        state: dict,
    ) -> dict[str, dict]:
        """Fetch from all APIs in a tier concurrently.

        Args:
            apis: List of API names to fetch from
            query: Search query
            state: GraphState with user_id, session_id, etc.

        Returns:
            Dict mapping API name to result dict:
            {
                "api_name": {
                    "status": "success" | "timeout" | "error" | "circuit_open",
                    "api": "api_name",
                    "data": {...},  # If success
                    "error": "...",  # If error
                }
            }
        """
        active_apis = [api for api in apis if not self.circuit_breaker.is_open(api)]
        skipped_apis = [api for api in apis if self.circuit_breaker.is_open(api)]

        # Run all fetches in parallel
        tasks = [self._fetch_single(api, query, state) for api in active_apis]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for api, response in zip(active_apis, responses):
            if isinstance(response, Exception):
                results[api] = {"status": "error", "api": api, "error": str(response)}
            else:
                results[api] = response

        for api in skipped_apis:
            results[api] = {"status": "circuit_open", "api": api}

        return results

    async def _fetch_single(
        self,
        api_name: str,
        query: str,
        state: dict,
    ) -> dict:
        """Fetch from a single API with timeout and error handling.

        Args:
            api_name: Name of the API to fetch from
            query: Search query
            state: GraphState with user_id, session_id, etc.

        Returns:
            Result dict with status, api, and data or error
        """
        config = get_api_config(api_name)
        if not config:
            return {"status": "error", "api": api_name, "error": "Unknown API"}

        start_time = time.time()

        try:
            # Execute the MCP tool
            result = await asyncio.wait_for(
                self._execute_mcp_tool(
                    tool_name=config.mcp_tool,
                    provider=config.provider,
                    query=query,
                    state=state,
                ),
                timeout=config.timeout_ms / 1000,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_success(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=config.cost_cents,
                latency_ms=latency_ms,
                success=True,
            )

            return {"status": "success", "api": api_name, "data": result}

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=0,
                latency_ms=latency_ms,
                success=False,
                error="timeout",
            )

            logger.warning(f"API timeout: {api_name} after {latency_ms}ms")
            return {"status": "timeout", "api": api_name}

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            self.circuit_breaker.record_failure(api_name)
            await log_api_usage(
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                api_name=api_name,
                tier=state.get("current_tier", 1),
                cost_cents=0,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

            logger.error(f"API error: {api_name} - {e}")
            return {"status": "error", "api": api_name, "error": str(e)}

    async def _execute_mcp_tool(
        self,
        tool_name: str,
        provider: str,
        query: str,
        state: dict,
    ) -> dict:
        """Execute MCP tool - placeholder for integration.

        This bridges the tiered router to existing MCP tools.
        Will be wired up during workflow integration.

        Args:
            tool_name: MCP tool to execute
            provider: Provider key (amazon, walmart, etc.)
            query: Search query
            state: GraphState

        Returns:
            Tool result dict

        Raises:
            NotImplementedError: MCP tool execution not yet wired up
        """
        # TODO: Wire up to actual MCP tools during workflow integration
        raise NotImplementedError("MCP tool execution not yet wired up")
