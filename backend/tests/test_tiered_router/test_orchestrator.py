# backend/tests/test_tiered_router/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from app.services.tiered_router.orchestrator import TieredAPIOrchestrator


@pytest.fixture
def orchestrator():
    return TieredAPIOrchestrator()


@pytest.fixture
def mock_state():
    return {
        "user_id": "test-user",
        "session_id": "test-session",
        "user_message": "best vacuum cleaner",
        "requested_products": [],
        "user_extended_search_enabled": False,
        "extended_search_confirmed": False,
    }


@pytest.mark.asyncio
async def test_execute_returns_success_when_sufficient(orchestrator, mock_state):
    """Should return success when Tier 1 results meet threshold"""
    with patch.object(orchestrator.fetcher, "fetch_tier", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {
            "amazon": {"status": "success", "data": {"products": [
                {"name": "p1"}, {"name": "p2"}, {"name": "p3"}
            ]}},
        }

        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "success"
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_execute_escalates_when_insufficient(orchestrator, mock_state):
    """Should escalate to Tier 2 when Tier 1 is insufficient"""
    call_count = 0

    async def mock_fetch(apis, query, state):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Tier 1 - insufficient
            return {"amazon": {"status": "success", "data": {"products": [{"name": "p1"}]}}}
        else:
            # Tier 2 - add more products
            return {"bing": {"status": "success", "data": {"products": [
                {"name": "p2"}, {"name": "p3"}, {"name": "p4"}
            ]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=mock_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "success"
    assert call_count == 2  # Called for Tier 1 and Tier 2


@pytest.mark.asyncio
async def test_execute_requires_consent_for_tier_3(orchestrator, mock_state):
    """Should return consent_required when Tier 3 is needed"""
    async def insufficient_fetch(apis, query, state):
        return {"api": {"status": "success", "data": {"products": [{"name": "p1"}]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=insufficient_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    assert result["status"] == "consent_required"
    assert result["consent_prompt"]["type"] == "account_toggle"


@pytest.mark.asyncio
async def test_execute_with_consent_proceeds_to_tier_3(orchestrator):
    """Should proceed to Tier 3 when consent is given"""
    mock_state = {
        "user_id": "test-user",
        "session_id": "test-session",
        "requested_products": [],
        "user_extended_search_enabled": True,
        "extended_search_confirmed": True,
    }

    tier_calls = []

    async def track_fetch(apis, query, state):
        tier_calls.append(apis)
        if "reddit_api" in apis:
            return {"reddit_api": {"status": "success", "data": {"products": [
                {"name": "p1"}, {"name": "p2"}, {"name": "p3"}
            ]}}}
        return {"api": {"status": "success", "data": {"products": [{"name": "x"}]}}}

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=track_fetch):
        with patch("app.services.tiered_router.orchestrator.log_consent_event", new_callable=AsyncMock):
            # Mock the settings to enable reddit_api
            with patch("app.services.tiered_router.orchestrator.settings") as mock_settings:
                mock_settings.MAX_AUTO_TIER = 2
                mock_settings.ENABLE_REDDIT_API = True
                mock_settings.ENABLE_YOUTUBE_TRANSCRIPTS = True
                result = await orchestrator.execute("product", "best vacuum", mock_state)

    # Should have called Tier 1, 2, and 3
    assert any("reddit_api" in apis for apis in tier_calls)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_execute_deduplicates_items(orchestrator, mock_state):
    """Should deduplicate items across tiers"""
    async def mock_fetch(apis, query, state):
        return {
            "amazon": {"status": "success", "data": {"products": [
                {"name": "Dyson V15", "price": 599},
                {"name": "Shark Navigator", "price": 299},
            ]}},
            "walmart": {"status": "success", "data": {"products": [
                {"name": "Dyson V15", "price": 599},  # Duplicate
                {"name": "Bissell Pet", "price": 199},
            ]}},
        }

    with patch.object(orchestrator.fetcher, "fetch_tier", side_effect=mock_fetch):
        result = await orchestrator.execute("product", "best vacuum", mock_state)

    # Should have 3 unique items, not 4
    assert len(result["items"]) == 3
