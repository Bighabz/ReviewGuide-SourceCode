"""Tests for speculative search execution in fast_router."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


class TestSpeculativeSearch:
    @pytest.mark.asyncio
    async def test_speculative_search_runs_parallel_with_router(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Sony XM5"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.speculative_results is not None
            assert result.speculative_results["product_names"] == ["Sony XM5"]
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_speculative_results_discarded_for_travel(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Fake"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("plan a trip to Tokyo", [], None, {})
            assert result.intent == "travel"
            assert result.speculative_results is None

    @pytest.mark.asyncio
    async def test_speculative_results_discarded_for_intro(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Fake"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("hello", [], None, {})
            assert result.intent == "intro"
            assert result.speculative_results is None

    @pytest.mark.asyncio
    async def test_speculative_search_failure_doesnt_block(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(side_effect=Exception("Search API down"))
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.intent == "product"
            assert result.speculative_results is None

    @pytest.mark.asyncio
    async def test_speculative_search_timeout(self):
        from app.services.fast_router import fast_router_with_speculation

        async def slow_search(*args, **kwargs):
            await asyncio.sleep(15)
            return {"product_names": [], "success": False}

        with patch("app.services.fast_router.run_speculative_search", slow_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.intent == "product"
            assert result.speculative_results is None

    @pytest.mark.asyncio
    async def test_speculative_results_kept_for_comparison(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Sony XM5", "Bose QC"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("sony xm5 vs bose qc ultra", [], None, {})
            assert result.intent == "comparison"
            assert result.speculative_results is not None

    @pytest.mark.asyncio
    async def test_speculative_results_kept_for_service(self):
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["NordVPN"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("best vpn service", [], None, {})
            assert result.intent == "service"
            assert result.speculative_results is not None
