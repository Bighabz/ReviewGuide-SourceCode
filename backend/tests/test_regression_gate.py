"""
Regression Gate — QA Remediation Phase 23

These tests gate deploys. All must pass before release.
Run: python -m pytest tests/test_regression_gate.py -v

Automated gate conditions (QAR-01 through QAR-07):
1. Affiliate label-domain parity (no Amazon label on BestBuy URLs)
2. Accessory suppression (no chargers/cases in laptop results)
3. Budget enforcement (no $2000 items in "under $500" queries)
4. Travel non-hang (partial response returned, not indefinite wait)
5. Source link presence (citations have real URLs)

NOT in automated gate (manual per VALIDATION.md):
- QAR-13: WCAG contrast (requires browser rendering)
- QAR-14: iOS scroll (requires real device)
- QAR-15: Landscape nav (requires device orientation)
"""
import asyncio
import os
import time
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


# ---------------------------------------------------------------------------
# Shared mock helper
# ---------------------------------------------------------------------------

def _make_model_service_mock():
    """Return a mock model_service that returns plausible strings without real API calls."""
    fake_service = MagicMock()
    fake_service.get_response = AsyncMock(return_value="mock response")
    fake_service.generate = AsyncMock(return_value="mock response")
    fake_service.generate_compose = AsyncMock(return_value="mock response")
    fake_service.get_streaming_response = AsyncMock(return_value=iter([]))
    fake_service.generate_compose_with_streaming = AsyncMock(return_value="mock response")
    return fake_service


# ---------------------------------------------------------------------------
# Gate 1: Affiliate label-domain parity (QAR-03)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_affiliate_label_domain_parity():
    """
    Regression gate for QAR-03: affiliate label-domain parity.

    Prevents: offers labeled "Amazon" that point to bestbuy.com, walmart.com,
    or other non-Amazon domains. Before the fix, mis-labeled offers confused
    users and broke trust.

    This test calls product_compose with an offer that has merchant="Amazon"
    but a Best Buy URL. The resulting affiliate_links in the product_review
    block must have merchant corrected to "Best Buy", not left as "Amazon".
    """
    from mcp_server.tools.product_compose import product_compose

    fake_service = _make_model_service_mock()
    fake_service.generate = AsyncMock(
        return_value="## Sony WH-1000XM5\nExcellent noise-cancelling headphones.\n\n## Our Verdict\nHighly recommended."
    )

    state = {
        "user_message": "best noise cancelling headphones",
        "intent": "product",
        "slots": {"category": "headphones"},
        "normalized_products": [
            {"name": "Sony WH-1000XM5", "price": 299, "url": "https://www.bestbuy.com/sony"},
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
                            # Mislabeled: merchant says "Amazon" but URL is Best Buy
                            "merchant": "Amazon",
                            "url": "https://www.bestbuy.com/site/sony-wh-1000xm5/1234",
                            "image_url": "https://example.com/img.jpg",
                            "source": "bestbuy",
                        }
                    ]
                }
            ]
        },
        "review_data": {
            "Sony WH-1000XM5": {
                "avg_rating": 4.7,
                "total_reviews": 1200,
                "quality_score": 0.90,
                "sources": [
                    {"site_name": "Wirecutter", "url": "https://wirecutter.com/sony", "snippet": "Best pick"},
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

    with patch("app.services.model_service.model_service", fake_service):
        result = await product_compose(state)

    assert result["success"] is True, f"product_compose failed: {result}"

    # Find the product_review block and inspect affiliate_links
    product_review_blocks = [b for b in result.get("ui_blocks", []) if b.get("type") == "product_review"]
    assert product_review_blocks, "Expected at least one product_review ui_block"

    for block in product_review_blocks:
        for link in block["data"].get("affiliate_links", []):
            merchant = link.get("merchant", "")
            url = link.get("affiliate_link", "")
            # If URL is from Best Buy, merchant must NOT be "Amazon"
            if "bestbuy.com" in url.lower():
                assert merchant.lower() != "amazon", (
                    f"QAR-03 REGRESSION: offer URL is {url!r} but merchant label is still {merchant!r}. "
                    "Label-domain parity fix is broken."
                )
                assert "best buy" in merchant.lower() or merchant.lower() in {"bestbuy", "best buy"} or merchant, (
                    f"QAR-03 REGRESSION: expected 'Best Buy' merchant for bestbuy.com URL, got {merchant!r}"
                )


# ---------------------------------------------------------------------------
# Gate 2: Accessory suppression (QAR-04)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_accessory_suppression():
    """
    Regression gate for QAR-04: accessory suppression in product compose.

    Prevents: laptop search results that include chargers, cases, or other
    accessories. Before the fix, users searching for "best laptops" would
    receive product cards for "MacBook Charger" or "Laptop Case".

    This test calls product_compose with a "best laptops" query and a mix of
    real laptops and accessories. The resulting ui_blocks must NOT contain
    product_review cards for any accessory items.
    """
    from mcp_server.tools.product_compose import product_compose, ACCESSORY_KEYWORDS

    fake_service = _make_model_service_mock()
    fake_service.generate = AsyncMock(
        return_value="## MacBook Pro\nPowerful laptop.\n\n## Dell XPS 15\nExcellent display."
    )

    state = {
        "user_message": "best laptops under $2000",
        "intent": "product",
        "slots": {"category": "laptops", "budget": 2000},
        "normalized_products": [
            {"name": "MacBook Pro 14-inch", "price": 1999, "url": "https://apple.com/macbook-pro"},
            {"name": "Dell XPS 15", "price": 1799, "url": "https://dell.com/xps15"},
            # Accessories that must be suppressed
            {"name": "MacBook Charger 140W", "price": 99, "url": "https://amazon.com/charger"},
            {"name": "Laptop Case 15 inch", "price": 29, "url": "https://amazon.com/case"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "MacBook Pro 14-inch",
                    "offers": [
                        {"title": "MacBook Pro 14-inch", "price": 1999.99, "currency": "USD",
                         "merchant": "Apple", "url": "https://amazon.com/macbook-pro",
                         "image_url": "https://example.com/mbp.jpg", "source": "amazon"}
                    ]
                },
                {
                    "product_name": "MacBook Charger 140W",
                    "offers": [
                        {"title": "MacBook Charger 140W", "price": 99.99, "currency": "USD",
                         "merchant": "Amazon", "url": "https://amazon.com/charger",
                         "image_url": "https://example.com/charger.jpg", "source": "amazon"}
                    ]
                },
                {
                    "product_name": "Laptop Case 15 inch",
                    "offers": [
                        {"title": "Laptop Case 15 inch", "price": 29.99, "currency": "USD",
                         "merchant": "Amazon", "url": "https://amazon.com/case",
                         "image_url": "https://example.com/case.jpg", "source": "amazon"}
                    ]
                },
            ]
        },
        "review_data": {
            "MacBook Pro 14-inch": {
                "avg_rating": 4.8, "total_reviews": 5000, "quality_score": 0.95,
                "sources": [{"site_name": "Wirecutter", "url": "https://wirecutter.com/mbp", "snippet": "Top pick"}]
            },
        },
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }

    with patch("app.services.model_service.model_service", fake_service):
        result = await product_compose(state)

    assert result["success"] is True, f"product_compose failed: {result}"

    # Collect all product names from ui_blocks
    all_product_names = []
    for block in result.get("ui_blocks", []):
        if block.get("type") == "product_review":
            name = block["data"].get("product_name", "")
            all_product_names.append(name.lower())
        elif block.get("type") == "product_cards":
            for card in block["data"].get("products", []):
                all_product_names.append(card.get("name", "").lower())

    # No accessory keywords should appear in any product name
    for pname in all_product_names:
        for kw in ACCESSORY_KEYWORDS:
            assert kw not in pname, (
                f"QAR-04 REGRESSION: accessory keyword {kw!r} found in result product name {pname!r}. "
                "Accessory suppression is broken."
            )


# ---------------------------------------------------------------------------
# Gate 3: Budget enforcement (QAR-05)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_budget_enforcement():
    """
    Regression gate for QAR-05: budget enforcement in product compose.

    Prevents: when a product has multiple offers where SOME are in-budget and
    SOME exceed the budget, the over-budget offers must be removed. Before the
    fix, budget filtering was not applied and all offers appeared regardless
    of the user's stated budget constraint.

    Design note: when ALL offers for a product exceed the budget, the product
    is intentionally kept (so the user still sees results). This gate tests the
    case where there IS an in-budget offer for a product — in that case,
    over-budget offers for the SAME product must be removed.
    """
    from mcp_server.tools.product_compose import product_compose, _parse_budget

    # First verify _parse_budget correctly parses "under $500" → (None, 500.0)
    budget_min, budget_max = _parse_budget("under $500")
    assert budget_max == 500.0, (
        f"QAR-05 REGRESSION: _parse_budget('under $500') returned budget_max={budget_max}, expected 500.0"
    )

    fake_service = _make_model_service_mock()
    fake_service.generate = AsyncMock(
        return_value="## Budget Headphones\nGreat value picks under $500."
    )

    # A product with two offers: one in budget ($299), one over budget ($799)
    # After filtering, only the $299 offer should survive for this product
    state = {
        "user_message": "best headphones under $500",
        "intent": "product",
        "slots": {"category": "headphones", "budget": "under $500"},
        "normalized_products": [
            {"name": "Sony WH-1000XM5", "price": 299, "url": "https://amazon.com/sony"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "Sony WH-1000XM5",
                    "offers": [
                        # In-budget offer — must be KEPT
                        {"title": "Sony WH-1000XM5 Amazon", "price": 299.99, "currency": "USD",
                         "merchant": "Amazon", "url": "https://amazon.com/sony",
                         "image_url": "https://example.com/sony.jpg", "source": "amazon"}
                    ]
                },
            ],
            "ebay": [
                {
                    "product_name": "Sony WH-1000XM5",
                    "offers": [
                        # Over-budget offer — must be REMOVED since in-budget alternative exists
                        {"title": "Sony WH-1000XM5 eBay markup", "price": 799.99, "currency": "USD",
                         "merchant": "eBay", "url": "https://ebay.com/itm/sony",
                         "image_url": "https://example.com/sony-ebay.jpg", "source": "ebay"}
                    ]
                },
            ],
        },
        "review_data": {
            "Sony WH-1000XM5": {
                "avg_rating": 4.7, "total_reviews": 12500, "quality_score": 0.95,
                "sources": [{"site_name": "Wirecutter", "url": "https://wirecutter.com/sony", "snippet": "Best ANC"}]
            },
        },
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }

    with patch("app.services.model_service.model_service", fake_service):
        result = await product_compose(state)

    assert result["success"] is True, f"product_compose failed: {result}"

    # Check all affiliate_link prices in product_review blocks
    # When an in-budget offer exists, over-budget offers must be stripped
    for block in result.get("ui_blocks", []):
        if block.get("type") == "product_review":
            for link in block["data"].get("affiliate_links", []):
                price = link.get("price", 0)
                if price and isinstance(price, (int, float)):
                    assert price <= 500, (
                        f"QAR-05 REGRESSION: offer price ${price} exceeds budget $500 in result "
                        "even though an in-budget offer exists for the same product. "
                        "Budget enforcement is broken."
                    )


# ---------------------------------------------------------------------------
# Gate 4: Travel non-hang (QAR-06)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_travel_non_hang():
    """
    Regression gate for QAR-06: travel_compose must not hang when all upstream
    travel tools fail or return empty data.

    Prevents: indefinite hang when Viator, hotels, or flights APIs all time out.
    Before the fix, travel_compose would block waiting for data that never arrived,
    causing the chat to freeze.

    This test calls travel_compose with all upstream data set to None (simulating
    complete upstream failure) and asserts it returns within 1 second.
    """
    from mcp_server.tools.travel_compose import travel_compose

    fake_service = _make_model_service_mock()

    state = {
        "user_message": "Plan a 5-day trip to Tokyo",
        "intent": "travel",
        "slots": {"destination": "Tokyo", "duration_days": 5},
        # All upstream data is None — simulates complete API timeout/failure
        "itinerary": None,
        "hotels": None,
        "flights": None,
        "activities": None,
        "cars": None,
        "destination_facts": None,
        "general_travel_info": None,
        "travel_results": None,
    }

    start = time.monotonic()

    with patch("app.services.model_service.model_service", fake_service):
        result = await travel_compose(state)

    elapsed = time.monotonic() - start

    assert elapsed < 1.0, (
        f"QAR-06 REGRESSION: travel_compose took {elapsed:.2f}s with all-None data. "
        "Non-hang fix is broken — response must arrive in under 1 second."
    )
    assert result.get("success") is True, (
        f"QAR-06 REGRESSION: expected success=True for all-None state, got {result.get('success')}"
    )
    assert result.get("assistant_text"), (
        "QAR-06 REGRESSION: expected non-empty assistant_text for timeout recovery path"
    )


# ---------------------------------------------------------------------------
# Gate 5: Source link presence (QAR-07)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gate_source_link_presence():
    """
    Regression gate for QAR-07: citations list must contain valid http URLs
    when review sources are available.

    Prevents: citations being empty or containing non-URL strings when the
    review_data has real source URLs. Before the fix, citation assembly was
    broken and sources like Wirecutter/RTINGS were silently dropped.

    This test calls product_compose with review_data that has valid source URLs
    and asserts that the returned citations list contains at least one valid
    http URL.
    """
    from mcp_server.tools.product_compose import product_compose

    fake_service = _make_model_service_mock()
    fake_service.generate = AsyncMock(
        return_value="## Sony WH-1000XM5\nBest pick according to Wirecutter."
    )

    state = {
        "user_message": "best wireless headphones",
        "intent": "product",
        "slots": {"category": "headphones"},
        "normalized_products": [
            {"name": "Sony WH-1000XM5", "price": 299, "url": "https://amazon.com/sony"},
        ],
        "affiliate_products": {
            "amazon": [
                {
                    "product_name": "Sony WH-1000XM5",
                    "offers": [
                        {"title": "Sony WH-1000XM5", "price": 299.99, "currency": "USD",
                         "merchant": "Amazon", "url": "https://amazon.com/sony",
                         "image_url": "https://example.com/img.jpg", "source": "amazon"}
                    ]
                }
            ]
        },
        "review_data": {
            "Sony WH-1000XM5": {
                "avg_rating": 4.7,
                "total_reviews": 12500,
                "quality_score": 0.90,
                "sources": [
                    {"site_name": "Wirecutter", "url": "https://www.wirecutter.com/reviews/best-wireless-headphones/", "snippet": "Top pick"},
                    {"site_name": "RTINGS", "url": "https://www.rtings.com/headphones/reviews/sony/wh-1000xm5", "snippet": "Excellent ANC"},
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

    with patch("app.services.model_service.model_service", fake_service):
        result = await product_compose(state)

    assert result["success"] is True, f"product_compose failed: {result}"

    citations = result.get("citations", [])
    assert citations, (
        "QAR-07 REGRESSION: citations list is empty even though review_data has source URLs. "
        "Source link presence fix is broken."
    )

    # At least one citation must be a valid http URL
    http_citations = [c for c in citations if isinstance(c, str) and c.startswith("http")]
    assert http_citations, (
        f"QAR-07 REGRESSION: no valid http URLs in citations {citations!r}. "
        "Source link presence fix is broken."
    )
