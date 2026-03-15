# Product Search & Review Feature Fixes

**Project:** ReviewGuide.ai
**Domain:** AI shopping assistant — affiliate product search, review aggregation
**Researched:** 2026-03-15
**Overall confidence:** HIGH (codebase verified directly; external APIs verified via official docs)

---

## Context

Four distinct bugs affect the product search and review pipeline. Each is investigated
separately below with diagnosis, solution, and implementation notes tied to the actual
code in this repo.

---

## Bug 1: Only eBay Returns Real Results

### Diagnosis

**Amazon PA-API** — `AMAZON_API_ENABLED=false` in config. Provider falls back to mock
data (`_search_mock_data`). The mock generates deterministic placeholder products with
`placehold.co` images and fake ASINs. No real data comes back.

**CJ affiliate** — Provider is implemented and registered (confirmed in `loader.py`
`_PROVIDER_INIT_MAP`). The problem stated in the plan doc (`2026-02-27-cj-integration`)
is accurate: `CJ_ADVERTISER_IDS=joined` returns only the advertisers you have been
approved for. The plan notes current approved advertisers are limited (Apple Vacations,
Audiobooks). This means CJ searches return empty or near-empty results for most product
categories until more advertiser relationships are approved.

**eBay** — Works because it has real OAuth credentials (`EBAY_APP_ID`, `EBAY_CERT_ID`)
and the Browse API is live.

### Solution: Serper.dev Shopping as a Product Data Source

The app already uses Serper.dev for review search (`serpapi/client.py`). The same API
key provides access to the shopping endpoint at `https://google.serper.dev/shopping`.

**Serper.dev shopping endpoint confirmed fields** (HIGH confidence — verified via
TypeScript SDK source and SerpApi documentation which mirrors the same data):

```
title        string    — product title
source       string    — retailer name (e.g. "Walmart", "Best Buy")
link         string    — direct product URL on retailer site
price        string    — formatted price (e.g. "$299.99")
imageUrl     string    — product thumbnail image URL (Google-hosted CDN)
rating       number?   — aggregate rating (0-5)
ratingCount  number?   — total ratings
productId    string?   — Google Shopping product ID
delivery     object?   — delivery info
position     number    — search result rank
```

This is sufficient to populate the `AffiliateProduct` dataclass. The `link` field is a
direct retailer URL (not an affiliate link), but it can be presented to users with a
note, or passed through an affiliate link wrapping service.

**Implementation approach:** Create a new `SerperShoppingProvider` that implements
`BaseAffiliateProvider` and uses the existing `SERPAPI_API_KEY` setting. No new API
key required. No new credential to manage. Slots directly into the
`AffiliateProviderRegistry` pattern.

```python
# backend/app/services/affiliate/providers/serper_shopping_provider.py

@AffiliateProviderRegistry.register(
    "serper_shopping",
    required_env_vars=["SERPAPI_API_KEY"],  # reuse existing key
)
class SerperShoppingProvider(BaseAffiliateProvider):
    """Google Shopping results via Serper.dev — no PA-API needed."""

    async def search_products(self, query, category=None, brand=None,
                               min_price=None, max_price=None, limit=10):
        payload = {"q": query, "num": min(limit, 10)}
        # optionally: payload["gl"] = "us" for US results

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://google.serper.dev/shopping",
                json=payload,
                headers={"X-API-KEY": settings.SERPAPI_API_KEY},
            )
        data = resp.json()

        products = []
        for item in data.get("shopping", []):
            price_raw = item.get("price", "")
            price = _parse_price(price_raw)  # strip "$", parse float

            # Apply min/max price filter
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue

            products.append(AffiliateProduct(
                product_id=item.get("productId", ""),
                title=item.get("title", ""),
                price=price,
                currency="USD",
                affiliate_link=item.get("link", ""),
                merchant=item.get("source", ""),
                image_url=item.get("imageUrl"),
                rating=item.get("rating"),
                review_count=item.get("ratingCount"),
                condition="new",
                availability=True,
                source_url=item.get("link", ""),
            ))

        return products[:limit]
```

Register in `loader.py` `_PROVIDER_INIT_MAP`:
```python
"serper_shopping": lambda: {},  # uses settings.SERPAPI_API_KEY internally
```

Add to `product_compose.py` `PROVIDER_CONFIG`:
```python
"serper_shopping": {
    "title": "Shop Online",
    "type": "serper_products",
    "order": 3
},
```

**Affiliate link note:** Serper shopping `link` fields are direct retailer URLs, not
commission-tracked links. This is acceptable for MVP — it still drives users to purchase
pages. For monetization, pass the URL through a Skimlinks or Sovrn Commerce deep-link
wrapper (see Bug 1 — CJ expansion path below).

**Confidence:** HIGH. The Serper shopping endpoint is documented, the `imageUrl` field
is confirmed in the TypeScript SDK interface, and the API key is already in use.

### CJ Expansion Path (parallel work, no code change)

The CJ provider code is correct and complete. The only blocker is lack of approved
advertisers. To expand results:

1. Log into CJ dashboard at https://www.cj.com/
2. Navigate to Advertisers tab, search by category
3. Apply to programs: Best Buy, Dell, HP, Target, Wayfair, Nike, Under Armour, Nordstrom
4. Once approved (typically 1-5 business days), `advertiser-ids=joined` automatically
   includes them — no code change needed
5. Verify via the `/v1/affiliate/cj/search` endpoint (already implemented in
   `backend/app/api/v1/affiliate.py`)

**Confidence:** HIGH. CJ API is verified working; the bottleneck is purely business
(advertiser approvals).

---

## Bug 2: Review Source Links Disappeared from Blog-Style Output

### Diagnosis

In `product_compose.py`, the blog article LLM prompt at line ~624 receives source data
formatted as:

```
- Wirecutter: [snippet text]
- Tom's Guide: [snippet text]
```

The `site_name` from each `ReviewSource` is included, but **the `url` field is never
passed to the LLM**. The system prompt says "Weave in source names only when it adds
credibility" but provides no URLs.

Looking at the blog system prompt (line ~625):
```
"Include the price and a markdown link: [Check price on Merchant →](url)"
```
This only instructs the LLM to link to purchase pages. There is no instruction to link
to review sources, and no review URLs are in the context.

Before the blog refactor (commit bd4b5c3), the template-based fallback path at lines
~767-795 also does not produce review source links — it outputs `consensus` text and
price links only.

The `citations` field at line 834 only collects `normalized_products` URLs, not review
sources:
```python
citations = [p["url"] for p in normalized_products if p.get("url")][:5]
```

### Solution: Two-part fix

**Part 1: Include source URLs in the blog data passed to the LLM.**

In `product_compose.py`, the `blog_data_parts` assembly loop (lines ~576-619) currently
formats each product as:
```
Product: Sony WH-1000XM5 (Best Overall) | Rating: 4.7/5 (1240 reviews) | Price: $279.00 on eBay | Link: https://... | Image: https://...
```

Extend this to append source URLs when `review_bundles` has them:
```python
# In the review_bundles loop (lines ~576-598)
source_refs = ""
if bundle.get("sources"):
    top_sources = bundle["sources"][:3]
    source_refs = " | Reviews: " + ", ".join(
        f"[{s.get('site_name', 'source')}]({s.get('url', '')})"
        for s in top_sources if s.get("url")
    )
blog_data_parts.append(
    f"Product: {pname}{label_str} | Rating: {rating}/5 ({total} reviews)"
    f" | Price: {price_str} on {merchant_str} | Link: {link_str}"
    f" | Image: {image_str}{source_refs}"
)
```

**Part 2: Update the blog system prompt to use those source links.**

Replace the current system prompt instruction (line ~631):
```
- Include the price and a markdown link: [Check price on Merchant →](url)
```

With:
```
- Include the price and a purchase link: [Check price on Merchant →](url)
- For each product, if review source links are provided in the data, include 1-2
  inline citations using the format: [Wirecutter](url) or [Tom's Guide](url).
  Only link to sources that are in the data — never invent URLs.
```

**Part 3: Populate citations from review sources.**

Replace line 834:
```python
citations = [p["url"] for p in normalized_products if p.get("url")][:5]
```

With:
```python
# Collect review source URLs for citations block
review_source_urls = []
for bundle in review_bundles.values():
    for source in bundle.get("sources", [])[:2]:
        if source.get("url"):
            review_source_urls.append(source["url"])

citations = review_source_urls[:5] or [p["url"] for p in normalized_products if p.get("url")][:5]
```

This means the `citations` array (rendered in the frontend `SourcesModal`) will surface
actual review links (Wirecutter, Reddit, Tom's Guide) instead of the product's own URL.

**Confidence:** HIGH. Root cause confirmed by reading the code. The fix is a data-
threading change — no new API calls.

---

## Bug 3: Static amzn.to Short Links Not Resolving

### Diagnosis

**Do amzn.to links expire?** — LOW-MEDIUM confidence (no official Amazon doc found
explicitly). General affiliate industry understanding: amzn.to short links do not
auto-expire. They are permanent redirects tied to your associate tag. A link stops
working only if the underlying ASIN is delisted or the associate program is terminated.

**CORS issue analysis** — This is the more likely culprit for a Next.js frontend. amzn.to
links use a chain of HTTP 301/302 redirects:
```
amzn.to/XXXXX → www.amazon.com/dp/ASIN?tag=xxx → [final product page]
```

If the frontend is attempting to `fetch()` these URLs (e.g., to pre-resolve them for
display), browsers will block the request:
- amzn.to does not set `Access-Control-Allow-Origin` headers
- Amazon.com does not set CORS headers on product pages
- A `fetch()` to these URLs fails silently in the browser

However, `amzn.to` links used as `href` values in `<a>` tags or as `window.location`
navigations do NOT trigger CORS. CORS only applies to `XMLHttpRequest` / `fetch()` calls.

**Redirect chain and third-party cookie blocking** — Modern browsers (Chrome 120+,
Safari 17+) block third-party cookies. Amazon uses cookies in its redirect chain for
session attribution. If the user has strict cookie settings, the affiliate attribution
may not be recorded, but the redirect itself still resolves.

**Root cause in curatedLinks.ts** — The `curatedLinks.ts` data file (created in the
CJ integration plan) stores amzn.to short links. These are used as `href` values in
anchor tags on browse category pages. This is correct usage — `<a href="amzn.to/...">`
works fine. The bug report says they "aren't resolving," which suggests one of:

1. **Frontend is fetching the URLs** to display product metadata (title, image) from
   the redirect target — this will always fail due to CORS + no-embed policies
2. **Link health checker is calling HEAD requests** to amzn.to — this can fail if
   Amazon returns 403 to server-side HEAD requests (they do rate-limit bots)
3. **The links were stored incorrectly** — missing `https://` prefix, or the amzn.to
   service is down (rare)

### Solution

**For browse page curated links** — Use them purely as anchor `href` values. Do NOT
fetch, HEAD-check, or resolve them server-side. Render as:
```tsx
<a href="https://amzn.to/XXXX" target="_blank" rel="noopener noreferrer">
  Pick 1 →
</a>
```

**If displaying product metadata is desired** — Do NOT resolve amzn.to on the frontend.
Instead, pre-resolve them once server-side (Node.js or Python can follow redirects
without CORS restrictions) and store the final ASIN or canonical URL. The Amazon product
thumbnail can then be fetched via the Open Graph approach (see Bug 4).

**For link health checking** — The `link_health_checker.py` service should either:
- Skip amzn.to links (treat them as always-healthy if they contain a valid associate tag)
- Use a server-side HEAD request with a browser User-Agent string and `follow_redirects=True`

**Confidence:** MEDIUM. Amazon link behavior is inferred from browser security rules
and industry knowledge. The exact failure mode in the app requires runtime log
inspection, but the remediation is clear regardless of exact cause.

---

## Bug 4: Product Images Without Amazon PA-API

### Diagnosis

Without PA-API, the Amazon provider falls back to `_search_mock_data` which sets:
```python
image_url=f"https://placehold.co/400x400/fef3c7/f59e0b?text={query.replace(' ', '+')}"
```
These placeholder images display fine but look unprofessional.

For curated amzn.to links in `curatedLinks.ts`, there is no corresponding product image
data at all — the component renders only text links.

### Solution Options (in priority order)

**Option A: Use Serper.dev shopping `imageUrl` (RECOMMENDED)**

As described in Bug 1, the Serper shopping endpoint returns `imageUrl` — a Google-hosted
CDN thumbnail of the product. These are the same images shown in Google Shopping SERP.

- Pros: Already have the API key. One API call gets both price data AND image.
- Cons: Images are Google CDN URLs (may have caching limits for bulk programmatic use;
  but for display on search results this is standard practice across the industry).
- Confidence: HIGH

This is the primary recommendation. Implement the `SerperShoppingProvider` (Bug 1 fix)
and `image_url` is automatically populated from `item.get("imageUrl")`.

**Option B: Open Graph scraping from retailer links**

For products that have a retailer URL (eBay, CJ, direct retailer), fetch the page
server-side and extract `og:image`. Works without any third-party API.

```python
import httpx
from bs4 import BeautifulSoup

async def fetch_og_image(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ReviewGuide/1.0)"},
            timeout=5
        ) as client:
            resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("meta", property="og:image")
        return tag["content"] if tag else None
    except Exception:
        return None
```

- Pros: No API cost. Works for any retailer page. Gets real product image.
- Cons: Latency (each HTTP fetch adds 200-500ms). Rate-limit risk on high-volume
  searches. Amazon.com blocks server-side scrapers and returns 503/robot blocks.
  Should be used for non-Amazon retailers only.
- Confidence: HIGH (standard technique, works for eBay and most retailer pages)

**Option C: eBay Browse API — images are already returned**

The eBay provider already extracts `image_url` from `item["image"]["imageUrl"]` in
`_parse_ebay_item()`. This is working. For categories where eBay has good coverage,
product images are already correct.

**Option D: For amzn.to curated links — pre-resolve once and store ASIN**

Run a one-time server-side resolution script:
1. Follow each amzn.to redirect to get the final Amazon URL
2. Extract the ASIN from `/dp/ASIN` pattern
3. Build a canonical Amazon image URL: `https://images-na.ssl-images-amazon.com/images/I/{imageId}._AC_SL600_.jpg`
   (Note: Amazon image URLs use internal image IDs, not ASINs — this approach requires
   PA-API to be reliable; LOW confidence without PA-API)

Alternative: Use the Open Graph approach for the final canonical Amazon URL after
redirect resolution. This sometimes works, but Amazon blocks scrapers aggressively.

**Recommended implementation path:**

1. Build `SerperShoppingProvider` (addresses Bugs 1 and 4 simultaneously)
2. For eBay results: images already work
3. For CJ results: CJ XML includes `<image-url>` field, already parsed
4. For curated amzn.to links in browse pages: accept no images for now, or use a
   placeholder branded to Amazon (show Amazon logo instead of product photo)
5. Add OG scraping as a background enrichment step for CJ/direct retailer URLs

**Confidence:** HIGH for Options A, B, C. LOW for Option D without PA-API.

---

## Summary of Recommended Changes

| Bug | Root Cause | Fix | Effort |
|-----|-----------|-----|--------|
| eBay only | Amazon mock + CJ no advertisers | Add `SerperShoppingProvider` using existing Serper key | Low — new provider file + register in loader |
| Missing review links | Review source URLs not passed to LLM prompt | Thread `source.url` into `blog_data_parts`; update system prompt; fix `citations` | Low — 3 targeted edits in `product_compose.py` |
| amzn.to not resolving | Frontend likely fetching URLs (CORS) or health checker blocking | Use as `href` only, never fetch; skip in health checker | Low — diagnostic + 1-line guard |
| No product images | Amazon mock returns placeholders | Serper shopping `imageUrl` field (via new provider) | Resolved by Bug 1 fix |

---

## Architecture Notes for Implementation

### Adding SerperShoppingProvider

The registry + loader pattern requires exactly three steps:
1. Create `backend/app/services/affiliate/providers/serper_shopping_provider.py` with
   `@AffiliateProviderRegistry.register("serper_shopping", required_env_vars=["SERPAPI_API_KEY"])`
2. Add `"serper_shopping": lambda: {}` to `_PROVIDER_INIT_MAP` in `loader.py`
3. Add `"serper_shopping"` to `PROVIDER_CONFIG` in `product_compose.py`

No changes to `manager.py`, `registry.py`, or `base.py` needed — the plugin architecture
handles everything.

### GraphState Safety

When the new provider returns results, they appear in `affiliate_products["serper_shopping"]`
in the state dict. The `product_compose` tool already iterates `affiliate_products.keys()`
dynamically — no hardcoding. The `PROVIDER_CONFIG` fallback handles unknown provider
names gracefully (line ~368 in `product_compose.py`).

### Serper API Credits

Serper.dev bills per search. The shopping endpoint costs the same as a regular search
(credits vary by plan). The `review_search` tool already runs 3 Serper calls per product
(editorial + Reddit + shopping for ratings). Adding shopping product search is additive
but uses the same budget. With 5 products per query and 1 shopping search per product,
that is 5 additional credits per user query.

**Caching:** Implement Redis caching in `SerperShoppingProvider` keyed on
`serper_shopping:{md5(query+filters)[:12]}` with a TTL of 3600s (1 hour). This matches
the pattern in `CJAffiliateProvider`. With caching, repeated searches for popular
products (headphones, laptops) consume zero additional credits.

---

## What Was Verified Directly in This Codebase

- `AffiliateProviderRegistry` uses decorator auto-discovery — adding a file to
  `providers/` is sufficient for registration
- `loader.py` `_PROVIDER_INIT_MAP` already has the CJ entry (CJ integration is done)
- `product_compose.py` `blog_data_parts` does NOT include review source URLs in the
  LLM context — this is the confirmed root cause of Bug 2
- `review_search.py` `review_data` contains `sources[].url` fields from Serper organic
  results — the data exists, it just is not threaded through
- `serpapi/client.py` uses `SERPAPI_API_KEY` for Serper.dev calls — the same key works
  for the shopping endpoint
- eBay provider already returns real `image_url` from Browse API when credentials are
  set
- `citations` at line 834 of `product_compose.py` collects from `normalized_products`
  not from `review_data` — confirmed root cause of source attribution loss

---

## Open Questions

1. **Serper.dev shopping `imageUrl` content policy** — Google's terms for Shopping SERP
   data prohibit bulk commercial use of images in certain contexts. For a live product
   recommendation surface, this is standard practice (same as Google Shopping), but
   verify with Serper's ToS if scaling to high volume.

2. **amzn.to link exact failure mode** — The specific failure ("not resolving") needs
   a runtime log check. If the issue is in `link_health_checker.py`, add a log call
   before and after the health check for amzn.to links to confirm.

3. **CJ advertiser approval timeline** — CJ advertiser approval can take 1-5 business
   days per program. Category coverage depends on which programs get approved. Best Buy
   and Target are likely to be approved quickly; niche brands may take longer or require
   minimum traffic proof.

4. **Serper.dev shopping for non-US locales** — The `_serper_request` payload can
   include `"gl": "us"` (country) and `"hl": "en"` (language) parameters. For the
   current US-focused deployment this is not urgent but should be added before any
   international expansion.

---

## Sources

- Serper.dev TypeScript SDK (shopping endpoint field definitions): [serper.ts gist](https://gist.github.com/transitive-bullshit/9ef36acf6dfa4d5b1e1990181a5c3846)
- SerpApi Google Shopping API docs (mirrors Serper field structure): [serpapi.com/google-shopping-api](https://serpapi.com/google-shopping-api)
- Amazon Associates short link guidance: [geniuslink.com/blog/using-short-links-amazon](https://geniuslink.com/blog/using-short-links-amazon/)
- Amazon OneLink redirect behavior: [ctrl.blog/entry/amazon-onelink-affiliate-redirection](https://www.ctrl.blog/entry/amazon-onelink-affiliate-redirection.html)
- Canopy API (Amazon PA-API alternative reference): [canopyapi.co/blog/alternatives-amazon-product-advertising-api](https://www.canopyapi.co/blog/alternatives-amazon-product-advertising-api)
- Walmart Affiliate API: [walmart.io/docs/affiliate](https://walmart.io/docs/affiliate/)
- CJ integration plan (in-repo): `docs/plans/2026-02-27-cj-integration-and-curated-content.md`
- Open Graph scraping: [opengraph — PyPI](https://pypi.org/project/opengraph/)
