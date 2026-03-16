"""
Unit tests for chat streaming behavior.

Covers:
  RX-01: Product cards (ui_blocks via stream_chunk_data) are emitted to the
         frontend before product_compose starts — the plan executor must fire
         an artifact callback after the product_affiliate step.
  RX-02: product_compose calls model_service.generate with stream=True for
         the blog_article task so tokens stream incrementally.
  Token registry: register_token_callback, get_token_callbacks,
         clear_token_callbacks are importable from plan_executor.
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

from mcp_server.tools.product_compose import product_compose  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_token_callback_registry_importable():
    """
    Task 1: register_token_callback, get_token_callbacks, clear_token_callbacks
    must be importable from app.services.plan_executor.
    """
    from app.services.plan_executor import (
        register_token_callback,
        get_token_callbacks,
        clear_token_callbacks,
    )
    # Verify the registry is a list-like container
    clear_token_callbacks()
    assert get_token_callbacks() == []

    sentinel = object()
    register_token_callback(sentinel)
    assert sentinel in get_token_callbacks()

    clear_token_callbacks()
    assert get_token_callbacks() == []

@pytest.mark.asyncio
async def test_product_cards_emitted_before_compose():
    """
    RX-01: After the product_affiliate step completes, the plan executor must
    emit an artifact callback (stream_chunk_data) containing product card
    ui_blocks so the frontend can render cards while product_compose is still
    running.

    Test approach: verify that product_affiliate sets stream_chunk_data in its
    return dict, which is the contract the plan executor relies on to detect
    when to fire the mid-pipeline emit.
    """
    from mcp_server.tools.product_affiliate import product_affiliate

    state = {
        "normalized_products": [
            {"title": "Sony WH-1000XM5"},
            {"title": "Bose QuietComfort 45"},
        ],
        "slots": {},
        "last_search_context": {},
    }

    with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
         patch("app.core.config.settings") as mock_settings:
        mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
        mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
        mock_manager.get_available_providers.return_value = []

        result = await product_affiliate(state)

    # RX-01: product_affiliate must set stream_chunk_data so the plan executor
    # knows to emit product cards immediately after this step.
    stream_chunk = result.get("stream_chunk_data")
    assert stream_chunk is not None, (
        "RX-01: plan_executor does not emit artifact callback after product_affiliate step — "
        "product_affiliate must set stream_chunk_data={'type': 'ui_blocks', ...} in its "
        "return dict for the plan executor to detect and forward to the SSE stream"
    )
    assert stream_chunk.get("type") == "ui_blocks", (
        f"RX-01: Expected stream_chunk_data['type'] == 'ui_blocks', got: {stream_chunk}"
    )


@pytest.mark.asyncio
async def test_blog_article_uses_model_service_stream():
    """
    RX-02: product_compose must call model_service.generate with stream=True
    for the blog_article task so that tokens are forwarded to the SSE stream
    incrementally instead of waiting for the full article to be generated.

    Test approach: patch model_service.generate to capture kwargs, run
    product_compose with data that triggers the blog_article path, then
    assert the blog_article_composer call used stream=True.
    """
    captured_calls = []

    async def fake_generate(**kwargs):
        captured_calls.append(kwargs)
        agent_name = kwargs.get("agent_name", "")
        if agent_name == "blog_article_composer":
            return "## Sony WH-1000XM5\nGreat headphones.\n\n## Our Verdict\nBuy the Sony."
        if agent_name == "review_consensus":
            return "Excellent product praised by experts."
        if agent_name == "product_compose_descriptions":
            return '{"descriptions": ["desc1", "desc2"]}'
        return "mock response"

    fake_service = MagicMock()
    fake_service.generate = fake_generate

    state = {
        "user_message": "best wireless headphones",
        "intent": "product",
        "slots": {"category": "headphones"},
        "normalized_products": [
            {"name": "Sony WH-1000XM5", "price": 299, "url": "https://example.com/sony"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "Sony WH-1000XM5",
                    "offers": [
                        {
                            "title": "Sony WH-1000XM5",
                            "price": 299.99,
                            "currency": "USD",
                            "url": "https://amazon.com/sony",
                            "merchant": "Amazon",
                            "image_url": "https://example.com/img.jpg",
                        }
                    ],
                }
            ]
        },
        "review_data": {
            "Sony WH-1000XM5": {
                "avg_rating": 4.7,
                "total_reviews": 12500,
                "quality_score": 0.95,
                "sources": [
                    {
                        "site_name": "Wirecutter",
                        "url": "https://wirecutter.com/sony",
                        "snippet": "Best in class ANC",
                    }
                ],
            }
        },
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }

    with patch("mcp_server.tools.product_compose.model_service", fake_service, create=True):
        result = await product_compose(state)

    assert result["success"] is True

    # Find the blog_article_composer call and verify stream=True
    blog_calls = [c for c in captured_calls if c.get("agent_name") == "blog_article_composer"]
    assert len(blog_calls) >= 1, (
        f"RX-02: Expected at least one blog_article_composer call but none found. "
        f"All calls: {[c.get('agent_name') for c in captured_calls]}"
    )

    blog_call = blog_calls[0]
    assert blog_call.get("stream") is True, (
        f"RX-02: product_compose does not call model_service.generate(stream=True) "
        f"for blog_article — got stream={blog_call.get('stream')}. "
        f"Update the blog_article generate call to pass stream=True."
    )
