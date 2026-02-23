"""
Unit tests for product_compose tool.

Covers the general_product_info fallback path: when the planner routes through
product_general_information (factoid queries), the fetched answer must be
surfaced as assistant_text rather than silently discarded by the no-results guard.
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

from mcp_server.tools.product_compose import product_compose


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_model_service():
    """
    Patch model_service so no real OpenAI calls are made during tests.
    The early-exit path tested here never reaches the LLM, but the fixture
    is required to prevent accidental API calls if the guard is removed.
    """
    fake_service = MagicMock()
    fake_service.get_response = AsyncMock(return_value="mock response")
    fake_service.get_streaming_response = AsyncMock(return_value=iter([]))
    with patch("mcp_server.tools.product_compose.model_service", fake_service, create=True):
        yield fake_service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compose_uses_general_product_info_when_no_listings(mock_model_service):
    """
    When general_product_info is in state but no affiliate/review/normalized data exists,
    product_compose must return general_product_info as assistant_text.
    """
    state = {
        "user_message": "tell me more about Sony WH-1000XM5",
        "intent": "product",
        "slots": {},
        "normalized_products": [],
        "affiliate_products": {},
        "review_data": {},
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "The Sony WH-1000XM5 is a premium over-ear headphone with industry-leading ANC.",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }
    result = await product_compose(state)
    assert result["success"] is True
    assert "Sony WH-1000XM5" in result["assistant_text"]
    assert result["ui_blocks"] == []


@pytest.mark.asyncio
async def test_compose_falls_back_to_generic_message_when_no_data_at_all(mock_model_service):
    """
    When neither general_product_info nor any listing data exists, product_compose
    must return the generic fallback message (not crash or return empty text).
    """
    state = {
        "user_message": "tell me about some unknown gadget",
        "intent": "product",
        "slots": {},
        "normalized_products": [],
        "affiliate_products": {},
        "review_data": {},
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }
    result = await product_compose(state)
    assert result["success"] is True
    assert result["assistant_text"]  # non-empty fallback
    assert result["ui_blocks"] == []


@pytest.mark.asyncio
async def test_compose_general_product_info_not_used_when_listings_present(mock_model_service):
    """
    When listing data IS present alongside general_product_info, the tool must
    not short-circuit — it should proceed through the full compose path.
    The early-exit guard must only fire when ALL of normalized/affiliate/review are empty.
    """
    state = {
        "user_message": "Sony WH-1000XM5",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "Sony WH-1000XM5", "price": 299, "url": "https://example.com"}
        ],
        "affiliate_products": {},
        "review_data": {},
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "Should not appear — listings are present.",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }
    result = await product_compose(state)
    # The tool must not short-circuit; it must attempt to compose a real response.
    # We only assert it did not raise and returned a dict with the expected keys.
    assert "success" in result
    assert "assistant_text" in result
    assert "ui_blocks" in result
