# Phase 7: Skimlinks Middleware + Editor's Picks - Research

**Researched:** 2026-03-25
**Domain:** Post-processing affiliate middleware (backend Python) + Editor's Picks UI (frontend Next.js/React)
**Confidence:** HIGH

## Summary

Phase 7 has two distinct deliverables: (1) a Skimlinks post-processing middleware that automatically wraps product URLs AFTER all providers return results, and (2) an Editor's Picks section on browse category pages that shows curated products with images and affiliate links.

The backend middleware intercepts `affiliate_products` in the `product_affiliate` MCP tool after all provider searches complete. Rather than modifying individual providers, a single post-processing pass iterates all offers, extracts each URL's domain, checks it against the Skimlinks merchant domain cache (built in Phase 6), and wraps qualifying URLs with `go.skimresources.com`. This is architecturally clean because Phase 6 already builds `SkimlinksLinkWrapper` as a standalone service -- Phase 7 just calls `wrap_url()` at the right point in the pipeline. Amazon and eBay URLs are excluded via the `EXCLUDED_DOMAINS` set from Phase 6.

The frontend Editor's Picks section reuses the existing `curatedLinks.ts` data (120+ products across 9 categories with ASINs, amzn.to URLs, titles, and descriptions). The category keys in `curatedLinks.ts` map 1:1 with `categoryConfig.ts` slugs (except `travel` which has no curated products). Product images come from Amazon's CDN using the ASIN-based URL pattern already proven in `InlineProductCard.tsx` and `ResultsProductCard.tsx`: `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg`. The `CuratedProductCard` component already exists but is unused -- it needs to be enhanced with image display and then wired into the browse category page.

**Primary recommendation:** Add Skimlinks post-processing as a function call inside `product_affiliate.py` (after the `asyncio.gather` of provider searches, before the return), and build an `EditorsPicks` component that maps `curatedLinks[category.slug]` to product cards with Amazon CDN images.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AFFL-04 | Any product URL returned by any provider is wrapped by Skimlinks if the merchant domain is in the cache -- without any change to the provider itself | Phase 6 builds `SkimlinksLinkWrapper.wrap_url()` and domain cache in Redis; Phase 7 calls this in `product_affiliate.py` post-processing after all provider results are gathered |
| AFFL-05 | Editor's Picks sections appear on browse category pages with product names, images, and working affiliate links | `curatedLinks.ts` has 120+ products mapped to 9 category keys that match `categoryConfig.ts` slugs; Amazon ASIN image URL pattern proven in `InlineProductCard.tsx`; `CuratedProductCard` component exists but needs image support |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SkimlinksLinkWrapper (Phase 6) | N/A | `wrap_url()` and `is_supported_domain()` for URL wrapping | Built in Phase 6 as standalone service in `backend/app/services/affiliate/skimlinks.py` |
| curatedLinks.ts | N/A | 120+ curated Amazon products with ASINs, URLs, titles, descriptions | Already in frontend, maps to browse categories |
| images-na.ssl-images-amazon.com | N/A | Amazon CDN image hosting via ASIN URL pattern | Proven working in InlineProductCard and ResultsProductCard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | (existing) | Icons for Editor's Picks cards (ExternalLink, Star, etc.) | Card CTAs and decorations |
| next/image or img tag | (existing) | Image rendering with error handling | Product images in Editor's Picks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Post-processing in product_affiliate.py | Separate MCP tool (e.g. skimlinks_wrap) | Adds pipeline complexity; product_affiliate already aggregates all providers so post-processing there is natural |
| Amazon CDN images via ASIN | Skimlinks Product Key API | Product Key requires account manager approval (not self-serve); ASIN images are immediate and proven |
| Enhance CuratedProductCard | Build new EditorsPicks component from scratch | CuratedProductCard exists but lacks images; extending it is less code than starting fresh |

**Installation:**
No new dependencies required. All libraries already in the project.

## Architecture Patterns

### Recommended Project Structure
```
backend/mcp_server/tools/
    product_affiliate.py           # ADD: post-processing call to SkimlinksLinkWrapper
backend/app/services/affiliate/
    skimlinks.py                   # EXISTS (Phase 6): SkimlinksLinkWrapper service

frontend/components/
    EditorsPicks.tsx               # NEW: Editor's Picks section with images
    CuratedProductCard.tsx         # EXISTS: enhance with image display
frontend/app/browse/[category]/
    page.tsx                       # MODIFY: add EditorsPicks section
frontend/lib/
    curatedLinks.ts                # EXISTS: curated product data (read-only)
    categoryConfig.ts              # EXISTS: category definitions (read-only)
```

### Pattern 1: Skimlinks Post-Processing in product_affiliate.py

**What:** After all provider searches complete (the `asyncio.gather` on line ~268 of product_affiliate.py), iterate through the collected `affiliate_products` dict and wrap qualifying URLs with Skimlinks.

**When to use:** Every time product_affiliate runs, regardless of which providers returned data.

**Example:**
```python
# In product_affiliate.py, after building affiliate_products dict (~line 282)

async def _apply_skimlinks_wrapping(affiliate_products: dict, session_id: str = "") -> dict:
    """Post-process all provider results: wrap qualifying URLs with Skimlinks."""
    try:
        from app.services.affiliate.skimlinks import skimlinks_wrapper
        if not skimlinks_wrapper or not settings.SKIMLINKS_API_ENABLED:
            return affiliate_products

        for provider_name, provider_groups in affiliate_products.items():
            for group in provider_groups:
                for offer in group.get("offers", []):
                    url = offer.get("url", "")
                    if url and skimlinks_wrapper.is_supported_domain(url):
                        offer["url"] = skimlinks_wrapper.wrap_url(url, xcust=session_id)
                        offer["skimlinks_wrapped"] = True

    except Exception as e:
        logger.warning(f"[product_affiliate] Skimlinks wrapping failed (non-fatal): {e}")

    return affiliate_products
```

**Key design points:**
- Non-fatal: if Skimlinks wrapping fails, original URLs are preserved
- Provider-agnostic: works on ALL providers without modifying them
- Session tracking: passes session_id as xcust for conversion attribution
- In-place mutation: modifies offer URLs directly in the dict (no copy needed since this is the final step)

### Pattern 2: Editor's Picks Component Using curatedLinks.ts

**What:** A frontend component that renders curated products for the current browse category with images, titles, prices, and affiliate links.

**When to use:** On each browse category page (`/browse/[category]`), between the Popular Questions section and the Explore Other Categories section.

**Example:**
```typescript
// frontend/components/EditorsPicks.tsx
import { curatedLinks, CuratedTopic } from '@/lib/curatedLinks'

interface EditorsPicksProps {
  categorySlug: string
}

function getImageUrl(asin: string): string {
  // Proven pattern from InlineProductCard.tsx
  return `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg`
}

export default function EditorsPicks({ categorySlug }: EditorsPicksProps) {
  const topics = curatedLinks[categorySlug]
  if (!topics || topics.length === 0) return null

  return (
    <section className="px-4 sm:px-6 md:px-8 py-8">
      <h2 className="font-serif text-xl text-[var(--text)]">
        Editor's Picks
      </h2>
      {topics.map((topic, idx) => (
        <div key={idx}>
          <h3>{topic.title}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {topic.products.map((product, pidx) => (
              <a key={pidx} href={product.url} target="_blank" rel="noopener noreferrer">
                <img
                  src={getImageUrl(product.asin)}
                  alt={topic.title}
                  className="w-full aspect-square object-cover rounded-lg"
                  onError={(e) => { /* fallback */ }}
                />
                <span>Option {pidx + 1}</span>
              </a>
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}
```

### Pattern 3: Category Slug to curatedLinks Key Mapping

**What:** The `curatedLinks.ts` keys match `categoryConfig.ts` slugs exactly for 9 of 10 categories.

**Mapping verification:**

| categoryConfig slug | curatedLinks key | Match? | Topics count |
|---------------------|------------------|--------|-------------|
| travel | (none) | NO curated data | 0 |
| electronics | electronics | YES | 4 topics |
| home-appliances | home-appliances | YES | 4 topics |
| health-wellness | health-wellness | YES | 6 topics |
| outdoor-fitness | outdoor-fitness | YES | 4 topics |
| fashion-style | fashion-style | YES | 4 topics |
| smart-home | smart-home | YES | 1 topic |
| kids-toys | kids-toys | YES | 1 topic |
| baby | baby | YES | 1 topic |
| big-tall | big-tall | YES | 1 topic |

**Design implication:** EditorsPicks returns `null` for `travel` (no curated products). All other categories render normally.

### Anti-Patterns to Avoid
- **Modifying individual providers for Skimlinks:** Never add Skimlinks logic inside `ebay_provider.py`, `cj_provider.py`, or any future provider. The whole point of middleware is provider-agnosticism.
- **Building a new data source for Editor's Picks:** `curatedLinks.ts` already has all the data needed. Do not create a separate JSON file or API endpoint.
- **Using placehold.co for product images:** The success criteria explicitly states images must come from a live provider. Use Amazon CDN ASIN images.
- **Double-wrapping Amazon/eBay URLs:** Phase 6's `EXCLUDED_DOMAINS` set prevents this, but the middleware must honor it. Never wrap `amzn.to` or `ebay.com` links.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Skimlinks URL wrapping | Custom URL construction | Phase 6's `SkimlinksLinkWrapper.wrap_url()` | Handles publisher ID, xcust sanitization, URL encoding, domain exclusion |
| Merchant domain lookup | Custom Redis lookup | Phase 6's `SkimlinksLinkWrapper.is_supported_domain()` | Handles cache miss -> API refresh, domain normalization, excluded domains |
| Product images from ASIN | Image scraper or separate API | `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg` | Pattern proven in InlineProductCard.tsx and ResultsProductCard.tsx |
| Image error handling | Custom error boundary | `ImageWithFallback` component or `onError` pattern from existing cards | Both patterns exist in the codebase |
| Category-to-curated mapping | Lookup table or API | Direct key access: `curatedLinks[categorySlug]` | Keys match 1:1 with categoryConfig slugs |

**Key insight:** Both halves of Phase 7 are integration work, not greenfield development. The Skimlinks service exists (Phase 6), the curated data exists (curatedLinks.ts), the image pattern exists (InlineProductCard), and the target page exists (browse/[category]/page.tsx). Phase 7 wires these together.

## Common Pitfalls

### Pitfall 1: Wrapping Already-Affiliated URLs
**What goes wrong:** An eBay URL that already has EPN tracking gets wrapped with Skimlinks, causing double-attribution confusion.
**Why it happens:** The middleware iterates ALL offers from ALL providers without checking if the URL already has affiliate tracking.
**How to avoid:** Phase 6's `SkimlinksLinkWrapper` includes `EXCLUDED_DOMAINS` set (amazon.*, ebay.*). The `is_supported_domain()` method checks this before wrapping. Trust this check -- do not duplicate it in the middleware.
**Warning signs:** URLs containing both `rover.ebay.com` and `go.skimresources.com`.

### Pitfall 2: Amazon ASIN Image URL Format Confusion
**What goes wrong:** Images fail to load because the wrong URL pattern is used.
**Why it happens:** Amazon has multiple image URL formats:
- `/images/P/{ASIN}.01.LZZZZZZZ.jpg` (used in curated_amazon_links.py backend)
- `/images/I/{ASIN}._SL300_.jpg` (used in InlineProductCard.tsx frontend)
- `m.media-amazon.com/images/I/{imageId}._AC_SL1500_.jpg` (used in constants.ts)
**How to avoid:** For Editor's Picks, use the `/images/I/${asin}._SL300_.jpg` pattern. This is the same pattern proven in `InlineProductCard.tsx` (line 38) and `ResultsProductCard.tsx` (line 31). The `/images/P/` pattern in backend curated links uses different sizing suffixes and is less reliable.
**Warning signs:** Broken image icons on Editor's Picks cards.

### Pitfall 3: curatedLinks.ts Only Has ASINs, Not Product Names per Product
**What goes wrong:** Developer tries to show individual product names under each image but discovers `CuratedProduct` only has `{ asin, url }` -- no title field.
**Why it happens:** The interface in `curatedLinks.ts` is minimal: `asin` and `url` only. Product titles live in the backend `curated_amazon_links.py` but not in the frontend.
**How to avoid:** The Editor's Picks design should show the TOPIC title (e.g. "Best Noise-Cancelling Headphones") above a grid of product images. Individual product cards show rank labels ("Option 1", "Option 2") not product names. This matches the existing `CuratedProductCard` pattern (line 52: `product.label || 'Option ${idx + 1}'`).
**Warning signs:** Placeholder text "undefined" under product images.

### Pitfall 4: Middleware Silently Failing Without Logging
**What goes wrong:** Skimlinks wrapping fails (e.g. Redis cache miss, service not initialized) but nobody notices because the error is swallowed.
**Why it happens:** The middleware is non-fatal by design -- failures must not break product search.
**How to avoid:** Always log warnings when wrapping is skipped or fails. Add a `skimlinks_wrapped` flag to offers so the compose tool can optionally display merchant attribution.
**Warning signs:** All product URLs remain unwrapped after deploying Phase 7. Check backend logs for `[product_affiliate] Skimlinks wrapping failed` messages.

### Pitfall 5: Editor's Picks Breaking SSR/Hydration
**What goes wrong:** The browse category page crashes with hydration mismatch errors.
**Why it happens:** The category page is already `'use client'` (line 1 of `app/browse/[category]/page.tsx`), so SSR hydration mismatches are unlikely for new components. However, using `Math.random()`, `Date.now()`, or other non-deterministic values in image fallbacks could cause issues.
**How to avoid:** Use deterministic image fallbacks based on ASIN or product index. Follow project convention: "Avoid `Math.random()` in SSR" (from CLAUDE.md troubleshooting section).
**Warning signs:** Console errors: "Hydration failed because the initial UI does not match what was rendered on the server."

## Code Examples

### Backend: Post-Processing Integration Point

The exact location where Skimlinks middleware hooks in:

```python
# product_affiliate.py -- AFTER line ~282 (building affiliate_products dict)
# and BEFORE the return statement on line ~283

# Apply Skimlinks wrapping to qualifying URLs
session_id = state.get("session_id", "")
affiliate_products = await _apply_skimlinks_wrapping(affiliate_products, session_id)

logger.info(f"[product_affiliate] Total providers with results: {list(affiliate_products.keys())}")

return {
    "affiliate_products": affiliate_products,
    "success": True
}
```

### Frontend: Editor's Picks Image Pattern (proven)

```typescript
// Same pattern as InlineProductCard.tsx line 38
function getImageUrl(asin: string): string {
  return `https://images-na.ssl-images-amazon.com/images/I/${asin}._SL300_.jpg`
}
```

### Frontend: Category Page Integration Point

```typescript
// app/browse/[category]/page.tsx
// Insert EditorsPicks between "Popular Questions" section and "Explore Other Categories" section

import EditorsPicks from '@/components/EditorsPicks'

// Inside the JSX, after the editorial-rule div:
{/* Editor's Picks */}
<EditorsPicks categorySlug={category.slug} />

{/* Curated Queries (existing) */}
<section className="px-4 sm:px-6 md:px-8 py-8">
  ...
</section>
```

### Frontend: Image Error Handling Pattern

```typescript
// Follow the pattern from ImageWithFallback.tsx
const [imgError, setImgError] = useState(false)

{imgError ? (
  <div className="flex items-center justify-center bg-[var(--surface)] w-full h-full rounded-lg">
    <Package size={24} className="text-[var(--text-muted)]" />
  </div>
) : (
  <img
    src={getImageUrl(product.asin)}
    alt={topicTitle}
    className="w-full aspect-square object-cover rounded-lg"
    onError={() => setImgError(true)}
    loading="lazy"
  />
)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-provider affiliate link injection | Post-processing middleware (Phase 7) | Phase 7 | Providers never touch Skimlinks; single integration point covers all |
| CuratedProductCard without images | EditorsPicks with ASIN images | Phase 7 | Browse pages show visual product cards instead of text-only links |
| Placeholder images on browse | Live Amazon CDN images | Phase 7 | Meets success criteria #3 (no placehold.co) |

**Deprecated/outdated:**
- `CuratedProductCard`: Will be superseded or extended by `EditorsPicks`. The existing component shows text links only (no images). It exists but is unused anywhere in the codebase.

## Open Questions

1. **ASIN image reliability for all 120+ products**
   - What we know: The `images/I/${asin}._SL300_.jpg` pattern works for the ASINs used in InlineProductCard and ResultsProductCard.
   - What's unclear: Whether ALL 120+ ASINs in curatedLinks.ts resolve to valid images via this URL pattern. Some ASINs may use a different image ID format (the `P/` vs `I/` distinction).
   - Recommendation: Implement robust `onError` fallback. Test a sample of ASINs from each category during development. If a significant number fail, fall back to the `/images/P/${asin}.01.LZZZZZZZ.jpg` pattern used in the backend curated_amazon_links.py.

2. **Phase 6 completion status**
   - What we know: Phase 6 has a RESEARCH.md but no PLAN.md files. Phase 6 is listed as "Not started" in ROADMAP.md.
   - What's unclear: Whether Phase 6's `SkimlinksLinkWrapper` service will exist when Phase 7 begins.
   - Recommendation: Phase 7 backend middleware MUST be coded against the Phase 6 service interface. If Phase 6 is not complete, the middleware should gracefully no-op (check `settings.SKIMLINKS_API_ENABLED` flag). The Editor's Picks frontend work has no dependency on Phase 6.

3. **Whether to enhance CuratedProductCard or build new EditorsPicks**
   - What we know: CuratedProductCard exists, has no images, and is unused. Its interface (`CuratedProduct { asin, url, label? }`) is close to what Editor's Picks needs.
   - What's unclear: Whether the existing component's layout (header + pill links) suits the visual requirement of "product names, images, and working affiliate links."
   - Recommendation: Build a new `EditorsPicks` component that internally renders product cards with images. The existing CuratedProductCard's text-link layout does not match the image-forward requirement. Keep CuratedProductCard for backward compatibility but build the new component fresh.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest 8.x with pytest-asyncio |
| Framework (frontend) | Vitest 4.x with jsdom + @testing-library/react |
| Config file (backend) | `backend/pytest.ini` |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Quick run command (backend) | `cd backend && python -m pytest tests/test_skimlinks_middleware.py -x` |
| Quick run command (frontend) | `cd frontend && npx vitest run tests/editorsPicks.test.tsx` |
| Full suite command (backend) | `cd backend && python -m pytest tests/ -x` |
| Full suite command (frontend) | `cd frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AFFL-04 | Non-excluded URLs are wrapped by Skimlinks post-processing | unit | `cd backend && python -m pytest tests/test_skimlinks_middleware.py::test_middleware_wraps_qualifying_urls -x` | Wave 0 |
| AFFL-04 | Amazon/eBay URLs are NOT wrapped | unit | `cd backend && python -m pytest tests/test_skimlinks_middleware.py::test_middleware_skips_excluded_domains -x` | Wave 0 |
| AFFL-04 | Middleware failure does not break product_affiliate | unit | `cd backend && python -m pytest tests/test_skimlinks_middleware.py::test_middleware_failure_is_nonfatal -x` | Wave 0 |
| AFFL-04 | Middleware is called without changes to any provider file | unit | `cd backend && python -m pytest tests/test_skimlinks_middleware.py::test_no_provider_modifications -x` | Wave 0 |
| AFFL-05 | EditorsPicks renders product images for a category with curated data | unit | `cd frontend && npx vitest run tests/editorsPicks.test.tsx -t "renders product images"` | Wave 0 |
| AFFL-05 | EditorsPicks returns null for category without curated data (travel) | unit | `cd frontend && npx vitest run tests/editorsPicks.test.tsx -t "returns null for travel"` | Wave 0 |
| AFFL-05 | Product images use Amazon CDN URL pattern (not placehold.co) | unit | `cd frontend && npx vitest run tests/editorsPicks.test.tsx -t "uses Amazon CDN"` | Wave 0 |
| AFFL-05 | Affiliate links from curatedLinks.ts are wired to product cards | unit | `cd frontend && npx vitest run tests/editorsPicks.test.tsx -t "affiliate links"` | Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run commands above
- **Per wave merge:** Full backend + frontend suite
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_skimlinks_middleware.py` -- covers AFFL-04
- [ ] `frontend/tests/editorsPicks.test.tsx` -- covers AFFL-05
- [ ] No framework install needed -- both pytest and vitest are already configured

## Sources

### Primary (HIGH confidence)
- Phase 6 RESEARCH.md (`.planning/phases/06-skimlinks-link-wrapper/06-RESEARCH.md`) -- SkimlinksLinkWrapper service design, EXCLUDED_DOMAINS, wrap_url() interface
- Skimlinks integration research (`.planning/research/skimlinks-integration.md`) -- Merchant API, link wrapper URL format, two-layer architecture
- `backend/mcp_server/tools/product_affiliate.py` -- exact code location for post-processing (after line ~268 asyncio.gather)
- `frontend/lib/curatedLinks.ts` -- 120+ curated products with ASINs across 9 categories
- `frontend/lib/categoryConfig.ts` -- 10 browse category slugs
- `frontend/components/InlineProductCard.tsx` -- ASIN image URL pattern (line 38)
- `frontend/components/CuratedProductCard.tsx` -- existing component (unused, no images)
- `frontend/app/browse/[category]/page.tsx` -- target page for Editor's Picks integration

### Secondary (MEDIUM confidence)
- Amazon CDN image URL patterns verified across three frontend files (InlineProductCard, ResultsProductCard, constants.ts) -- consistent usage confirms reliability

### Tertiary (LOW confidence)
- Whether all 120+ ASINs in curatedLinks.ts resolve to valid images via the `/images/I/` pattern -- needs runtime verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all components already exist in the codebase or are built by Phase 6
- Architecture: HIGH -- post-processing pattern is clean; category-to-curated mapping is 1:1
- Pitfalls: HIGH -- identified from direct codebase analysis, not speculation
- Image URL pattern: MEDIUM -- proven for some ASINs but untested for all 120+

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable -- curated data and Phase 6 interface are locked)
