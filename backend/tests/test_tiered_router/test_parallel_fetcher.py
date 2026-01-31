# backend/tests/test_tiered_router/test_parallel_fetcher.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tiered_router.parallel_fetcher import ParallelFetcher
from app.services.tiered_router.circuit_breaker import CircuitBreaker


@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(failure_threshold=3, reset_timeout=300)


@pytest.fixture
def fetcher(circuit_breaker):
    return ParallelFetcher(circuit_breaker)


@pytest.mark.asyncio
async def test_fetch_tier_returns_results(fetcher):
    """fetch_tier should return results from all APIs"""
    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"status": "success", "api": "test", "data": {"products": []}}

        results = await fetcher.fetch_tier(["amazon_affiliate", "walmart_affiliate"], "test query", mock_state)

    assert "amazon_affiliate" in results
    assert "walmart_affiliate" in results


@pytest.mark.asyncio
async def test_fetch_tier_marks_circuit_open(fetcher, circuit_breaker):
    """fetch_tier should mark circuit-broken APIs"""
    # Open circuit for amazon
    for _ in range(3):
        circuit_breaker.record_failure("amazon_affiliate")

    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"status": "success", "api": "test", "data": {}}

        results = await fetcher.fetch_tier(["amazon_affiliate", "walmart_affiliate"], "test query", mock_state)

    assert results["amazon_affiliate"]["status"] == "circuit_open"
    assert results["walmart_affiliate"]["status"] == "success"


@pytest.mark.asyncio
async def test_fetch_tier_handles_timeout(fetcher, circuit_breaker):
    """fetch_tier should handle timeouts gracefully"""
    mock_state = {"user_id": "test", "session_id": "sess"}

    async def slow_fetch(*args, **kwargs):
        await asyncio.sleep(10)  # Longer than timeout

    with patch.object(fetcher, "_fetch_single", side_effect=asyncio.TimeoutError):
        with patch("app.services.tiered_router.parallel_fetcher.log_api_usage", new_callable=AsyncMock):
            results = await fetcher.fetch_tier(["amazon_affiliate"], "test query", mock_state)

    # Should handle the exception from gather
    assert "amazon_affiliate" in results


@pytest.mark.asyncio
async def test_fetch_tier_runs_in_parallel(fetcher):
    """fetch_tier should call APIs in parallel, not sequentially"""
    call_times = []

    async def track_call(api, query, state):
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)
        return {"status": "success", "api": api, "data": {}}

    mock_state = {"user_id": "test", "session_id": "sess"}

    with patch.object(fetcher, "_fetch_single", side_effect=track_call):
        await fetcher.fetch_tier(["api1", "api2", "api3"], "test query", mock_state)

    # If parallel, all calls should start within 0.05s of each other
    assert len(call_times) == 3
    assert max(call_times) - min(call_times) < 0.05
