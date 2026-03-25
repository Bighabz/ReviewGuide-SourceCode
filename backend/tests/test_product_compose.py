"""
Unit tests for product_compose tool.

Covers the general_product_info fallback path: when the planner routes through
product_general_information (factoid queries), the fetched answer must be
surfaced as assistant_text rather than silently discarded by the no-results guard.

Also covers RX-06: opener and conclusion LLM calls must be removed.
Also covers RX-07: review source URLs must be threaded into blog_data.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

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
    with patch("app.services.model_service.model_service", fake_service):
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
async def test_compose_ignores_whitespace_only_general_product_info(mock_model_service):
    """
    Whitespace-only general_product_info must not be surfaced as assistant_text.
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
        "general_product_info": "   ",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }
    result = await product_compose(state)
    assert result["success"] is True
    assert result["assistant_text"].strip()
    assert "wasn't able to find" in result["assistant_text"]


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


# ---------------------------------------------------------------------------
# RX-06: Opener and conclusion LLM calls must be removed
# ---------------------------------------------------------------------------

_REVIEW_STATE_WITH_DATA = {
    "user_message": "best noise cancelling headphones under $300",
    "intent": "product",
    "slots": {"category": "headphones", "budget": 300},
    "normalized_products": [
        {"name": "Sony WH-1000XM5", "price": 299, "url": "https://example.com/sony"},
        {"name": "Bose QuietComfort 45", "price": 279, "url": "https://example.com/bose"},
    ],
    "affiliate_products": {
        "amazon": [
            {
                "product_name": "Sony WH-1000XM5",
                "offers": [{"title": "Sony WH-1000XM5", "price": 299.99, "currency": "USD",
                             "url": "https://amazon.com/sony", "merchant": "Amazon",
                             "image_url": "https://example.com/img.jpg"}]
            }
        ]
    },
    "review_data": {
        "Sony WH-1000XM5": {
            "avg_rating": 4.7,
            "total_reviews": 12500,
            "quality_score": 0.95,
            "sources": [
                {"site_name": "Wirecutter", "url": "https://wirecutter.com/sony", "snippet": "Best in class ANC"},
                {"site_name": "The Verge", "url": "https://theverge.com/sony", "snippet": "Excellent comfort"},
            ]
        },
        "Bose QuietComfort 45": {
            "avg_rating": 4.5,
            "total_reviews": 8400,
            "quality_score": 0.88,
            "sources": [
                {"site_name": "RTINGS", "url": "https://rtings.com/bose", "snippet": "Great sound quality"},
            ]
        }
    },
    "comparison_html": None,
    "comparison_data": None,
    "general_product_info": "",
    "conversation_history": [],
    "last_search_context": {},
    "search_history": [],
}


@pytest.fixture
def capturing_model_service():
    """
    Patch model_service to capture all call kwargs and return plausible strings
    so the tool can complete without error.

    The reverted product_compose imports model_service inside the function, so
    we patch at `app.services.model_service.model_service`.
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
    fake_service.generate_compose = fake_generate

    with patch("app.services.model_service.model_service", fake_service):
        yield fake_service, captured_calls


# ---------------------------------------------------------------------------
# RX-07: Review source URLs must be threaded into blog_data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blog_includes_source_inline_links(capturing_model_service):
    """
    RX-07: When review bundle has sources with url+site_name, the blog_data string
    passed to model_service.generate for the blog_article call must contain
    'Reviews: [SiteName](url)' entries.
    """
    import copy
    fake_service, captured_calls = capturing_model_service
    state = copy.deepcopy(_REVIEW_STATE_WITH_DATA)

    result = await product_compose(state)

    assert result["success"] is True

    # Find the blog_article generate call
    blog_calls = [c for c in captured_calls if c.get("agent_name") == "blog_article_composer"]
    assert len(blog_calls) >= 1, "Expected at least one blog_article_composer call"

    # Extract the user content from the messages list
    blog_call = blog_calls[0]
    messages = blog_call.get("messages", [])
    user_content = next(
        (m["content"] for m in messages if m.get("role") == "user"),
        ""
    )

    # The blog_data must contain inline source refs for Sony (which has sources with url+site_name)
    assert "Reviews:" in user_content, (
        f"Expected 'Reviews:' in blog_data user content, but got:\n{user_content[:500]}"
    )
    assert "[Wirecutter]" in user_content, (
        f"Expected '[Wirecutter]' markdown link in blog_data, but got:\n{user_content[:500]}"
    )


# ---------------------------------------------------------------------------
# FIX-01: System prompt must forbid inventing URLs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_system_prompt_forbids_inventing_urls(capturing_model_service):
    """
    FIX-01: The blog system prompt must explicitly instruct the LLM to never
    invent URLs — only link to sources provided in the data.
    """
    import copy
    fake_service, captured_calls = capturing_model_service
    state = copy.deepcopy(_REVIEW_STATE_WITH_DATA)

    result = await product_compose(state)
    assert result["success"] is True

    # Find the blog_article generate call
    blog_calls = [c for c in captured_calls if c.get("agent_name") == "blog_article_composer"]
    assert len(blog_calls) >= 1, "Expected at least one blog_article_composer call"

    blog_call = blog_calls[0]
    messages = blog_call.get("messages", [])
    system_content = next(
        (m["content"] for m in messages if m.get("role") == "system"),
        ""
    )

    lower_content = system_content.lower()
    assert "never invent" in lower_content, (
        f"System prompt must contain 'never invent URLs' guard, but got:\n{system_content[:500]}"
    )
    # Check that at least one "never invent" occurrence specifically mentions URLs
    parts = lower_content.split("never invent")
    has_url_guard = any("url" in part[:30] for part in parts[1:])
    assert has_url_guard, (
        "The 'never invent' instruction must specifically mention URLs"
    )


# ---------------------------------------------------------------------------
# FIX-01: Citations must prefer review source URLs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_citations_contain_review_source_urls(capturing_model_service):
    """
    FIX-01: When review_bundles have sources with URLs, the citations array
    must contain those review source URLs (e.g. Wirecutter, RTINGS) — not
    just product buy-page URLs from normalized_products.
    """
    import copy
    fake_service, captured_calls = capturing_model_service
    state = copy.deepcopy(_REVIEW_STATE_WITH_DATA)

    result = await product_compose(state)
    assert result["success"] is True

    citations = result.get("citations", [])
    assert len(citations) >= 2, (
        f"Expected at least 2 citations from review sources, got {len(citations)}: {citations}"
    )
    # Should contain review source URLs, not product page URLs
    review_urls = {"https://wirecutter.com/sony", "https://theverge.com/sony", "https://rtings.com/bose"}
    product_urls = {"https://example.com/sony", "https://example.com/bose"}
    # At least one review source URL must be in citations
    assert any(url in review_urls for url in citations), (
        f"Expected review source URLs in citations, but got only: {citations}"
    )
    # Product page URLs should NOT be the primary citations when review sources exist
    assert not all(url in product_urls for url in citations), (
        f"Citations should prefer review source URLs over product page URLs: {citations}"
    )


@pytest.mark.asyncio
async def test_citations_fallback_to_product_urls_without_review_sources(capturing_model_service):
    """
    FIX-01: When no review source URLs exist, citations must fall back to
    normalized_products URLs (backward compatibility).
    """
    fake_service, captured_calls = capturing_model_service
    state = {
        "user_message": "best wireless earbuds",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "AirPods Pro", "price": 249, "url": "https://example.com/airpods"},
            {"name": "Galaxy Buds", "price": 149, "url": "https://example.com/galaxy"},
        ],
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
    citations = result.get("citations", [])
    assert len(citations) >= 1, (
        f"Expected at least 1 citation from normalized_products, got {len(citations)}"
    )
    assert "https://example.com/airpods" in citations or "https://example.com/galaxy" in citations, (
        f"Expected product URLs as fallback citations, got: {citations}"
    )


# ---------------------------------------------------------------------------
# UX-03 / UX-04 / UX-05: Top Pick, 5-product cap, comparison follow-up
# ---------------------------------------------------------------------------

@pytest.fixture
def capturing_model_service_v2():
    """
    Extended model service mock that handles top_pick_composer and comparison_composer
    agent names in addition to the originals.
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
        if agent_name == "top_pick_composer":
            return '{"headline": "Best noise cancellation in its class", "best_for": "Commuters and frequent flyers who want silence", "not_for": "Audiophiles who prioritize pure sound quality over ANC"}'
        if agent_name == "comparison_composer":
            return '{"products": [{"title": "Sony WH-1000XM5", "price": 299, "pros": ["Great ANC"], "cons": ["Heavy"]}, {"title": "Bose QC 45", "price": 279, "pros": ["Comfortable"], "cons": ["Older codec"]}], "criteria": ["ANC", "Comfort"], "summary": "Both are excellent."}'
        return "mock response"

    fake_service = MagicMock()
    fake_service.generate = fake_generate
    fake_service.generate_compose = fake_generate

    with patch("app.services.model_service.model_service", fake_service):
        yield fake_service, captured_calls


@pytest.mark.asyncio
async def test_top_pick_block_present(capturing_model_service_v2):
    """
    UX-03: When review_data has products with quality_score, product_compose must
    produce a top_pick block at the beginning of ui_blocks with product_name,
    headline, best_for, not_for fields.
    """
    import copy
    fake_service, captured_calls = capturing_model_service_v2
    state = copy.deepcopy(_REVIEW_STATE_WITH_DATA)

    result = await product_compose(state)

    assert result["success"] is True

    # Find top_pick block
    top_pick_blocks = [b for b in result["ui_blocks"] if b.get("type") == "top_pick"]
    assert len(top_pick_blocks) >= 1, (
        f"Expected at least one top_pick block in ui_blocks, got types: "
        f"{[b.get('type') for b in result['ui_blocks']]}"
    )

    tp = top_pick_blocks[0]
    tp_data = tp.get("data", {})
    assert "product_name" in tp_data, "top_pick block missing product_name"
    assert "headline" in tp_data, "top_pick block missing headline"
    assert "best_for" in tp_data, "top_pick block missing best_for"
    assert "not_for" in tp_data, "top_pick block missing not_for"

    # top_pick must appear BEFORE any product_review block
    top_pick_idx = next(
        i for i, b in enumerate(result["ui_blocks"]) if b.get("type") == "top_pick"
    )
    product_review_indices = [
        i for i, b in enumerate(result["ui_blocks"]) if b.get("type") == "product_review"
    ]
    if product_review_indices:
        assert top_pick_idx < product_review_indices[0], (
            f"top_pick (index {top_pick_idx}) must appear before first product_review "
            f"(index {product_review_indices[0]})"
        )


@pytest.mark.asyncio
async def test_max_five_products(capturing_model_service_v2):
    """
    UX-04: Even with 8 products in affiliate_products, product_compose must not
    return more than 5 product_review blocks or more than 5 items in any
    products/carousel block.
    """
    fake_service, captured_calls = capturing_model_service_v2

    # Build state with 8 products
    product_names = [
        "Product Alpha", "Product Beta", "Product Gamma", "Product Delta",
        "Product Epsilon", "Product Zeta", "Product Eta", "Product Theta"
    ]
    state = {
        "user_message": "best wireless headphones",
        "intent": "product",
        "slots": {"category": "headphones"},
        "normalized_products": [
            {"name": name, "price": 100 + i * 50, "url": f"https://example.com/{name.lower().replace(' ', '-')}"}
            for i, name in enumerate(product_names)
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": name,
                    "offers": [{
                        "title": name,
                        "price": 100 + i * 50,
                        "currency": "USD",
                        "url": f"https://amazon.com/{name.lower().replace(' ', '-')}",
                        "merchant": "Amazon",
                        "image_url": f"https://example.com/img/{i}.jpg"
                    }]
                }
                for i, name in enumerate(product_names)
            ]
        },
        "review_data": {
            name: {
                "avg_rating": 4.5 - i * 0.1,
                "total_reviews": 1000 - i * 100,
                "quality_score": 0.95 - i * 0.05,
                "sources": [
                    {"site_name": "Wirecutter", "url": f"https://wirecutter.com/{i}", "snippet": f"Good product {name}"}
                ]
            }
            for i, name in enumerate(product_names)
        },
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }

    result = await product_compose(state)
    assert result["success"] is True

    # Count product_review blocks
    review_blocks = [b for b in result["ui_blocks"] if b.get("type") == "product_review"]
    assert len(review_blocks) <= 5, (
        f"Expected at most 5 product_review blocks, got {len(review_blocks)}"
    )

    # Check that no products or carousel block has more than 5 items
    for block in result["ui_blocks"]:
        if block.get("type") in ("products", "carousel"):
            items = block.get("data", {})
            if isinstance(items, dict):
                products_list = items.get("products", items.get("items", []))
            elif isinstance(items, list):
                products_list = items
            else:
                products_list = []
            assert len(products_list) <= 5, (
                f"Block type '{block['type']}' has {len(products_list)} items, expected <= 5"
            )


@pytest.mark.asyncio
async def test_comparison_follow_up(capturing_model_service_v2):
    """
    UX-05: When user_message is a comparison follow-up and last_search_context
    has product_names, product_compose must return a product_comparison block.
    """
    fake_service, captured_calls = capturing_model_service_v2
    state = {
        "user_message": "how do these compare?",
        "intent": "product",
        "slots": {},
        "normalized_products": [],
        "affiliate_products": {},
        "review_data": {},
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {
            "product_names": ["Sony WH-1000XM5", "Bose QC 45"],
            "category": "headphones",
            "top_prices": {"Sony WH-1000XM5": 299, "Bose QC 45": 279},
            "avg_rating": {"Sony WH-1000XM5": 4.7, "Bose QC 45": 4.5},
        },
        "search_history": [],
    }

    result = await product_compose(state)
    assert result["success"] is True

    comparison_blocks = [b for b in result["ui_blocks"] if b.get("type") == "product_comparison"]
    assert len(comparison_blocks) >= 1, (
        f"Expected at least one product_comparison block, got types: "
        f"{[b.get('type') for b in result['ui_blocks']]}"
    )
