# Phase 11: Viator + CJ Expansion - Research

**Researched:** 2026-03-25
**Domain:** Travel activity API integration (Viator Partner API v2) + CJ affiliate network expansion
**Confidence:** HIGH (codebase patterns) / MEDIUM (Viator API specifics)

## Summary

Phase 11 has two distinct tracks: (A) integrating the Viator Partner API as a travel activity search provider, and (B) expanding CJ affiliate advertiser coverage by submitting applications to major retail brands. Track B requires no code changes -- the existing CJ provider already uses `advertiser_ids="joined"` which means any newly approved advertiser's products automatically appear in search results.

Track A (Viator) requires building a new `travel_search_activities` MCP tool and a `ViatorActivityProvider` class. The project already has a stub PLP link generator at `backend/app/services/travel/providers/viator_plp_provider.py` which only generates search URLs. The real implementation needs to call the Viator Partner API `/search/freetext` endpoint to return actual activity data (names, images, prices, booking links). The existing patterns for travel PLP providers (Expedia, Booking) and affiliate providers (CJ, eBay) provide clear templates.

**Primary recommendation:** Build a `ViatorActivityProvider` that calls `/search/freetext` with `searchType: PRODUCTS`, returns results as a new `activities` state field, and registers in the `AffiliateProviderRegistry` for auto-discovery. Use the two-track approach: API search for rich data, PLP fallback link for when API is unavailable.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROV-02 | Viator activity search is available for travel queries with activity names, images, prices, and booking links; auto-discovered by provider loader | Viator Partner API `/search/freetext` endpoint returns product summaries (title, images, pricing, reviews). Provider pattern from CJ/eBay shows how to use `@AffiliateProviderRegistry.register()` for auto-discovery. New MCP tool `travel_search_activities` follows existing `travel_search_hotels` pattern. |
| PROV-03 | CJ advertiser applications submitted for 3+ target brands; approved advertisers appear without code changes | Existing CJ provider uses `advertiser_ids="joined"` (all joined advertisers). CJ publisher portal at signup.cj.com allows applying to individual advertiser programs. No code change needed -- this is purely a business process. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | (existing) | Async HTTP client for Viator API calls | Already used by CJ provider, eBay provider |
| pydantic | (existing) | Data models for activity cards | Already used for HotelCard, FlightCard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Redis (existing) | 7 | Cache Viator search results and destination ID lookups | Every API call should check cache first |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Viator API `/search/freetext` | PLP link only (existing stub) | PLP links don't provide activity names, images, or prices -- fails PROV-02 requirement |
| Viator API `/products/search` | Requires destination ID lookup first | Adds extra API call; `/search/freetext` accepts text queries directly |

**Installation:**
No new dependencies required. All libraries (httpx, pydantic, redis) are already installed.

## Architecture Patterns

### Decision: Two Registrations, One Provider

The Viator provider is unique because it serves **both** the travel system (activity search) and the affiliate system (affiliate links with commission tracking). The implementation should:

1. Register in `AffiliateProviderRegistry` (for PROV-02 auto-discovery requirement)
2. Create a new MCP tool `travel_search_activities` (for travel workflow integration)
3. Add an `activities` field to GraphState and initial_state in chat.py
4. Update `travel_compose` to handle the new `activities` UI block type with Viator data

### Recommended Project Structure
```
backend/
  app/
    services/
      affiliate/
        providers/
          viator_provider.py          # NEW: AffiliateProviderRegistry provider
      travel/
        providers/
          viator_plp_provider.py      # EXISTS: PLP fallback (keep)
  mcp_server/
    tools/
      travel_search_activities.py     # NEW: MCP tool for activity search
  tests/
    test_viator_provider.py           # NEW: Unit tests
```

### Pattern 1: Viator API Provider (follows CJ provider pattern)
**What:** A class implementing `BaseAffiliateProvider` that calls the Viator Partner API
**When to use:** For every travel query asking about activities, experiences, tours, or things to do
**Example:**
```python
# Source: Existing CJ provider pattern + Viator API docs
@AffiliateProviderRegistry.register(
    "viator",
    required_env_vars=["VIATOR_API_KEY"],
    optional_env_vars=["VIATOR_AFFILIATE_ID"],
)
class ViatorActivityProvider(BaseAffiliateProvider):
    """
    Viator Partner API v2 Activity Provider

    Searches for tours, activities, and experiences via /search/freetext.
    Returns results with activity names, images, prices, and affiliate booking links.
    """

    VIATOR_API_BASE = "https://api.viator.com/partner"

    def __init__(self, api_key: str = None, affiliate_id: str = None):
        self.api_key = api_key or settings.VIATOR_API_KEY
        self.affiliate_id = affiliate_id or settings.VIATOR_AFFILIATE_ID
        self.timeout = settings.VIATOR_API_TIMEOUT  # new config setting
        self.cache_ttl = settings.VIATOR_CACHE_TTL  # new config setting

    async def search_products(
        self, query: str, category=None, brand=None,
        min_price=None, max_price=None, limit: int = 10,
    ) -> List[AffiliateProduct]:
        # Check Redis cache first
        # POST to /search/freetext
        # Parse response into AffiliateProduct list
        # Cache and return
        pass
```

### Pattern 2: MCP Tool (follows travel_search_cars pattern)
**What:** An MCP tool that reads destination from state slots and returns activity results
**When to use:** When planner selects `travel_search_activities` for a travel query
**Example:**
```python
# Source: Existing travel_search_cars.py pattern
TOOL_CONTRACT = {
    "name": "travel_search_activities",
    "purpose": "Search for tours, activities, experiences, things to do",
    "intent": "travel",
    "tools": {
        "pre": [],   # Entry-point tool
        "post": []    # Compose is auto-added
    },
    "produces": ["activities"],
    "required_slots": ["destination"],
    "optional_slots": ["departure_date", "duration_days"],
    "citation_message": "Finding activities and experiences...",
    "tool_order": 100,
}
```

### Pattern 3: Viator Affiliate Deep Link Construction
**What:** Converting Viator product codes to affiliate booking links
**When to use:** For every activity result returned by the API
**Format:** `https://www.viator.com/tours/{destination}/{product-title}/d{destId}-{productCode}?pid={PID}&mcid=42383&medium=api`

Alternatively, for search-level PLP links (fallback):
`https://www.viator.com/searchResults/all?text={destination}&pid={PID}&mcid=42383&medium=link`

### Anti-Patterns to Avoid
- **Using /products/search without destination ID:** Requires a prior `/taxonomy/destinations` call to resolve city name to destId. Use `/search/freetext` instead -- it accepts free text.
- **Ingesting via search endpoints:** Viator explicitly forbids using `/products/search` or `/search/freetext` for data ingestion. Only use for real-time user queries.
- **Removing PID/MCID from affiliate links:** These parameters are required for commission tracking. If removed, no commissions are paid.
- **Adding `activities` to GraphState without updating `chat.py`:** Will crash LangGraph channels. MUST add default value `"activities": []` to initial_state dict.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Destination ID resolution | Custom destination name-to-ID mapper | `/search/freetext` endpoint | Accepts text queries directly; no need for `/taxonomy/destinations` lookup |
| Affiliate link construction | Custom URL builder | Viator's returned `productUrl` + affiliate params | API returns product page URLs; just append `?pid=...&mcid=42383` |
| Activity data caching | Custom in-memory cache | Redis with `redis_get_with_retry`/`redis_set_with_retry` | Pattern established by CJ provider; handles failures gracefully |
| CJ advertiser expansion | Custom advertiser ID management | `advertiser_ids="joined"` setting | Already configured -- CJ API returns products from ALL joined advertisers |

**Key insight:** The CJ expansion requires zero code changes. The existing `CJ_ADVERTISER_IDS=joined` setting means any approved advertiser automatically appears in results. The work is entirely business process (submitting applications on CJ publisher portal).

## Common Pitfalls

### Pitfall 1: GraphState Missing `activities` Field
**What goes wrong:** LangGraph channels crash when a tool writes to a state key that doesn't exist in the TypedDict
**Why it happens:** New state fields require both TypedDict definition AND initial_state default
**How to avoid:** Add `activities: List[Dict[str, Any]]` to GraphState AND `"activities": []` to initial_state in chat.py (~line 330)
**Warning signs:** `KeyError` or channel crash on first travel query with activities

### Pitfall 2: Viator API Rate Limiting
**What goes wrong:** API returns 429 errors when search endpoints are called too frequently
**Why it happens:** Viator explicitly warns about rate limits on `/products/search` and `/search/freetext`
**How to avoid:** Redis cache with 4-8 hour TTL (like CJ provider's 8-hour TTL). Log cache hit/miss ratio.
**Warning signs:** Increasing 429 responses in logs

### Pitfall 3: Viator API Key Not Set on Railway
**What goes wrong:** Provider silently skips (due to env var check) and no activities appear
**Why it happens:** Lesson from project memory: "ALWAYS verify new feature flags exist on Railway after adding them"
**How to avoid:** Add `VIATOR_API_KEY` and `VIATOR_AFFILIATE_ID` to Railway env vars. Provider loader logs warning when vars are missing -- check startup logs.
**Warning signs:** `Skipping affiliate provider 'viator': missing required env vars` in logs

### Pitfall 4: PLP Fallback Not Wired When API Fails
**What goes wrong:** If Viator API is down, no activities appear at all
**Why it happens:** Provider only tries API call, doesn't fall back to PLP search link
**How to avoid:** On API failure, fall back to generating a Viator PLP search URL (existing `ViatorPLPLinkGenerator`). Return a single result with the search link.
**Warning signs:** Empty activities list when API times out

### Pitfall 5: MCP Tool Not Imported in main.py
**What goes wrong:** New tool is not available in the MCP server
**Why it happens:** MCP tools require explicit import and registration in `main.py`
**How to avoid:** Add import + Tool() registration in `backend/mcp_server/main.py`
**Warning signs:** Tool not appearing in `list_tools()` response

### Pitfall 6: Provider Loader Missing Init Map Entry
**What goes wrong:** `viator` provider class is auto-discovered but fails to instantiate
**Why it happens:** `_PROVIDER_INIT_MAP` in `loader.py` maps provider names to constructor kwargs. Without an entry, the loader calls `provider_class()` with no args.
**How to avoid:** Add `"viator"` entry to `_PROVIDER_INIT_MAP` in `backend/app/services/affiliate/loader.py`
**Warning signs:** `Failed to instantiate affiliate provider 'viator'` in logs

## Code Examples

### Viator API /search/freetext Request
```python
# Source: Viator Partner API documentation (docs.viator.com)
# POST https://api.viator.com/partner/search/freetext
headers = {
    "exp-api-key": self.api_key,
    "Accept-Language": "en-US",
    "Accept": "application/json;version=2.0",
    "Content-Type": "application/json",
}
body = {
    "searchTerm": "Paris tours",
    "searchTypes": [
        {
            "searchType": "PRODUCTS",
            "pagination": {
                "start": 1,
                "count": 10
            }
        }
    ],
    "currency": "USD",
    "productSorting": {
        "sort": "DEFAULT",
        "order": "DESCENDING"
    },
}
```

### Viator Affiliate Link Construction
```python
# Source: Viator partner documentation (partnerresources.viator.com)
# Format: base_url + ?pid={PID}&mcid=42383&medium=api
def build_affiliate_link(product_url: str, affiliate_id: str) -> str:
    separator = "&" if "?" in product_url else "?"
    return f"{product_url}{separator}pid={affiliate_id}&mcid=42383&medium=api"
```

### ActivityCard Pydantic Model (new)
```python
# Source: Existing TravelCard/HotelCard pattern in base.py
class ActivityCard(TravelCard):
    """Standardized activity/experience card format"""
    name: str
    description: Optional[str] = None
    destination: str
    price_from: float
    currency: str = "USD"
    duration_minutes: Optional[int] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None  # e.g. "Walking Tour", "Food & Drink"
    free_cancellation: bool = False
```

### Config Settings to Add
```python
# Source: Existing pattern from CJ settings in config.py
VIATOR_API_KEY: str = Field(default="", description="Viator Partner API key (exp-api-key header)")
VIATOR_AFFILIATE_ID: str = Field(default="", description="Viator affiliate ID (PID) for tracking")  # EXISTS already
VIATOR_API_ENABLED: bool = Field(default=False, description="Enable Viator activity search API")
VIATOR_API_TIMEOUT: float = Field(default=10.0, description="Viator API request timeout in seconds")
VIATOR_CACHE_TTL: int = Field(default=28800, description="Viator search cache TTL in seconds (8 hours)")
VIATOR_MAX_RESULTS: int = Field(default=10, description="Max Viator activities per search request")
```

### travel_compose Update for Activities
```python
# Source: Existing pattern in travel_compose.py
# Add after cars block (line ~153)
activities = state.get("activities")
has_activities = activities and len(activities) > 0

if has_activities:
    ui_blocks.append({"type": "activities_viator", "data": activities[:5]})
    logger.info(f"[travel_compose] Added Viator activities UI block with {len(activities[:5])} activities")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Viator PLP link only (stub) | Viator Partner API v2 `/search/freetext` | Phase 11 | Rich activity data with names, images, prices |
| CJ manual advertiser IDs | `CJ_ADVERTISER_IDS=joined` (all joined) | Already done | New advertisers auto-included after approval |
| Viator API v1 (apiKey query param) | Viator API v2 (exp-api-key header) | 2024 | New auth format, new search endpoints |

**Deprecated/outdated:**
- Viator API v1 query parameter authentication -- still works but new endpoints require header-based auth
- Viator PLP-only approach for activities -- provides no data for UI cards (only a search link)

## Open Questions

1. **Viator API Response Schema Details**
   - What we know: Response includes product title, short description, cover image, rating, review count, pricing. Endpoint is `/search/freetext` with POST.
   - What's unclear: Exact JSON field names in response body (e.g., is it `productCode` or `code`? Is pricing under `pricing.summary.fromPrice`?). The API docs are JS-rendered and not scrape-able.
   - Recommendation: Sign up for Viator affiliate account to get API key, make test call, inspect response. Alternatively, handle with flexible JSON parsing and log full response on first call.

2. **Viator API Key Provisioning**
   - What we know: Free to sign up, Basic Access API key provided immediately on account creation. Key format is UUID (e.g., `f26df9bd-0b21-427b-9a9f-6d2be46f06d8`).
   - What's unclear: Whether the project already has a Viator affiliate account, or if sign-up is needed.
   - Recommendation: Check if `VIATOR_AFFILIATE_ID` is already set in Railway. If not, sign up at partnerresources.viator.com.

3. **Frontend ActivityCard Component**
   - What we know: Frontend already renders `activities` UI blocks from `destination_facts` (plain text list). Viator activities would be richer (images, prices, links).
   - What's unclear: Whether a new frontend component is needed for `activities_viator` type, or if existing `activities` type can be extended.
   - Recommendation: Use a new `activities_viator` UI block type to avoid breaking existing plain-text activities from `destination_facts`. Frontend component work may be deferred.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/pytest.ini` or `pyproject.toml` |
| Quick run command | `cd backend && python -m pytest tests/test_viator_provider.py -x -v` |
| Full suite command | `cd backend && python -m pytest tests/ -x -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROV-02a | Viator API call returns activity data | unit | `pytest tests/test_viator_provider.py::TestViatorSearch -x` | No -- Wave 0 |
| PROV-02b | Viator provider auto-discovered by registry | unit | `pytest tests/test_viator_provider.py::TestViatorRegistration -x` | No -- Wave 0 |
| PROV-02c | Results include name, image, price, booking link | unit | `pytest tests/test_viator_provider.py::TestViatorResponseParsing -x` | No -- Wave 0 |
| PROV-02d | Redis caching for Viator results | unit | `pytest tests/test_viator_provider.py::TestViatorCaching -x` | No -- Wave 0 |
| PROV-02e | PLP fallback when API fails | unit | `pytest tests/test_viator_provider.py::TestViatorFallback -x` | No -- Wave 0 |
| PROV-02f | MCP tool produces activities state | unit | `pytest tests/test_viator_provider.py::TestViatorMCPTool -x` | No -- Wave 0 |
| PROV-03 | CJ advertiser_ids=joined returns all joined advertisers | manual-only | N/A -- business process, no code change | N/A |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_viator_provider.py -x -v`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_viator_provider.py` -- covers PROV-02 (all sub-requirements)
- [ ] Framework install: none needed (pytest already installed)

## Sources

### Primary (HIGH confidence)
- Existing codebase: `cj_provider.py`, `ebay_provider.py`, `registry.py`, `loader.py`, `base.py` -- provider pattern
- Existing codebase: `travel_search_cars.py`, `travel_search_hotels.py` -- MCP tool pattern
- Existing codebase: `travel_compose.py`, `graph_state.py`, `chat.py` -- state management pattern
- Existing codebase: `viator_plp_provider.py` -- existing PLP stub
- Existing codebase: `test_cj_provider.py` -- test pattern

### Secondary (MEDIUM confidence)
- [Viator Partner API docs](https://docs.viator.com/partner-api/) -- API structure, authentication
- [Viator Technical Guide](https://partnerresources.viator.com/travel-commerce/technical-guide/) -- search endpoint capabilities
- [Viator Affiliate Search API](https://partnerresources.viator.com/travel-commerce/affiliate/search-api/) -- /products/search and /search/freetext
- [Viator Create Links Guide](https://partnerresources.viator.com/travel-content/links/create-links/) -- Affiliate link format (PID, MCID)
- [Viator Access Levels](https://partnerresources.viator.com/travel-commerce/levels-of-access/) -- Basic vs Full vs Booking access
- [Viator Golden Path (Basic)](https://partnerresources.viator.com/travel-commerce/affiliate/basic-access/golden-path/) -- Recommended implementation flow

### Tertiary (LOW confidence)
- Viator API response JSON field names -- could not verify exact schema (JS-rendered docs). Needs validation with actual API call.
- Viator rate limit specifics -- documented as "controlled" but exact numbers not published.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all libraries already in use
- Architecture: HIGH -- follows exact patterns from CJ provider and travel tools
- Viator API specifics: MEDIUM -- authentication, endpoints, and link format confirmed; exact response JSON schema unverified
- CJ expansion: HIGH -- zero code change needed, purely business process
- Pitfalls: HIGH -- based on existing project memory (Railway env vars, GraphState crashes) and Viator docs

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (Viator API is stable; CJ process is ongoing)
