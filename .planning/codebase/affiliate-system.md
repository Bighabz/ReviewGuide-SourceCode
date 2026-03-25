# Affiliate Provider System Deep Dive

**Analysis Date:** 2026-03-25

## Overview

The affiliate provider system is a plugin-based architecture for fetching product data and affiliate links from multiple retail networks. It uses a decorator-based registry pattern with auto-discovery, environment-variable-gated activation, and automatic fallback between providers.

## Architecture Diagram

```
product_affiliate tool (MCP)
        |
        v
AffiliateManager (singleton)
   |-- register_provider()
   |-- search_products() -> try primary, fallback to others
   |-- search_amazon_products() -> Amazon-specific with country_code
   |-- generate_affiliate_link()
   |-- check_link_health()
        |
        v
AffiliateProviderRegistry (class-level registry)
   |-- @register("name", required_env_vars=[...]) decorator
   |-- get_provider_class(name) -> Type[BaseAffiliateProvider]
   |-- list_providers() -> ["ebay", "amazon", "cj"]
        |
        v
loader.py / setup_affiliate_providers(manager)
   |-- _auto_import_providers() -> scans providers/*.py
   |-- _check_env_vars(required) -> validates env vars
   |-- _PROVIDER_INIT_MAP -> per-provider constructor kwargs
   |-- instantiates and registers each provider with manager
```

## Core Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/services/affiliate/base.py` | `BaseAffiliateProvider` ABC + `AffiliateProduct` dataclass | ~94 |
| `backend/app/services/affiliate/registry.py` | `AffiliateProviderRegistry` with `@register` decorator | ~68 |
| `backend/app/services/affiliate/loader.py` | Auto-discovery, env var validation, provider instantiation | ~108 |
| `backend/app/services/affiliate/manager.py` | `AffiliateManager` orchestrator + `MockAffiliateProvider` | ~461 |
| `backend/app/services/affiliate/providers/amazon_provider.py` | Amazon Associates PA-API + mock mode | ~700+ |
| `backend/app/services/affiliate/providers/ebay_provider.py` | eBay Partner Network Browse API + mock mode | ~500+ |
| `backend/app/services/affiliate/providers/cj_provider.py` | Commission Junction XML API + Redis cache | ~300+ |
| `backend/app/services/affiliate/providers/curated_amazon_links.py` | Static curated Amazon affiliate links (120+ products) | ~900+ |

## BaseAffiliateProvider Interface

**File:** `backend/app/services/affiliate/base.py`

```python
@dataclass
class AffiliateProduct:
    product_id: str
    title: str
    price: float
    currency: str
    affiliate_link: str
    merchant: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    condition: str = "new"
    shipping_cost: Optional[float] = None
    availability: bool = True
    source_url: Optional[str] = None

class BaseAffiliateProvider(ABC):
    @abstractmethod
    async def search_products(self, query, category, brand, min_price, max_price, limit) -> List[AffiliateProduct]
    @abstractmethod
    async def generate_affiliate_link(self, product_id, campaign_id, tracking_id) -> str
    @abstractmethod
    async def check_link_health(self, affiliate_link) -> bool
    @abstractmethod
    def get_provider_name(self) -> str
```

All providers MUST implement these four methods. The `AffiliateProduct` dataclass is the standardized output format used across the system.

## AffiliateProviderRegistry

**File:** `backend/app/services/affiliate/registry.py`

**Pattern:** Class-level `_providers` dict populated by `@register` decorators on provider classes.

```python
@AffiliateProviderRegistry.register(
    "cj",
    required_env_vars=["CJ_API_KEY", "CJ_WEBSITE_ID"],
)
class CJAffiliateProvider(BaseAffiliateProvider):
    ...
```

**Key Methods:**
- `register(name, required_env_vars, optional_env_vars)` -- Decorator that stores class + env var metadata
- `get_provider_class(name)` -- Returns the registered class (not instance)
- `list_providers()` -- Returns all registered provider names
- `list_provider_info()` -- Returns name -> {required_env_vars, optional_env_vars} mapping

## Auto-Discovery Loader

**File:** `backend/app/services/affiliate/loader.py`

**Flow:**
1. `setup_affiliate_providers(manager)` is called from `AffiliateManager._initialize_providers()`
2. `_auto_import_providers()` scans `backend/app/services/affiliate/providers/` directory
3. For each `*.py` file (except `__init__`), dynamically imports via `importlib.import_module("app.services.affiliate.providers.{name}")`
4. Import triggers `@register` decorator, populating the registry
5. For each registered provider, validates required env vars via `_check_env_vars()`
6. Uses `_PROVIDER_INIT_MAP` to get constructor kwargs per provider
7. Instantiates and calls `manager.register_provider(name, instance)`

**Provider Init Map:**
```python
_PROVIDER_INIT_MAP = {
    "ebay": lambda: {
        "app_id": settings.EBAY_APP_ID,
        "cert_id": settings.EBAY_CERT_ID,
        "campaign_id": settings.EBAY_CAMPAIGN_ID,
        "custom_id": settings.EBAY_AFFILIATE_CUSTOM_ID,
    },
    "amazon": lambda: {
        "country_code": settings.AMAZON_DEFAULT_COUNTRY,
        "associate_tag": settings.AMAZON_ASSOCIATE_TAG,
    },
    "cj": lambda: {
        "api_key": settings.CJ_API_KEY,
        "website_id": settings.CJ_WEBSITE_ID,
    },
}
```

**Adding a new provider:**
1. Create `backend/app/services/affiliate/providers/new_provider.py`
2. Decorate with `@AffiliateProviderRegistry.register("new_name", required_env_vars=[...])`
3. Implement `BaseAffiliateProvider` interface
4. Add entry to `_PROVIDER_INIT_MAP` in `backend/app/services/affiliate/loader.py` if constructor needs non-default kwargs
5. Add relevant settings to `backend/app/core/config.py`
6. No other code changes needed -- auto-discovery handles the rest

## AffiliateManager

**File:** `backend/app/services/affiliate/manager.py`

**Singleton:** `affiliate_manager = AffiliateManager()` at module level

**Initialization Flow:**
1. If `USE_MOCK_AFFILIATE=True`, registers `MockAffiliateProvider` as primary
2. Calls `setup_affiliate_providers(self)` for auto-discovery
3. Sets primary provider to first non-mock provider found (or mock as fallback)

**Key Methods:**
- `search_products(query, ..., provider_name)` -- Search via specified or primary provider; on failure, tries all other providers via `_search_with_fallback()`
- `search_amazon_products(query, ..., country_code)` -- Amazon-specific search with regional support
- `get_amazon_search_url(query, country_code)` -- Get Amazon search URL with affiliate tag
- `generate_affiliate_link(product_id, provider_name, ...)` -- Generate affiliate tracking link
- `check_link_health(affiliate_link, provider_name)` -- Validate link is still active
- `get_available_providers()` -- List currently active provider names

**MockAffiliateProvider:** Built into `manager.py`. Generates realistic mock products with category-specific brands, price ranges, and titles. Used when `USE_MOCK_AFFILIATE=True` or as last-resort fallback.

## Provider Implementations

### Amazon Provider

**File:** `backend/app/services/affiliate/providers/amazon_provider.py`

**Dual Mode:**
- **Mock mode** (default, `AMAZON_API_ENABLED=False`): Generates realistic mock Amazon products using `CATEGORY_VARIATIONS` and `CATEGORY_BASE_PRICES` dicts. Supports 12+ product categories (laptop, phone, headphones, monitor, camera, etc.).
- **Real PA-API mode** (`AMAZON_API_ENABLED=True`): Makes signed requests to Amazon Product Advertising API v5. Requires `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_ASSOCIATE_TAG`.

**Regional Support:**
- `AMAZON_ASSOCIATE_TAGS` setting: Comma-separated `country:tag` pairs (e.g., `"US:reviewguide-20,UK:reviewguide-21"`)
- `AMAZON_DOMAINS` dict maps country codes to Amazon domain suffixes
- `generate_amazon_affiliate_link(url, country_code)` stamps the correct associate tag

**Registration:**
```python
@AffiliateProviderRegistry.register(
    "amazon",
    required_env_vars=[],  # No required env vars (mock mode works without)
    optional_env_vars=["AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_ASSOCIATE_TAG"],
)
```

### eBay Provider

**File:** `backend/app/services/affiliate/providers/ebay_provider.py`

**Dual Mode:**
- **Mock mode** (when `EBAY_APP_ID` empty): Generates eBay-flavored mock products (different titles/conditions than Amazon mock)
- **Real Browse API mode**: Uses eBay Browse API for search, builds EPN affiliate links with tracking parameters

**EPN Link Parameters:**
- `mkcid` (marketing channel), `mkrid` (rotation ID), `toolid`, `mkevt` (marketing event)
- Configured via `EBAY_MKCID`, `EBAY_MKRID`, `EBAY_TOOLID`, `EBAY_MKEVT` settings

**Registration:**
```python
@AffiliateProviderRegistry.register(
    "ebay",
    required_env_vars=[],
    optional_env_vars=["EBAY_APP_ID", "EBAY_CERT_ID", "EBAY_CAMPAIGN_ID"],
)
```

### CJ (Commission Junction) Provider

**File:** `backend/app/services/affiliate/providers/cj_provider.py`

**API:** CJ Product Search API v2 (XML-based, `https://product-search.api.cj.com/v2/product-search`)

**Features:**
- Bearer token auth via `CJ_API_KEY`
- XML response parsing via `xml.etree.ElementTree`
- Redis caching with configurable TTL (`CJ_CACHE_TTL`, default 8 hours)
- Cache key: `cj:search:{md5_hash_of_params}`
- Advertiser filtering via `CJ_ADVERTISER_IDS` (default "joined" = all joined advertisers)
- Link health monitoring via HEAD requests

**Registration:**
```python
@AffiliateProviderRegistry.register(
    "cj",
    required_env_vars=["CJ_API_KEY", "CJ_WEBSITE_ID"],
)
```

**Relevant Settings:**
- `CJ_API_KEY` -- Personal access token (Bearer token)
- `CJ_WEBSITE_ID` -- Publisher website ID (PID)
- `CJ_ADVERTISER_IDS` -- "joined" or comma-separated CIDs
- `CJ_API_TIMEOUT` -- Request timeout (default 10s)
- `CJ_CACHE_TTL` -- Redis cache TTL (default 28800s / 8h)
- `CJ_MAX_RESULTS` -- Max products per search (default 20)

### Curated Amazon Links

**File:** `backend/app/services/affiliate/providers/curated_amazon_links.py`

**Not a provider class** -- this is a static data module containing the `CURATED_LINKS` dict.

**Structure:**
```python
CURATED_LINKS = {
    "bluetooth speaker": [
        {"url": "https://amzn.to/...", "title": "...", "price": 179.95, "asin": "...", "image_url": "..."},
        ...
    ],
    "noise cancelling headphone": [...],
    "laptop student": [...],
    ...
}
```

**Usage:** When `USE_CURATED_LINKS=True` (default), `product_compose` and `product_affiliate` tools check `CURATED_LINKS` for keyword matches before falling back to live API search. This provides reliable affiliate links without requiring PA-API credentials.

**Current Coverage:** 120+ products across categories:
- Electronics: bluetooth speakers, headphones, laptops, smartphones
- Home Appliances: robot vacuums, washing machines, vacuums, espresso machines
- Health/Wellness: standing desks
- And more

**Keyword Matching:** Fuzzy matching against the dict keys. The tool searches for the best matching category based on user query keywords.

## Placeholder Providers (Not Yet Implemented)

Settings exist in `backend/app/core/config.py` but no provider implementations:

| Provider | Settings | Status |
|----------|----------|--------|
| Walmart | `WALMART_API_ENABLED`, `WALMART_API_KEY`, `WALMART_AFFILIATE_ID` | Placeholder |
| Best Buy | `BESTBUY_API_ENABLED`, `BESTBUY_API_KEY`, `BESTBUY_AFFILIATE_ID` | Placeholder |
| Target | `TARGET_API_ENABLED`, `TARGET_API_KEY`, `TARGET_AFFILIATE_ID` | Placeholder |

These are referenced in `TIER_ROUTING_TABLE` (tiered router) as `walmart_affiliate`, `bestbuy_affiliate` but have no actual provider implementations.

## Data Flow: Product Query to Affiliate Links

1. **User sends:** "best noise cancelling headphones"
2. **Intent Agent:** Classifies as `intent="product"`
3. **Planner Agent:** Selects `product_search` as entry-point tool; dependency expansion adds `product_normalize`, `product_affiliate`, `product_compose`, `next_step_suggestion`
4. **PlanExecutor Step 1:** `product_search` tool calls Perplexity/OpenAI search provider
5. **PlanExecutor Step 2:** `product_normalize` merges search results with evidence/ranking data
6. **PlanExecutor Step 3:** `product_affiliate` tool calls `affiliate_manager.search_products()` for each product
   - If `USE_CURATED_LINKS=True`: Checks `CURATED_LINKS` for matching keywords first
   - Calls each registered provider (amazon, ebay, cj) depending on availability
   - Falls back between providers on failure
7. **PlanExecutor Step 4:** `product_compose` merges affiliate links into products, generates `assistant_text` and `ui_blocks`
8. **Frontend:** Renders `ProductCards` with affiliate links embedded

## Link Health Monitoring

**Background Service:** `backend/app/services/link_health_checker.py`

**Scheduler:** `backend/app/services/scheduler.py` -> Runs link health checks every `LINK_HEALTH_CHECK_INTERVAL_HOURS` (default 6)

**Process:**
1. Loads affiliate links from database
2. For each link, calls provider's `check_link_health()` method (typically HEAD request)
3. Updates link status in database
4. Controlled by `ENABLE_LINK_HEALTH_CHECKER` flag

**Settings:**
- `ENABLE_LINK_HEALTH_CHECKER` -- Enable/disable (default True)
- `LINK_HEALTH_CHECK_INTERVAL_HOURS` -- Check frequency (default 6)
- `LINK_HEALTH_CHECK_TIMEOUT` -- Per-link timeout (default 10s)
- `LINK_HEALTH_CHECK_MAX_CONCURRENT` -- Max parallel checks (default 10)

## Click Tracking

**Endpoint:** `POST /v1/affiliate/click` in `backend/app/api/v1/affiliate.py`

**Model:** `AffiliateClick` in `backend/app/models/affiliate_click.py`

**Tracked Fields:** session_id, provider, product_name, category, url, timestamp

**Rate Limited:** Via `check_rate_limit` dependency

## Configuration Summary

| Setting | Default | Purpose |
|---------|---------|---------|
| `USE_MOCK_AFFILIATE` | True | Use mock provider for development |
| `USE_CURATED_LINKS` | True | Use static curated Amazon links as primary source |
| `MAX_AFFILIATE_OFFERS_PER_PRODUCT` | 3 | Max affiliate offers to fetch per product |
| `SHOW_AFFILIATE_LINKS_PER_PRODUCT` | False | Show multiple seller links per product |
| `AMAZON_API_ENABLED` | False | Enable real PA-API |
| `AMAZON_ACCESS_KEY` | "" | PA-API access key |
| `AMAZON_SECRET_KEY` | "" | PA-API secret key |
| `AMAZON_ASSOCIATE_TAG` | "" | Default associate tag |
| `AMAZON_ASSOCIATE_TAGS` | "US:,UK:,..." | Regional associate tags |
| `AMAZON_DEFAULT_COUNTRY` | "US" | Default country for Amazon links |
| `EBAY_APP_ID` | "" | eBay application ID |
| `EBAY_CERT_ID` | "" | eBay client secret |
| `EBAY_CAMPAIGN_ID` | "" | EPN campaign ID |
| `CJ_API_ENABLED` | False | Enable CJ API |
| `CJ_API_KEY` | "" | CJ Bearer token |
| `CJ_WEBSITE_ID` | "" | CJ publisher website ID |

---

*Affiliate system analysis: 2026-03-25*
