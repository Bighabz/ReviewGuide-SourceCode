# CJ Affiliate Integration & Curated Browse Content

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Commission Junction as an affiliate provider with full API infrastructure, populate browse pages with curated Amazon affiliate picks, and create legal pages.

**Architecture:** CJ provider plugs into the existing `AffiliateProviderRegistry` decorator system — auto-discovered, config-driven, with Redis caching. Frontend gets a new `curatedLinks.ts` data file rendered as "Editor's Picks" cards on browse category pages. Four new browse categories added. Privacy and affiliate disclosure get dedicated routes.

**Tech Stack:** FastAPI, httpx, xml.etree.ElementTree (CJ REST returns XML), Redis, Next.js 14, TypeScript, Tailwind CSS

---

## Phase 1: Backend — CJ Provider Infrastructure

### Task 1: Add CJ config settings

**Files:**
- Modify: `backend/app/core/config.py` (after line ~287, near other affiliate placeholders)

**Step 1: Add CJ settings to the Settings class**

Add these fields after the Target Affiliate block (~line 287):

```python
# Commission Junction (CJ) Affiliate
CJ_API_ENABLED: bool = Field(default=False, description="Enable CJ Product Search API")
CJ_API_KEY: str = Field(default="", description="CJ personal access token (Bearer token)")
CJ_WEBSITE_ID: str = Field(default="", description="CJ publisher website ID (PID)")
CJ_ADVERTISER_IDS: str = Field(
    default="joined",
    description="CJ advertiser IDs: 'joined' for all, or comma-separated CIDs"
)
CJ_API_TIMEOUT: float = Field(default=10.0, description="CJ API request timeout in seconds")
CJ_CACHE_TTL: int = Field(default=28800, description="CJ search cache TTL in seconds (8 hours)")
CJ_MAX_RESULTS: int = Field(default=20, description="Max CJ products per search request")
```

**Step 2: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat: add CJ affiliate configuration settings"
```

---

### Task 2: Create CJ affiliate provider

**Files:**
- Create: `backend/app/services/affiliate/providers/cj_provider.py`
- Test: `backend/tests/test_cj_provider.py`

**Step 1: Write the failing test**

```python
"""Tests for CJ affiliate provider"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.affiliate.providers.cj_provider import CJAffiliateProvider

# Sample CJ XML response matching their real API format
SAMPLE_CJ_XML = """<?xml version="1.0" encoding="UTF-8"?>
<cj-api>
  <products total-matched="2" records-returned="2" page-number="1">
    <product>
      <ad-id>12345</ad-id>
      <advertiser-id>5167350</advertiser-id>
      <advertiser-name>Apple Vacations</advertiser-name>
      <buy-url>https://www.anrdoezrs.net/click-101568669-5167350?url=https%3A%2F%2Fexample.com%2Fproduct1</buy-url>
      <description>All-inclusive Caribbean vacation package</description>
      <image-url>https://images.example.com/vacation1.jpg</image-url>
      <in-stock>true</in-stock>
      <name>Caribbean Beach Resort Package</name>
      <price>1299.99</price>
      <currency>USD</currency>
      <sale-price>999.99</sale-price>
      <sku>AV-CARIB-001</sku>
      <manufacturer-name>Apple Vacations</manufacturer-name>
    </product>
    <product>
      <ad-id>12346</ad-id>
      <advertiser-id>5167350</advertiser-id>
      <advertiser-name>Apple Vacations</advertiser-name>
      <buy-url>https://www.anrdoezrs.net/click-101568669-5167350?url=https%3A%2F%2Fexample.com%2Fproduct2</buy-url>
      <description>Mexico all-inclusive resort deal</description>
      <image-url>https://images.example.com/vacation2.jpg</image-url>
      <in-stock>true</in-stock>
      <name>Cancun Resort All-Inclusive</name>
      <price>1599.00</price>
      <currency>USD</currency>
      <sale-price></sale-price>
      <sku>AV-CANCUN-002</sku>
      <manufacturer-name>Apple Vacations</manufacturer-name>
    </product>
  </products>
</cj-api>
"""

EMPTY_CJ_XML = """<?xml version="1.0" encoding="UTF-8"?>
<cj-api>
  <products total-matched="0" records-returned="0" page-number="1">
  </products>
</cj-api>
"""


@pytest.fixture
def cj_provider():
    return CJAffiliateProvider(
        api_key="test-key",
        website_id="101568669",
    )


class TestCJProviderName:
    def test_provider_name(self, cj_provider):
        assert cj_provider.get_provider_name() == "CJ"


class TestCJXMLParsing:
    def test_parse_products_from_xml(self, cj_provider):
        products = cj_provider._parse_xml_response(SAMPLE_CJ_XML)
        assert len(products) == 2

        first = products[0]
        assert first.title == "Caribbean Beach Resort Package"
        assert first.price == 999.99  # sale_price preferred over price
        assert first.currency == "USD"
        assert first.merchant == "Apple Vacations"
        assert "anrdoezrs.net" in first.affiliate_link
        assert first.image_url == "https://images.example.com/vacation1.jpg"
        assert first.product_id == "AV-CARIB-001"

    def test_parse_empty_response(self, cj_provider):
        products = cj_provider._parse_xml_response(EMPTY_CJ_XML)
        assert products == []

    def test_fallback_to_regular_price(self, cj_provider):
        """When sale-price is empty, use regular price"""
        products = cj_provider._parse_xml_response(SAMPLE_CJ_XML)
        second = products[1]
        assert second.price == 1599.00  # no sale price, uses regular


class TestCJSearchProducts:
    @pytest.mark.asyncio
    async def test_search_calls_api(self, cj_provider):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = SAMPLE_CJ_XML

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            products = await cj_provider.search_products("caribbean vacation", limit=5)

        assert len(products) == 2
        assert products[0].title == "Caribbean Beach Resort Package"

    @pytest.mark.asyncio
    async def test_search_handles_api_error(self, cj_provider):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            products = await cj_provider.search_products("test query")

        assert products == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, cj_provider):
        import httpx
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("timeout")):
            products = await cj_provider.search_products("test query")

        assert products == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_cj_provider.py -v`
Expected: FAIL — module not found

**Step 3: Write the CJ provider**

Create `backend/app/services/affiliate/providers/cj_provider.py`:

```python
"""
Commission Junction (CJ) Affiliate Provider
Searches CJ Product Catalog via REST API (XML response).
Auto-registered via the AffiliateProviderRegistry decorator.
"""
import json
import hashlib
import xml.etree.ElementTree as ET
from typing import List, Optional

import httpx

from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.core.redis_client import redis_get_with_retry, redis_set_with_retry
from app.services.affiliate.base import BaseAffiliateProvider, AffiliateProduct
from app.services.affiliate.registry import AffiliateProviderRegistry

logger = get_logger(__name__)

CJ_API_BASE = "https://product-search.api.cj.com/v2/product-search"


@AffiliateProviderRegistry.register(
    "cj",
    required_env_vars=["CJ_API_KEY", "CJ_WEBSITE_ID"],
    optional_env_vars=["CJ_ADVERTISER_IDS"],
)
class CJAffiliateProvider(BaseAffiliateProvider):
    """CJ Product Search API provider"""

    def __init__(
        self,
        api_key: str = "",
        website_id: str = "",
    ):
        self.api_key = api_key or settings.CJ_API_KEY
        self.website_id = website_id or settings.CJ_WEBSITE_ID

    def get_provider_name(self) -> str:
        return "CJ"

    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        advertiser_ids: Optional[str] = None,
    ) -> List[AffiliateProduct]:
        """Search CJ product catalog. Checks Redis cache first."""
        adv_ids = advertiser_ids or settings.CJ_ADVERTISER_IDS
        cache_key = self._build_cache_key(query, adv_ids, min_price, max_price, limit)

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached is not None:
            logger.info(f"CJ cache hit for '{query}' ({len(cached)} products)")
            return cached

        # Call API
        products = await self._call_api(
            query=query,
            advertiser_ids=adv_ids,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
        )

        # Cache results (even empty — prevents hammering for bad queries)
        await self._set_cached(cache_key, products)

        return products

    async def _call_api(
        self,
        query: str,
        advertiser_ids: str,
        min_price: Optional[float],
        max_price: Optional[float],
        limit: int,
    ) -> List[AffiliateProduct]:
        """Make HTTP request to CJ Product Search REST API"""
        params = {
            "website-id": self.website_id,
            "keywords": query,
            "advertiser-ids": advertiser_ids,
            "records-per-page": str(min(limit, settings.CJ_MAX_RESULTS)),
        }

        if min_price is not None:
            params["low-price"] = str(min_price)
        if max_price is not None:
            params["high-price"] = str(max_price)

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=settings.CJ_API_TIMEOUT) as client:
                response = await client.get(CJ_API_BASE, params=params, headers=headers)

            if response.status_code != 200:
                logger.error(f"CJ API returned {response.status_code}: {response.text[:200]}")
                return []

            return self._parse_xml_response(response.text)

        except httpx.TimeoutException:
            logger.error(f"CJ API timeout for query '{query}'")
            return []
        except Exception as e:
            logger.error(f"CJ API error: {e}", exc_info=True)
            return []

    def _parse_xml_response(self, xml_text: str) -> List[AffiliateProduct]:
        """Parse CJ XML response into AffiliateProduct list"""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"CJ XML parse error: {e}")
            return []

        products = []
        for product_el in root.iter("product"):
            try:
                # Prefer sale-price if present and non-empty
                sale_price_text = (product_el.findtext("sale-price") or "").strip()
                regular_price_text = (product_el.findtext("price") or "0").strip()

                if sale_price_text:
                    price = float(sale_price_text)
                else:
                    price = float(regular_price_text) if regular_price_text else 0.0

                products.append(
                    AffiliateProduct(
                        product_id=product_el.findtext("sku") or product_el.findtext("ad-id") or "",
                        title=product_el.findtext("name") or "",
                        price=price,
                        currency=product_el.findtext("currency") or "USD",
                        affiliate_link=product_el.findtext("buy-url") or "",
                        merchant=product_el.findtext("advertiser-name") or "CJ",
                        image_url=product_el.findtext("image-url"),
                        condition="new",
                        availability=(product_el.findtext("in-stock") or "").lower() == "true",
                    )
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed CJ product: {e}")
                continue

        return products

    # ── Cache helpers ────────────────────────────────────────────

    def _build_cache_key(
        self, query: str, advertiser_ids: str, min_price: Optional[float],
        max_price: Optional[float], limit: int,
    ) -> str:
        raw = f"{query}|{advertiser_ids}|{min_price}|{max_price}|{limit}"
        digest = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"cj:search:{digest}"

    async def _get_cached(self, key: str) -> Optional[List[AffiliateProduct]]:
        try:
            data = await redis_get_with_retry(key)
            if data is None:
                return None
            items = json.loads(data)
            return [AffiliateProduct(**item) for item in items]
        except Exception as e:
            logger.warning(f"CJ cache read error: {e}")
            return None

    async def _set_cached(self, key: str, products: List[AffiliateProduct]) -> None:
        try:
            data = json.dumps([p.__dict__ for p in products])
            await redis_set_with_retry(key, data, ex=settings.CJ_CACHE_TTL)
        except Exception as e:
            logger.warning(f"CJ cache write error: {e}")

    # ── Required abstract methods ────────────────────────────────

    async def generate_affiliate_link(
        self, product_id: str, campaign_id: Optional[str] = None,
        tracking_id: Optional[str] = None,
    ) -> str:
        # CJ buy-urls are already complete affiliate links
        return f"https://www.anrdoezrs.net/click-{self.website_id}-{product_id}"

    async def check_link_health(self, affiliate_link: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
                resp = await client.head(affiliate_link)
                return resp.status_code in (200, 301, 302)
        except Exception:
            return False
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_cj_provider.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/affiliate/providers/cj_provider.py backend/tests/test_cj_provider.py
git commit -m "feat: add CJ affiliate provider with XML parsing and Redis cache"
```

---

### Task 3: Register CJ provider in loader

**Files:**
- Modify: `backend/app/services/affiliate/loader.py` (~line 55, `_PROVIDER_INIT_MAP`)

**Step 1: Add CJ to the init map**

Add to `_PROVIDER_INIT_MAP` dict:

```python
"cj": lambda: {
    "api_key": settings.CJ_API_KEY,
    "website_id": settings.CJ_WEBSITE_ID,
},
```

**Step 2: Commit**

```bash
git add backend/app/services/affiliate/loader.py
git commit -m "feat: register CJ provider in affiliate loader init map"
```

---

### Task 4: Add CJ search endpoint (optional API route)

**Files:**
- Modify: `backend/app/api/v1/affiliate.py`

**Step 1: Add a CJ search endpoint**

Add after the existing `/v1/affiliate/click` and `/v1/affiliate/event` endpoints:

```python
from pydantic import BaseModel
from typing import Optional, List

class CJSearchRequest(BaseModel):
    keywords: str
    advertiser_ids: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = 10

class CJProductResponse(BaseModel):
    title: str
    price: float
    currency: str
    buy_url: str
    merchant: str
    image_url: Optional[str] = None
    product_id: str = ""

class CJSearchResponse(BaseModel):
    results: List[CJProductResponse]
    count: int
    cached: bool = False

@router.post("/cj/search", response_model=CJSearchResponse)
async def cj_search(req: CJSearchRequest):
    """Search CJ product catalog"""
    from app.services.affiliate.manager import affiliate_manager

    provider = affiliate_manager.get_provider("cj")
    if not provider:
        return CJSearchResponse(results=[], count=0)

    products = await provider.search_products(
        query=req.keywords,
        min_price=req.min_price,
        max_price=req.max_price,
        limit=req.limit,
        advertiser_ids=req.advertiser_ids,
    )

    results = [
        CJProductResponse(
            title=p.title,
            price=p.price,
            currency=p.currency,
            buy_url=p.affiliate_link,
            merchant=p.merchant,
            image_url=p.image_url,
            product_id=p.product_id,
        )
        for p in products
    ]

    return CJSearchResponse(results=results, count=len(results))
```

**Step 2: Commit**

```bash
git add backend/app/api/v1/affiliate.py
git commit -m "feat: add CJ product search API endpoint"
```

---

## Phase 2: Frontend — Curated Browse Content

### Task 5: Create curated affiliate links data file

**Files:**
- Create: `frontend/lib/curatedLinks.ts`

**Step 1: Create the data file**

This maps category slugs to topics, each with a display title and Amazon affiliate URLs.

```typescript
export interface CuratedTopic {
  title: string
  links: string[]
}

export interface CuratedCategory {
  [slug: string]: CuratedTopic[]
}

export const curatedLinks: CuratedCategory = {
  electronics: [
    {
      title: 'Best Noise-Cancelling Headphones',
      links: [
        'https://amzn.to/4cg2c2g',
        'https://amzn.to/46sYSNy',
        'https://amzn.to/40hVQbz',
        'https://amzn.to/4qWWrtW',
        'https://amzn.to/4kZCHVl',
      ],
    },
    {
      title: 'Top Laptops for Students in 2026',
      links: [
        'https://amzn.to/4tSpXE1',
        'https://amzn.to/3OtNdIf',
        'https://amzn.to/40srrqS',
        'https://amzn.to/3ZTVpE2',
        'https://amzn.to/4kUxiPj',
      ],
    },
    {
      title: 'Best Budget Smartphones Under $400',
      links: [
        'https://amzn.to/40wHa8k',
        'https://amzn.to/4baYypf',
        'https://amzn.to/4s7D16v',
        'https://amzn.to/4ucdsmS',
        'https://amzn.to/4aAkUjS',
      ],
    },
    {
      title: 'Best Bluetooth Speakers',
      links: [
        'https://amzn.to/40tnceG',
        'https://amzn.to/4cW8fcm',
        'https://amzn.to/3OE2Rkf',
        'https://amzn.to/4aUTEeI',
        'https://amzn.to/46ZowJS',
        'https://amzn.to/4sflr0x',
      ],
    },
  ],
  'home-appliances': [
    {
      title: 'Best Robot Vacuums for Pet Hair',
      links: [
        'https://amzn.to/4kZU08C',
        'https://amzn.to/3ZYKrNt',
        'https://amzn.to/4cK6Jdq',
        'https://amzn.to/4sxhxAv',
        'https://amzn.to/46qmUst',
      ],
    },
    {
      title: 'Best Compact Washing Machines',
      links: [
        'https://amzn.to/4u2A4Gq',
        'https://amzn.to/4kXfNxK',
        'https://amzn.to/4qRmimV',
        'https://amzn.to/4siBCKJ',
        'https://amzn.to/4sel4Dv',
      ],
    },
    {
      title: 'Dyson vs Shark: Which Vacuum Wins?',
      links: [
        'https://amzn.to/4r3yGk3',
        'https://amzn.to/4s43SQQ',
        'https://amzn.to/4aC3lQt',
        'https://amzn.to/46te6SN',
        'https://amzn.to/4kZFii3',
      ],
    },
    {
      title: 'Best Espresso Machines Under $500',
      links: [
        'https://amzn.to/46NZBZZ',
        'https://amzn.to/4bgoDlV',
        'https://amzn.to/4kVjGTL',
        'https://amzn.to/4rxiqbW',
        'https://amzn.to/4b8KI6O',
      ],
    },
  ],
  'health-wellness': [
    {
      title: 'Best Standing Desks for Back Pain',
      links: [
        'https://amzn.to/4rHjBWv',
        'https://amzn.to/3ZTY3ts',
        'https://amzn.to/3MTqx3r',
        'https://amzn.to/3ZYlH84',
        'https://amzn.to/3MIFHsr',
      ],
    },
    {
      title: 'Best Supplements for Energy and Focus',
      links: [
        'https://amzn.to/4aSaSto',
        'https://amzn.to/4u2BIrA',
        'https://amzn.to/3ZTq1FL',
        'https://amzn.to/4cgr1el',
        'https://amzn.to/4kXo0lz',
      ],
    },
    {
      title: 'Theragun vs Hypervolt: Which Massage Gun Is Better?',
      links: [
        'https://amzn.to/4kZ7fX1',
        'https://amzn.to/4l2yxMq',
        'https://amzn.to/4tXXqNg',
        'https://amzn.to/4qWfnsA',
        'https://amzn.to/4l0t7kX',
      ],
    },
    {
      title: 'Best Fitness Trackers Under $100',
      links: [
        'https://amzn.to/3ZXGdpy',
        'https://amzn.to/4aRMcBb',
        'https://amzn.to/4scnhiz',
        'https://amzn.to/4tWNnb3',
        'https://amzn.to/46u0M0j',
      ],
    },
    {
      title: 'Top-Rated Supplements for Weight Loss',
      links: [
        'https://amzn.to/4baXYIa',
        'https://amzn.to/46OSVuD',
        'https://amzn.to/3OM6Yuw',
        'https://amzn.to/4s88HZr',
        'https://amzn.to/3OBZXg0',
        'https://amzn.to/4cPmL5G',
      ],
    },
    {
      title: 'Best Supplements for Menopause Support',
      links: [
        'https://amzn.to/4sdlxpu',
        'https://amzn.to/46P16aj',
        'https://amzn.to/46uZPVx',
        'https://amzn.to/4qY1JVW',
      ],
    },
  ],
  'outdoor-fitness': [
    {
      title: 'Best Hiking Boots for Beginners',
      links: [
        'https://amzn.to/4aIxo7G',
        'https://amzn.to/4aU6jP2',
        'https://amzn.to/3MvKUUr',
        'https://amzn.to/3OAEGDf',
        'https://amzn.to/3P2NBNS',
      ],
    },
    {
      title: 'Best Shoes for Flat Feet',
      links: [
        'https://amzn.to/3P4MahS',
        'https://amzn.to/3MvLcdZ',
        'https://amzn.to/4si597f',
        'https://amzn.to/47ebcRY',
        'https://amzn.to/3ZYOMQL',
      ],
    },
    {
      title: 'Garmin vs Apple Watch for Fitness',
      links: [
        'https://amzn.to/46rIc94',
        'https://amzn.to/4tXZNQ5',
        'https://amzn.to/4rFsj7D',
        'https://amzn.to/4l6ws1R',
        'https://amzn.to/4tWPfAB',
      ],
    },
    {
      title: 'Best Home Treadmills Under $1,000',
      links: [
        'https://amzn.to/4aC70hb',
        'https://amzn.to/4siFxXX',
        'https://amzn.to/46pe8uP',
        'https://amzn.to/46VPrGw',
        'https://amzn.to/4qX2ZJ2',
      ],
    },
  ],
  'fashion-style': [
    {
      title: 'Best White Sneakers for Everyday Wear',
      links: [
        'https://amzn.to/3ZXKuJu',
        'https://amzn.to/476uRmL',
        'https://amzn.to/4cguOZg',
        'https://amzn.to/4rE2h4J',
        'https://amzn.to/4qX1Hh0',
      ],
    },
    {
      title: 'Best Affordable Jewelry That Won\'t Tarnish',
      links: [
        'https://amzn.to/3MKtN1c',
        'https://amzn.to/4rHcIo2',
        'https://amzn.to/46vziY9',
        'https://amzn.to/4l6BoUr',
        'https://amzn.to/4aXQ2Jb',
      ],
    },
    {
      title: 'Best Streetwear Brands in 2026',
      links: [
        'https://amzn.to/3OyKi0U',
        'https://amzn.to/3ZYtGly',
        'https://amzn.to/40wRNYM',
        'https://amzn.to/4shzrHk',
        'https://amzn.to/4sezXWl',
      ],
    },
    {
      title: 'Best Watches Under $500',
      links: [
        'https://amzn.to/4aN66gE',
        'https://amzn.to/3N5VIsv',
        'https://amzn.to/4qX2XAK',
        'https://amzn.to/4aXQTJN',
        'https://amzn.to/4qU4Tdh',
      ],
    },
  ],
  'smart-home': [
    {
      title: 'Best Alexa-Compatible Smart Home Gadgets',
      links: [
        'https://amzn.to/4l2GelM',
        'https://amzn.to/4r3IWsz',
        'https://amzn.to/3OPqRRr',
        'https://amzn.to/46Y9EeO',
        'https://amzn.to/4sg5N5d',
        'https://amzn.to/4qTKyov',
        'https://amzn.to/3P2VD9u',
      ],
    },
  ],
  'kids-toys': [
    {
      title: 'Hottest Toys of 2026',
      links: [
        'https://amzn.to/4u2gfis',
        'https://amzn.to/4qX4iHM',
        'https://amzn.to/4rzKtHH',
        'https://amzn.to/3ZXSWZk',
        'https://amzn.to/4cgFw1Y',
        'https://amzn.to/4r3JVcf',
        'https://amzn.to/4sdnEd0',
        'https://amzn.to/3MwI5CB',
      ],
    },
  ],
  baby: [
    {
      title: 'Baby Essentials Every New Parent Needs',
      links: [
        'https://amzn.to/40y4ZfW',
        'https://amzn.to/46pFVLM',
        'https://amzn.to/4kTSBjM',
        'https://amzn.to/4kU8p68',
        'https://amzn.to/4cOOKT6',
        'https://amzn.to/4l08rtk',
        'https://amzn.to/4qTLWHL',
      ],
    },
  ],
  'big-tall': [
    {
      title: 'Best Big & Tall Clothing for Men',
      links: [
        'https://amzn.to/4cbMKnN',
        'https://amzn.to/3MwIkO1',
        'https://amzn.to/401kjl9',
        'https://amzn.to/4bcefMY',
        'https://amzn.to/4seDT9z',
        'https://amzn.to/4aEwmLq',
      ],
    },
  ],
}
```

**Step 2: Commit**

```bash
git add frontend/lib/curatedLinks.ts
git commit -m "feat: add curated Amazon affiliate links data for all categories"
```

---

### Task 6: Update categoryConfig with new categories and polished queries

**Files:**
- Modify: `frontend/lib/categoryConfig.ts`

**Step 1: Update existing query text and add new categories**

Replace the entire `categories` array with updated entries. Changes:
- Existing queries polished (cleaner wording, no user rough-draft text)
- 4 new categories added: Smart Home, Kids & Toys, Baby, Big & Tall
- Each new category gets 4 queries (first matches curated topic, rest are AI-only)

The updated categories array should be:

```typescript
export const categories: BrowseCategory[] = [
  {
    slug: 'travel',
    name: 'Travel',
    tagline: 'Flights, hotels & destinations worth the trip',
    image: '/images/browse/travel.jpg',
    icon: 'Plane',
    queries: [
      'Top all-inclusive resorts in the Caribbean',
      'When to book flights to Japan for cheap',
      'Airbnb vs hotels for family vacations',
      'Great travel backpacks under $100',
    ],
  },
  {
    slug: 'electronics',
    name: 'Electronics',
    tagline: 'Researched, rated & ready to buy',
    image: '/images/browse/electronics.jpg',
    icon: 'Laptop',
    queries: [
      'Best noise-cancelling headphones',
      'Top laptops for students in 2026',
      'Best budget smartphones under $400',
      'Best Bluetooth speakers',
    ],
  },
  {
    slug: 'home-appliances',
    name: 'Home Appliances',
    tagline: 'The machines that make your home work',
    image: '/images/browse/home-appliances.jpg',
    icon: 'Home',
    queries: [
      'Best robot vacuums for pet hair',
      'Best compact washing machines',
      'Dyson vs Shark: which vacuum wins?',
      'Best espresso machines under $500',
    ],
  },
  {
    slug: 'health-wellness',
    name: 'Health & Wellness',
    tagline: 'Gear and supplements backed by research',
    image: '/images/browse/health-wellness.jpg',
    icon: 'Heart',
    queries: [
      'Best standing desks for back pain',
      'Best supplements for energy and focus',
      'Theragun vs Hypervolt: which massage gun is better?',
      'Best fitness trackers under $100',
    ],
  },
  {
    slug: 'outdoor-fitness',
    name: 'Outdoor & Fitness',
    tagline: 'Built for the trail, the road & the gym',
    image: '/images/browse/outdoor-fitness.jpg',
    icon: 'Mountain',
    queries: [
      'Best hiking boots for beginners',
      'Best shoes for flat feet',
      'Garmin vs Apple Watch for fitness',
      'Best home treadmills under $1,000',
    ],
  },
  {
    slug: 'fashion-style',
    name: 'Fashion & Style',
    tagline: 'Sneakers, watches & wardrobe essentials reviewed',
    image: '/images/browse/fashion-style.jpg',
    icon: 'Shirt',
    queries: [
      'Best white sneakers for everyday wear',
      'Best affordable jewelry that won\'t tarnish',
      'Best streetwear brands in 2026',
      'Best watches under $500',
    ],
  },
  {
    slug: 'smart-home',
    name: 'Smart Home',
    tagline: 'Voice assistants, smart displays & connected living',
    image: '/images/browse/smart-home.jpg',
    icon: 'Speaker',
    queries: [
      'Best Alexa-compatible smart home gadgets',
      'Best smart plugs and switches',
      'Best smart doorbell cameras',
      'Best smart lighting systems',
    ],
  },
  {
    slug: 'kids-toys',
    name: 'Kids & Toys',
    tagline: 'Top-rated picks for every age and stage',
    image: '/images/browse/kids-toys.jpg',
    icon: 'Gamepad2',
    queries: [
      'Hottest toys of 2026',
      'Best educational toys for toddlers',
      'Best STEM toys for kids',
      'Best outdoor toys for summer',
    ],
  },
  {
    slug: 'baby',
    name: 'Baby',
    tagline: 'Essentials and gear for new parents',
    image: '/images/browse/baby.jpg',
    icon: 'Baby',
    queries: [
      'Baby essentials every new parent needs',
      'Best baby monitors',
      'Best strollers for city living',
      'Best baby car seats in 2026',
    ],
  },
  {
    slug: 'big-tall',
    name: 'Big & Tall',
    tagline: 'Clothing and gear that actually fits',
    image: '/images/browse/big-tall.jpg',
    icon: 'PersonStanding',
    queries: [
      'Best big & tall clothing for men',
      'Best big & tall dress shirts',
      'Best jeans for big and tall guys',
      'Best activewear for larger builds',
    ],
  },
]
```

**Step 2: Commit**

```bash
git add frontend/lib/categoryConfig.ts
git commit -m "feat: update category queries and add 4 new browse categories"
```

---

### Task 7: Add curated picks section to category pages

**Files:**
- Modify: `frontend/app/browse/[category]/page.tsx`

**Step 1: Import curatedLinks and add Editor's Picks section**

Add import at top:

```typescript
import { curatedLinks } from '@/lib/curatedLinks'
```

After the "Popular Questions" section and before "Explore Other Categories", add a new section. The section renders each curated topic as a card with numbered Amazon pick links (opens in new tab).

Each link renders as a small pill button: "Pick 1", "Pick 2", etc. with an external-link icon. The topic title doubles as a clickable link to start an AI chat on that topic.

**Key UI spec:**
- Section title: "Editor's Picks"
- Each topic is a card with: topic title (clickable → AI chat), numbered Amazon link buttons below
- Links styled as small outline pills: `border border-[var(--border)] rounded-lg px-3 py-1.5`
- Amazon attribution: small "Available on Amazon" text per card
- Only show section if category has curated links

**Step 2: Commit**

```bash
git add frontend/app/browse/[category]/page.tsx
git commit -m "feat: add Editor's Picks curated affiliate section to category pages"
```

---

### Task 8: Also show curated picks on main browse page cards

**Files:**
- Modify: `frontend/app/browse/page.tsx`

**Step 1: Add curated link count badges to category cards**

Import `curatedLinks` and show a small "N picks" badge on categories that have curated content. This signals to users that there are direct shopping links available.

Add below each category's query chips section, a small count line like:
```
✦ 5 editor's picks available
```

Only display for categories that have entries in `curatedLinks`.

**Step 2: Commit**

```bash
git add frontend/app/browse/page.tsx
git commit -m "feat: show curated picks count on browse page category cards"
```

---

## Phase 3: Legal Pages & Footer

### Task 9: Create privacy policy page

**Files:**
- Create: `frontend/app/privacy/page.tsx`

**Step 1: Create the page**

Server component with the privacy policy text provided by the user. Styled with the editorial theme: `font-serif` headings, `var(--text)` colors, proper spacing. Include the AI Content Disclosure section.

Content sections:
1. Privacy Policy header with effective date
2. Information We Collect
3. How We Use Information
4. Cookies and Tracking
5. Third-Party Links
6. Data Security
7. Changes
8. Contact: mike@reviewguide.ai
9. AI Content Disclosure

**Step 2: Commit**

```bash
git add frontend/app/privacy/page.tsx
git commit -m "feat: add privacy policy page with AI content disclosure"
```

---

### Task 10: Create affiliate disclosure page and update footer

**Files:**
- Create: `frontend/app/affiliate-disclosure/page.tsx`
- Modify: `frontend/lib/constants.ts` (FOOTER_LINKS)

**Step 1: Create the affiliate disclosure page**

Content sections:
1. Affiliate Disclosure header
2. Amazon Associates disclosure
3. Other affiliate programs mention
4. No additional cost to users
5. Editorial independence statement

**Step 2: Update FOOTER_LINKS in constants.ts**

Change the `href: '#'` placeholders to real routes:

```typescript
export const FOOTER_LINKS = [
  { label: 'About', href: '#' },
  { label: 'Privacy', href: '/privacy' },
  { label: 'Affiliate Disclosure', href: '/affiliate-disclosure', desktopOnly: true },
  { label: 'Contact', href: 'mailto:mike@reviewguide.ai' },
] as const
```

**Step 3: Commit**

```bash
git add frontend/app/affiliate-disclosure/page.tsx frontend/lib/constants.ts
git commit -m "feat: add affiliate disclosure page and wire up footer links"
```

---

## Post-Implementation Notes

### CJ Environment Variables to Set on Railway

```
CJ_API_ENABLED=true
CJ_API_KEY=<your-key>
CJ_WEBSITE_ID=101568669
CJ_ADVERTISER_IDS=joined
```

**Do NOT commit the API key.** Set it only as a Railway environment variable.

### CJ Advertiser Expansion

Current advertisers (Apple Vacations + Audiobooks) won't cover most categories. To expand CJ coverage:

1. Log into CJ dashboard → Advertisers tab
2. Apply to programs by category:
   - **Electronics:** Best Buy, Dell, HP, Samsung
   - **Home:** Target, Wayfair, Overstock
   - **Fitness:** Nike, Under Armour, REI
   - **Fashion:** Nordstrom, Macy's, ASOS
3. Once approved, products automatically appear in API searches (no code change needed — `advertiser-ids=joined` covers all)

### Missing Data

- One Amazon link is truncated: "Supplements to support menopause" last link is `https://amzn.to/4` — needs the full URL
- New category images needed in `/public/images/browse/`: `smart-home.jpg`, `kids-toys.jpg`, `baby.jpg`, `big-tall.jpg`
