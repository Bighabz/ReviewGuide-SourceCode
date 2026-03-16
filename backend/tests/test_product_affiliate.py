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

    Verification: track the call order — gather fires all coroutines before any
    result is consumed, so a sequential implementation would differ in timing.
    This stub intentionally fails until the for-loop inside search_provider() is
    replaced with asyncio.gather on per-product coroutines.
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

        # NOTE: This stub fails unconditionally — the implementation still uses
        # a sequential for-loop inside search_provider(), not asyncio.gather
        # per product within a single provider call.
        pytest.fail(
            "RX-03: per-product parallelism not yet implemented — "
            "search_provider() uses a for loop instead of asyncio.gather "
            "over per-product coroutines"
        )


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
