"""
Unit tests for travel_compose tool.

Covers the timeout recovery path: when all upstream travel tools fail/timeout
(itinerary=None, hotels=None, flights=None, etc.), travel_compose must return
an actionable recovery prompt instead of hanging or returning empty text.

Also covers partial data path: when some tools succeed and others fail,
travel_compose must compose the available data gracefully.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Environment bootstrap — must happen before any app import
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

from mcp_server.tools.travel_compose import travel_compose


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_model_service():
    """
    Patch model_service so no real OpenAI calls are made during tests.
    The early-exit path tested here never reaches the LLM, but the fixture
    prevents accidental API calls if the guard is removed.
    """
    fake_service = MagicMock()
    fake_service.generate = AsyncMock(return_value="mock response")
    fake_service.get_response = AsyncMock(return_value="mock response")
    with patch("app.services.model_service.model_service", fake_service):
        yield fake_service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_timeout_recovery(mock_model_service):
    """
    QAR-06: When all upstream travel tools fail/timeout (itinerary=None,
    hotels=None, flights=None, activities=None, cars=None), travel_compose
    must return:
    - assistant_text that is non-empty and contains actionable suggestions
    - ui_blocks that is an empty list
    - success that is True
    """
    state = {
        "user_message": "Plan a trip to Paris for 5 days",
        "intent": "travel",
        "slots": {"destination": "Paris", "duration_days": 5},
        "itinerary": None,
        "hotels": None,
        "flights": None,
        "activities": None,
        "cars": None,
        "destination_facts": None,
        "general_travel_info": None,
        "travel_results": None,
    }
    result = await travel_compose(state)

    assert result["success"] is True, f"Expected success=True, got {result.get('success')}"
    assert result["assistant_text"], "Expected non-empty assistant_text for timeout recovery"
    # The recovery prompt must contain actionable suggestions
    assistant_text = result["assistant_text"].lower()
    assert any(
        phrase in assistant_text
        for phrase in ["try again", "ask for", "specific", "hotels", "itinerary", "issue"]
    ), (
        f"Expected actionable recovery suggestions in assistant_text, got: {result['assistant_text']}"
    )
    assert result["ui_blocks"] == [], (
        f"Expected empty ui_blocks when all data missing, got: {result['ui_blocks']}"
    )


@pytest.mark.asyncio
async def test_partial_response(mock_model_service):
    """
    QAR-17: When only hotels has data but itinerary and flights are None,
    travel_compose must return a partial response that includes hotel information
    and does not crash.
    """
    state = {
        "user_message": "Find me hotels in Rome",
        "intent": "travel",
        "slots": {"destination": "Rome", "duration_days": 3},
        "itinerary": None,
        "hotels": [
            {
                "type": "plp_link",
                "provider": "expedia",
                "destination": "Rome",
                "search_url": "https://expedia.com/hotels?destination=Rome",
                "title": "Hotels in Rome",
            }
        ],
        "flights": None,
        "activities": None,
        "cars": None,
        "destination_facts": None,
        "general_travel_info": None,
        "travel_results": None,
    }
    result = await travel_compose(state)

    assert result["success"] is True, f"Expected success=True, got {result.get('success')}"
    assert result["assistant_text"], "Expected non-empty assistant_text for partial data"
    # Should include some hotel-related content in blocks
    hotel_blocks = [b for b in result["ui_blocks"] if b.get("type") == "hotels"]
    assert len(hotel_blocks) >= 1, (
        f"Expected at least one hotels UI block when hotel data is present, "
        f"got block types: {[b.get('type') for b in result['ui_blocks']]}"
    )
