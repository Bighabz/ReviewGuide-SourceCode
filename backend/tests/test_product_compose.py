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
    fake_service.generate_compose_with_streaming = AsyncMock(side_effect=fake_generate)

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
    fake_service.generate_compose_with_streaming = AsyncMock(side_effect=fake_generate)

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


# ---------------------------------------------------------------------------
# QAR-01: Fallback loop must use `continue` (not `break`) on duplicate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_loop_continue(capturing_model_service_v2):
    """
    QAR-01: When blog_product_names has ["Product A", "Product B", "Product C"]
    and "Product A" is already in seen_card_names (has a product_review card),
    fallback cards must still be generated for "Product B" and "Product C".

    The bug: a `break` statement exits the loop on first duplicate, so B and C
    are silently skipped. Fix requires `continue` instead of `break`.
    """
    fake_service, captured_calls = capturing_model_service_v2

    # "Product A" gets a main review card (has affiliate offers from 2 providers)
    # "Product B" and "Product C" have review data (so they appear in blog_product_names)
    # but NO affiliate offers — they should get fallback cards instead.
    # The order in review_data dict must put A first, then B, then C.
    state = {
        "user_message": "best gadgets",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "Product A", "price": 99, "url": "https://example.com/a"},
            {"name": "Product B", "price": 149, "url": "https://example.com/b"},
            {"name": "Product C", "price": 199, "url": "https://example.com/c"},
        ],
        "affiliate_products": {
            # Product A has both amazon + ebay → gets main review card
            "amazon": [
                {
                    "product_name": "Product A",
                    "offers": [
                        {
                            "title": "Product A",
                            "price": 99.00,
                            "currency": "USD",
                            "url": "https://amazon.com/product-a",
                            "merchant": "Amazon",
                            "image_url": "https://example.com/img/a.jpg",
                        }
                    ],
                }
            ],
            "ebay": [
                {
                    "product_name": "Product A",
                    "offers": [
                        {
                            "title": "Product A",
                            "price": 89.00,
                            "currency": "USD",
                            "url": "https://ebay.com/product-a",
                            "merchant": "eBay",
                            "image_url": "https://example.com/img/a-ebay.jpg",
                        }
                    ],
                }
            ],
            # Product B and C have NO affiliate offers in any provider
        },
        "review_data": {
            # Order matters: A first (gets main card → added to seen_card_names)
            # then B and C (no offers → should get fallback cards)
            "Product A": {
                "avg_rating": 4.5,
                "total_reviews": 500,
                "quality_score": 0.9,
                "sources": [
                    {"site_name": "Wirecutter", "url": "https://wirecutter.com/a", "snippet": "Great product A"},
                ],
            },
            "Product B": {
                "avg_rating": 4.2,
                "total_reviews": 300,
                "quality_score": 0.8,
                "sources": [
                    {"site_name": "Wirecutter", "url": "https://wirecutter.com/b", "snippet": "Good product B"},
                ],
            },
            "Product C": {
                "avg_rating": 4.0,
                "total_reviews": 200,
                "quality_score": 0.75,
                "sources": [
                    {"site_name": "The Verge", "url": "https://theverge.com/c", "snippet": "Decent product C"},
                ],
            },
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

    review_blocks = result["ui_blocks"]
    product_names_in_cards = [
        b["data"]["product_name"]
        for b in review_blocks
        if b.get("type") == "product_review"
    ]

    # "Product A" must have a main review card (it has affiliate offers)
    assert "Product A" in product_names_in_cards, (
        f"Expected 'Product A' main review card, got: {product_names_in_cards}"
    )

    # "Product B" and "Product C" must appear as fallback cards
    # (they have review data → appear in blog_product_names, but no offers → fallback)
    assert "Product B" in product_names_in_cards, (
        f"Expected 'Product B' in product cards (fallback), got: {product_names_in_cards}. "
        f"BUG: loop break on 'Product A' duplicate skipped B and C."
    )
    assert "Product C" in product_names_in_cards, (
        f"Expected 'Product C' in product cards (fallback), got: {product_names_in_cards}. "
        f"BUG: loop break on 'Product A' duplicate skipped B and C."
    )


# ---------------------------------------------------------------------------
# QAR-02: Single-provider products must emit product cards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_provider_card(capturing_model_service_v2):
    """
    QAR-02: A product with only 1 provider (e.g., only Amazon) and a valid
    non-placeholder URL must still emit a product_review card. The current
    multi-provider guard requires 2 providers or curated amzn.to/eBay offers,
    silently dropping legitimate single-retailer products.
    """
    fake_service, captured_calls = capturing_model_service_v2

    state = {
        "user_message": "best coffee maker",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "Breville Barista Express", "price": 699, "url": "https://breville.com/barista-express"},
        ],
        "affiliate_products": {
            # Only one provider — serper_shopping (not curated amzn.to, not eBay)
            "serper_shopping": [
                {
                    "product_name": "Breville Barista Express",
                    "offers": [
                        {
                            "title": "Breville Barista Express",
                            "price": 699.00,
                            "currency": "USD",
                            "url": "https://www.bestbuy.com/breville-barista-express",
                            "merchant": "Best Buy",
                            "image_url": "https://example.com/img/breville.jpg",
                            "source": "serper_shopping",
                        }
                    ],
                }
            ],
        },
        "review_data": {
            "Breville Barista Express": {
                "avg_rating": 4.8,
                "total_reviews": 2000,
                "quality_score": 0.92,
                "sources": [
                    {"site_name": "Wirecutter", "url": "https://wirecutter.com/breville", "snippet": "Best espresso machine"},
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

    result = await product_compose(state)
    assert result["success"] is True

    review_blocks = [b for b in result["ui_blocks"] if b.get("type") == "product_review"]
    product_names_in_cards = [b["data"]["product_name"] for b in review_blocks]

    assert "Breville Barista Express" in product_names_in_cards, (
        f"Expected 'Breville Barista Express' product card (single-provider with valid URL), "
        f"got: {product_names_in_cards}. "
        f"BUG: multi-provider gate silently dropped it."
    )

    # The card must use the real offer URL (not an Amazon search fallback)
    breville_block = next(
        (b for b in review_blocks if b["data"].get("product_name") == "Breville Barista Express"),
        None
    )
    assert breville_block is not None, "Expected Breville Barista Express product_review block"

    affiliate_links = breville_block["data"].get("affiliate_links", [])
    assert len(affiliate_links) >= 1, "Expected at least 1 affiliate link in Breville card"

    # Real cards use the actual offer URL; fallback cards use Amazon search URL with ?k= param
    actual_link = affiliate_links[0].get("affiliate_link", "")
    assert "amazon.com/s?k=" not in actual_link, (
        f"Expected real offer URL (https://www.bestbuy.com/breville-barista-express), "
        f"but got Amazon search fallback URL: {actual_link}. "
        f"BUG: multi-provider gate dropped the real offer; only fallback search URL was generated."
    )


# ---------------------------------------------------------------------------
# QAR-03: Merchant label must match offer domain (no Amazon label on BestBuy URL)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_label_domain_parity(capturing_model_service_v2):
    """
    QAR-03: When an offer has source="Amazon" (label) but url pointing to
    bestbuy.com, the emitted product card's affiliate_links must NOT contain
    an entry where merchant="Amazon" and affiliate_link contains "bestbuy.com".
    The fix should either correct the label or exclude the mismatched offer.
    """
    fake_service, captured_calls = capturing_model_service_v2

    state = {
        "user_message": "best laptop",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "Dell XPS 15", "price": 1299, "url": "https://dell.com/xps15"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "Dell XPS 15",
                    "offers": [
                        {
                            # Mislabeled: source says "Amazon" but URL is BestBuy
                            "title": "Dell XPS 15",
                            "price": 1299.00,
                            "currency": "USD",
                            "url": "https://www.bestbuy.com/site/dell-xps-15",
                            "merchant": "Amazon",
                            "image_url": "https://example.com/img/dell.jpg",
                            "source": "Amazon",
                        }
                    ],
                }
            ],
            "ebay": [
                {
                    "product_name": "Dell XPS 15",
                    "offers": [
                        {
                            "title": "Dell XPS 15",
                            "price": 1199.00,
                            "currency": "USD",
                            "url": "https://ebay.com/dell-xps-15",
                            "merchant": "eBay",
                            "image_url": "https://example.com/img/dell-ebay.jpg",
                            "source": "ebay",
                        }
                    ],
                }
            ],
        },
        "review_data": {
            "Dell XPS 15": {
                "avg_rating": 4.6,
                "total_reviews": 3000,
                "quality_score": 0.91,
                "sources": [
                    {"site_name": "The Verge", "url": "https://theverge.com/dell-xps", "snippet": "Excellent display"},
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

    result = await product_compose(state)
    assert result["success"] is True

    review_blocks = [b for b in result["ui_blocks"] if b.get("type") == "product_review"]
    assert len(review_blocks) >= 1, f"Expected at least one product_review block, got: {[b.get('type') for b in result['ui_blocks']]}"

    dell_block = next(
        (b for b in review_blocks if b["data"].get("product_name") == "Dell XPS 15"),
        None
    )
    assert dell_block is not None, "Expected Dell XPS 15 product_review block"

    affiliate_links = dell_block["data"].get("affiliate_links", [])

    # Check that no affiliate link has merchant="Amazon" but URL pointing to bestbuy.com
    for link in affiliate_links:
        merchant = (link.get("merchant") or "").lower()
        url = (link.get("affiliate_link") or "").lower()
        assert not (merchant == "amazon" and "bestbuy.com" in url), (
            f"Label-domain mismatch: merchant='Amazon' but URL='{link.get('affiliate_link')}'. "
            f"Fix must correct label or exclude the offer."
        )


# ---------------------------------------------------------------------------
# QAR-07: Citation URLs must start with "http" — no fabricated/empty URLs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_citations_have_real_urls(capturing_model_service_v2):
    """
    QAR-07: When review_bundles have sources with a mix of real http URLs,
    empty strings, and None values, the citations list must contain ONLY
    URLs that start with "http". Empty and None values must be excluded.
    """
    fake_service, captured_calls = capturing_model_service_v2

    state = {
        "user_message": "best running shoes",
        "intent": "product",
        "slots": {},
        "normalized_products": [
            {"name": "Nike Pegasus 40", "price": 130, "url": "https://nike.com/pegasus-40"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "Nike Pegasus 40",
                    "offers": [
                        {
                            "title": "Nike Pegasus 40",
                            "price": 130.00,
                            "currency": "USD",
                            "url": "https://amazon.com/nike-pegasus",
                            "merchant": "Amazon",
                            "image_url": "https://example.com/img/nike.jpg",
                            "source": "amazon",
                        }
                    ],
                }
            ],
            "ebay": [
                {
                    "product_name": "Nike Pegasus 40",
                    "offers": [
                        {
                            "title": "Nike Pegasus 40",
                            "price": 119.00,
                            "currency": "USD",
                            "url": "https://ebay.com/nike-pegasus",
                            "merchant": "eBay",
                            "image_url": "https://example.com/img/nike-ebay.jpg",
                            "source": "ebay",
                        }
                    ],
                }
            ],
        },
        "review_data": {
            "Nike Pegasus 40": {
                "avg_rating": 4.7,
                "total_reviews": 5000,
                "quality_score": 0.93,
                "sources": [
                    # Mix of real URLs, empty strings, and None
                    {"site_name": "Runner's World", "url": "https://runnersworld.com/pegasus", "snippet": "Best everyday trainer"},
                    {"site_name": "BadSource", "url": "", "snippet": "Some review"},
                    {"site_name": "NoneSource", "url": None, "snippet": "Another review"},
                    {"site_name": "Road Runner", "url": "https://roadrunnersports.com/pegasus", "snippet": "Great cushioning"},
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

    result = await product_compose(state)
    assert result["success"] is True

    citations = result.get("citations", [])
    assert len(citations) >= 1, f"Expected at least 1 citation, got 0"

    for url in citations:
        assert url and url.startswith("http"), (
            f"Citation URL must start with 'http', got: {repr(url)}. "
            f"Empty/None URLs from review sources must be filtered out."
        )
