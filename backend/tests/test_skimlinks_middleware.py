"""
Unit tests for Skimlinks post-processing middleware in product_affiliate.

Covers:
  AFFL-04: Skimlinks post-processing wraps qualifying URLs, skips excluded domains,
           and fails non-fatally. No provider file contains Skimlinks logic.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Environment bootstrap -- must happen before any app import
# ---------------------------------------------------------------------------
os.environ.setdefault("ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("LOG_ENABLED", "false")

from mcp_server.tools.product_affiliate import _apply_skimlinks_wrapping  # noqa: E402


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_middleware_wraps_qualifying_urls():
    """
    AFFL-04: Qualifying merchant URLs are wrapped by Skimlinks.
    A Best Buy URL should be replaced with a go.skimresources.com wrapped URL.
    """
    affiliate_products = {
        "serper_shopping": [
            {
                "product_name": "Sony WH-1000XM5",
                "offers": [
                    {
                        "url": "https://www.bestbuy.com/product/123",
                        "merchant": "Best Buy",
                        "source": "serper_shopping",
                    }
                ],
            }
        ]
    }

    wrapped_url = "https://go.skimresources.com?id=123&url=https://www.bestbuy.com/product/123"

    with patch("mcp_server.tools.product_affiliate.skimlinks_wrapper") as mock_wrapper, \
         patch("mcp_server.tools.product_affiliate.settings") as mock_settings:
        mock_wrapper.is_supported_domain.return_value = True
        mock_wrapper.wrap_url.return_value = wrapped_url
        mock_settings.SKIMLINKS_API_ENABLED = True

        result = await _apply_skimlinks_wrapping(affiliate_products, session_id="test-session")

    offer = result["serper_shopping"][0]["offers"][0]
    assert offer["url"] == wrapped_url
    assert offer["skimlinks_wrapped"] is True


@pytest.mark.asyncio
async def test_middleware_skips_excluded_domains():
    """
    AFFL-04: Amazon and eBay URLs are never wrapped by Skimlinks middleware.
    """
    affiliate_products = {
        "amazon": [
            {
                "product_name": "Headphones",
                "offers": [
                    {
                        "url": "https://amzn.to/abc123",
                        "merchant": "Amazon",
                        "source": "amazon",
                    }
                ],
            }
        ],
        "ebay": [
            {
                "product_name": "Speaker",
                "offers": [
                    {
                        "url": "https://www.ebay.com/itm/456",
                        "merchant": "eBay",
                        "source": "ebay",
                    }
                ],
            }
        ],
    }

    with patch("mcp_server.tools.product_affiliate.skimlinks_wrapper") as mock_wrapper, \
         patch("mcp_server.tools.product_affiliate.settings") as mock_settings:
        mock_wrapper.is_supported_domain.return_value = False
        mock_settings.SKIMLINKS_API_ENABLED = True

        result = await _apply_skimlinks_wrapping(affiliate_products)

    # Amazon URL unchanged
    amazon_offer = result["amazon"][0]["offers"][0]
    assert amazon_offer["url"] == "https://amzn.to/abc123"
    assert "skimlinks_wrapped" not in amazon_offer

    # eBay URL unchanged
    ebay_offer = result["ebay"][0]["offers"][0]
    assert ebay_offer["url"] == "https://www.ebay.com/itm/456"
    assert "skimlinks_wrapped" not in ebay_offer


@pytest.mark.asyncio
async def test_middleware_failure_is_nonfatal():
    """
    AFFL-04: Skimlinks wrapping failure does not propagate exceptions.
    Original affiliate_products dict is returned unchanged.
    """
    affiliate_products = {
        "serper_shopping": [
            {
                "product_name": "Sony WH-1000XM5",
                "offers": [
                    {
                        "url": "https://www.bestbuy.com/product/123",
                        "merchant": "Best Buy",
                        "source": "serper_shopping",
                    }
                ],
            }
        ]
    }

    with patch("mcp_server.tools.product_affiliate.skimlinks_wrapper") as mock_wrapper, \
         patch("mcp_server.tools.product_affiliate.settings") as mock_settings:
        mock_wrapper.is_supported_domain.side_effect = Exception("API timeout")
        mock_settings.SKIMLINKS_API_ENABLED = True

        result = await _apply_skimlinks_wrapping(affiliate_products)

    # Original data returned unchanged, no exception propagated
    offer = result["serper_shopping"][0]["offers"][0]
    assert offer["url"] == "https://www.bestbuy.com/product/123"
    assert "skimlinks_wrapped" not in offer


def test_no_provider_modifications():
    """
    AFFL-04: No provider file contains Skimlinks logic.
    Skimlinks wrapping happens only in post-processing, not inside providers.
    """
    providers_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "services", "affiliate", "providers"
    )

    provider_files = [
        f for f in os.listdir(providers_dir)
        if f.endswith(".py") and f != "__init__.py"
    ]

    assert len(provider_files) > 0, "No provider files found"

    for filename in provider_files:
        filepath = os.path.join(providers_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Check only non-comment code lines for Skimlinks references
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments and docstrings
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            line_lower = stripped.lower()
            assert "skimlinks" not in line_lower, (
                f"Provider file {filename}:{line_num} contains 'skimlinks' in code -- "
                f"wrapping should only happen in post-processing middleware"
            )
            assert "skimresources" not in line_lower, (
                f"Provider file {filename}:{line_num} contains 'skimresources' in code -- "
                f"wrapping should only happen in post-processing middleware"
            )
