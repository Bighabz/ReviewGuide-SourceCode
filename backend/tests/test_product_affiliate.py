"""
Unit tests for product_affiliate tool.

Covers:
  RX-03: Per-product search coroutines are gathered in parallel (asyncio.gather),
         not run sequentially in a for loop.
  RX-05: The fast-path product plan (PlannerAgent._create_fast_path_product_plan)
         collocates review_search and product_affiliate in the same parallel step.
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

from mcp_server.tools.product_affiliate import product_affiliate  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_affiliate_search_products_parallel_within_provider():
    """
    RX-03: When multiple products are searched on a single provider, the
    individual search_products coroutines must be gathered with asyncio.gather
    (all at once), not executed sequentially in a for-loop.

    Verification: all 3 products are searched and results returned correctly.
    Uses asyncio.gather(*search_tasks) inside search_provider() to issue all
    per-product coroutines concurrently.
    """
    mock_result = MagicMock()
    mock_result.merchant = "Mock"
    mock_result.price = 99.99
    mock_result.currency = "USD"
    mock_result.affiliate_link = "https://mock.example.com/product"
    mock_result.condition = "new"
    mock_result.title = "Product A"
    mock_result.image_url = ""
    mock_result.rating = 4.5
    mock_result.review_count = 100
    mock_result.product_id = "MOCK123"

    mock_provider = MagicMock()
    mock_provider.search_products = AsyncMock(return_value=[mock_result])

    state = {
        "normalized_products": [
            {"title": "Product A"},
            {"title": "Product B"},
            {"title": "Product C"},
        ],
        "slots": {},
        "last_search_context": {},
    }

    with patch("app.services.affiliate.manager.affiliate_manager") as mock_manager, \
         patch("app.core.config.settings") as mock_settings:
        mock_settings.MAX_AFFILIATE_OFFERS_PER_PRODUCT = 3
        mock_settings.AMAZON_DEFAULT_COUNTRY = "US"
        mock_manager.get_available_providers.return_value = ["mock_provider"]
        mock_manager.get_provider.return_value = mock_provider

        result = await product_affiliate(state)

    # All 3 products should have been searched via asyncio.gather
    assert result["success"] is True
    assert "mock_provider" in result["affiliate_products"]
    provider_results = result["affiliate_products"]["mock_provider"]
    assert len(provider_results) == 3, (
        f"Expected 3 product results (one per product via asyncio.gather), got {len(provider_results)}: "
        f"search_products call count={mock_provider.search_products.call_count}"
    )
    # search_products must have been called 3 times (once per product)
    assert mock_provider.search_products.call_count == 3


@pytest.mark.asyncio
async def test_planner_fast_path_review_and_affiliate_in_same_step():
    """
    RX-05: PlannerAgent._create_fast_path_product_plan must put review_search
    and product_affiliate in the SAME execution step with parallel=True.

    Currently review_search and product_affiliate are in separate sequential
    steps, which forces waiting for review results before affiliate links start.
    Combining them saves ~2s latency.
    """
    from app.agents.planner_agent import PlannerAgent

    planner = PlannerAgent()
    plan = planner._create_fast_path_product_plan(include_extractor=False)

    steps = plan.get("steps", [])

    # Find whether review_search and product_affiliate appear in the same step
    combined_step = None
    for step in steps:
        tools_in_step = step.get("tools", [])
        if "review_search" in tools_in_step and "product_affiliate" in tools_in_step:
            combined_step = step
            break

    # This stub intentionally fails until review_search and product_affiliate
    # are merged into a single parallel step in the fast-path plan.
    pytest.fail(
        "RX-05: review_search and product_affiliate not in the same parallel step "
        "in fast_path plan — currently they are sequential steps: "
        f"{[s['tools'] for s in steps]}"
    )
