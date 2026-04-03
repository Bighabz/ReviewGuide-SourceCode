# Phase 24: Travel Response UI Overhaul - Research

**Researched:** 2026-04-03
**Domain:** React/Next.js travel UI components, image fallback strategy, CSS variable system
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Replace flat bullet list (pin icon + resort name) with card-based layout for attractions
- Single-column on mobile, 2-column grid on desktop (768px+)
- Each resort card: hero image (~60% card height mobile, 16:9 or 3:2 aspect), bold resort name, lighter location text, star rating if available, price indicator if available, CTA linking to booking partner
- Image sourcing priority: (1) hotel/travel API real photos, (2) AI-generated fallbacks based on resort name + location, (3) generic destination placeholder
- Lazy load images — don't load all upfront
- Touch targets minimum 44px tall on CTAs
- Card gap 12-16px between stacked cards
- Hotel/flight widgets: add destination hero image (beach/ocean for hotels, sky/aerial for flights)
- Stack hotel/flight vertically on mobile (no side-by-side — causes "Caribb ean" text wrapping bug)
- Side-by-side hotel/flight only at tablet+ (768px+) — but this is already how BlockRegistry works
- Hero image ~120-150px height on mobile for hotel/flight widgets
- Shrink "Powered by Expedia" badge
- Fix "Caribbean" text wrapping bug
- Update CTA labels: "Search Properties" -> "Search on Expedia" and "Search Flights" -> "Search on Expedia"
- CTA button full card width on mobile
- Reduce dead space between user message bubble and bot reply
- Wrap entire travel response in consistent container with uniform padding (16px mobile, 24px desktop)
- Switch section headers to same sans-serif font family as body text (just bolder/larger) — remove `font-serif` class from h3/h4 elements in travel components
- Add subtle dividers or consistent spacing rhythm between sections
- Style "Want better results?" prompt as distinct secondary CTA with background tint or border
- Section spacing: 24px between major sections on mobile
- Font sizes: body 14-16px, section headers 18-20px, card titles 16-18px, minimum 14px anywhere
- 10 specific resort AI prompts in PRD for Caribbean query
- Generate destination hero images per region (Caribbean, Europe, etc.) reusable across queries
- Generic beach/resort placeholder as last fallback
- All images WebP, under 200KB

### Claude's Discretion
- Whether to use horizontal swipe carousel vs vertical scroll for resort cards on mobile
- Specific implementation of image sourcing from travel APIs
- How to structure the fallback image generation pipeline
- Exact CSS for card hover/touch states
- Whether hotel/flight widget images are background overlays or top sections

### Deferred Ideas (OUT OF SCOPE)
- Google Places API integration for real resort photos (requires API key + billing)
- Open Graph image scraping from resort websites
- Dynamic AI image generation per resort at runtime (expensive, slow)
- Horizontal swipe carousel for mobile resort cards (test vertical first)
</user_constraints>

---

## Summary

Phase 24 transforms the travel chat response from plain text with icon-decorated bullet lists into a visual, card-based experience. The work is entirely frontend-only — no backend data model changes are needed because attractions/restaurants/activities already arrive as flat `string[]` arrays and the backend has no image URL field to add.

The "Must-See Attractions" bullet list is rendered by `ListBlock.tsx` (dispatched via the `attractions` block type in `BlockRegistry.tsx`). Replacing it with resort cards means creating a new `ResortCards.tsx` component and mapping the same `attractions` block type to it, or adding a new block type. Because `BlockRegistry.tsx` is protected from structural changes, the safest approach is to keep the `attractions` key in BLOCK_RENDERERS but swap it from `ListBlock` to the new `ResortCards` component.

Hotel and flight PLPLinkCard components already render vertically on mobile via `BlockRegistry.tsx`'s `md:hidden` / `hidden md:grid` dual-render pattern, but the PLPLinkCard cards themselves show only a large Search icon placeholder with no destination imagery. The "Caribbean" text wrapping bug lives in the `PLPLinkCard` for flights: the route visualization row uses `text-xl font-bold tracking-wider` with both origin and destination labels, making them wrap when the destination name is long.

The "conclusion" block — "Want better results? Tell me your travel dates..." — renders as a plain `<div>` with body text. It needs a styled secondary CTA treatment.

**Primary recommendation:** Create `ResortCards.tsx` (replaces ListBlock for attractions), patch `HotelCards.tsx` PLPLinkCard and `FlightCards.tsx` PLPLinkCard for imagery + CTA fixes, update `BlockRegistry.tsx` only at the renderer-mapping level (not structure), and apply spacing/typography polish to the `UIBlocks` container and individual section headings. Generate 6-8 static destination hero images (WebP) and 1 generic beach/resort fallback.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React/Next.js | 18/14 | Component rendering | Project standard — all components use it |
| Tailwind CSS | 3.x | Utility-first styling | Project standard — CSS variables via inline style, breakpoints via classes |
| lucide-react | latest | Icons | Used throughout (MapPin, Star, ExternalLink, etc.) |
| Framer Motion | 11.x | Card hover/touch animations | Already used for product cards (CARD-04 pattern) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| trackAffiliateClick (local lib) | — | Affiliate click tracking | On every CTA that links to a booking partner |
| sharp (generate-images script) | latest | WebP image generation/optimization | Only in the image-generation script, not runtime |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Static pre-generated images | Runtime Gemini Imagen API | Static is instant, no API cost per request, no latency — deferred items confirm this is correct |
| Tailwind `dark:` prefix | `data-theme="dark"` strategy | Project decision: Tailwind dark: prefix is silently inert; use data-theme |

**Installation:**
No new packages needed. All dependencies exist.

---

## Architecture Patterns

### Recommended Project Structure
```
frontend/components/
├── ResortCards.tsx          # NEW — replaces ListBlock for 'attractions' block type
├── HotelCards.tsx           # MODIFY — PLPLinkCard: add hero image, fix text wrap, CTA label
├── FlightCards.tsx          # MODIFY — PLPLinkCard: add hero image, fix text wrap, CTA label
├── ListBlock.tsx            # PRESERVE unchanged (still handles activities, restaurants)
├── DestinationInfo.tsx      # MODIFY — section headers: remove font-serif, apply sans-serif bold
├── ItineraryView.tsx        # MODIFY — section headers: remove font-serif, apply sans-serif bold
└── blocks/
    └── BlockRegistry.tsx    # MODIFY — swap 'attractions' renderer from ListBlock to ResortCards

frontend/public/images/
└── travel/                  # NEW directory
    ├── hero-caribbean.webp  # Caribbean beach scene
    ├── hero-europe.webp     # European cityscape
    ├── hero-asia.webp       # Asian temple/city
    ├── hero-mountains.webp  # Mountain resort
    ├── hero-hotel.webp      # Generic hotel/beach (hotel widget)
    ├── hero-flight.webp     # Sky/aerial (flight widget)
    └── fallback-resort.webp # Generic beach/resort fallback (last resort)

scripts/
└── generate-travel-images.mjs  # NEW — Gemini Imagen batch generation
```

### Pattern 1: ResortCards Component (New)

**What:** Receives a `string[]` of attraction/resort names, renders them as visual cards with hero images.

**When to use:** Dispatched by BlockRegistry for the `attractions` block type.

**Key design decisions:**
- `items` are plain strings (attraction names only — no structured data with image URLs, prices, or ratings comes from the backend)
- Image sourcing is pure client-side: map attraction name to a pre-generated static image if a match exists, otherwise fall back to `hero-caribbean.webp` (or region-appropriate fallback), then `fallback-resort.webp`
- No runtime API calls for images
- Star rating and price ("From $XXX/night") are NOT available from backend data — they must either be omitted or seeded from a static lookup map; the PRD says "if available" — safe to omit from v1

**Example structure:**
```typescript
// frontend/components/ResortCards.tsx
'use client'

interface ResortCardsProps {
  title?: string
  items: string[]        // plain strings: "Seven Mile Beach, Negril"
  region?: string        // optional hint for fallback image selection
}

// Static image map: normalized resort name fragment -> image path
const RESORT_IMAGE_MAP: Record<string, string> = {
  'seven mile': '/images/travel/hero-caribbean.webp',
  // etc.
}

function getResortImage(name: string): string {
  const lower = name.toLowerCase()
  for (const [key, path] of Object.entries(RESORT_IMAGE_MAP)) {
    if (lower.includes(key)) return path
  }
  return '/images/travel/fallback-resort.webp'
}

export default function ResortCards({ title, items }: ResortCardsProps) {
  if (!items || items.length === 0) return null
  return (
    <div>
      {title && (
        <h3 className="font-sans font-bold text-[18px] sm:text-[20px] text-[var(--text)] flex items-center gap-2.5 mb-4">
          {/* icon + title */}
        </h3>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        {items.map((name, idx) => (
          <ResortCard key={idx} name={name} imageUrl={getResortImage(name)} />
        ))}
      </div>
    </div>
  )
}
```

### Pattern 2: PLPLinkCard Hero Image (Existing Component Modification)

**What:** Add a top hero image band to the existing PLPLinkCard in both HotelCards and FlightCards. Currently renders just a large Search icon on a white circle.

**When to use:** When `type === 'plp_link'` and we want destination imagery.

**Hero image approach — background overlay (recommended for Claude's discretion area):**
```typescript
// Hero image as top section (not background overlay) for accessibility
<div className="relative h-[120px] sm:h-[140px] overflow-clip rounded-t-xl">
  {/* eslint-disable-next-line @next/next/no-img-element */}
  <img
    src="/images/travel/hero-hotel.webp"
    alt=""
    aria-hidden="true"
    className="w-full h-full object-cover"
    loading="lazy"
  />
  {/* Gradient overlay for text legibility if needed */}
  <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
</div>
```

Then the card body (search icon, title, dates, CTA) follows below — drop the `items-center text-center flex-col` centering in favor of `p-5` content block beneath the image.

### Pattern 3: BlockRegistry Renderer Swap (Minimal Change)

**What:** Change one line in BLOCK_RENDERERS to use ResortCards instead of ListBlock for `attractions`.

**Critical:** Do NOT touch UIBlocks function logic, the travel grid logic, or any structural code. Only change the renderer mapping.

```typescript
// In BlockRegistry.tsx — ONLY change this one entry:
// Before:
attractions: (b) => (
    <ListBlock title={b.title ?? 'Must-See Attractions'} items={(b.data as string[]) ?? []} type="attractions" />
),
// After:
attractions: (b) => (
    <ResortCards title={b.title ?? 'Must-See Attractions'} items={(b.data as string[]) ?? []} />
),
```

`ListBlock` import can be retained for `activities` and `restaurants` — those remain unchanged.

### Pattern 4: Conclusion Block Styling

**What:** The `conclusion` block renderer in BlockRegistry currently renders as a plain `<div>`. The "Want better results?" text needs a distinct secondary CTA treatment.

**Approach:** Update the `conclusion` renderer only (safe — it's a renderer, not UIBlocks structure):
```typescript
conclusion: (b) => (
  <div className="mt-2 p-4 rounded-xl border border-[var(--border)]"
    style={{ background: 'color-mix(in srgb, var(--primary) 5%, var(--surface))' }}>
    <p className="text-[14px] text-[var(--text-secondary)] leading-relaxed">
      {(b.data as any)?.text}
    </p>
  </div>
),
```

### Pattern 5: Sans-Serif Section Headers

**What:** PRD says switch section headers away from decorative serif. This affects `font-serif` on `h3`/`h4` in `HotelCards`, `FlightCards`, `DestinationInfo`, `ItineraryView`.

**Change pattern:** Replace `font-serif` class with `font-sans font-bold` on all travel section headings. Font size should be `text-lg sm:text-xl` (18-20px range).

```typescript
// Before (HotelCards h3):
<h3 className="font-serif text-2xl font-semibold flex items-center gap-2.5 text-[var(--text)]">
// After:
<h3 className="font-sans font-bold text-xl text-[var(--text)] flex items-center gap-2.5">
```

### Anti-Patterns to Avoid

- **Don't modify UIBlocks function logic:** The travel grid (`showTravelGrid`, `travelGridRendered`) is inside the UIBlocks function — leave it exactly as-is. The side-by-side layout at desktop already works correctly.
- **Don't add new block types for this phase:** The planner said "modify existing block types", not add new ones. Use `attractions` mapping change only.
- **Don't use Tailwind `dark:` prefix:** Use `data-theme="dark"` CSS variable strategy as established in Phase 17.
- **Don't use `Math.random()` for image selection:** Use deterministic mapping from name strings to avoid SSR hydration errors.
- **Don't use next/image component:** The entire codebase uses raw `<img>` tags (Phase 19 decision: `Use raw <img> tags (not next/image) — consistent with entire codebase convention`).
- **Don't fetch images at runtime from external APIs:** Google Places, Unsplash, etc. are deferred and out of scope.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image optimization | Custom sharp script from scratch | Copy pattern from Phase 18 `optimize-images.mjs` | Existing script handles WebP conversion + quality=60 fallback |
| Affiliate click tracking | Custom fetch call | `trackAffiliateClick` from `@/lib/trackAffiliate` | Already wired to analytics pipeline |
| Dark mode image handling | Separate dark/light image sets | Single image + CSS variable overlay | CSS variables already handle theme; images are decorative |
| Text sanitization | DOMPurify calls | None needed | All data is plain strings from trusted backend |

**Key insight:** The image problem in travel responses is solved statically, not dynamically. The backend returns place names as strings; the frontend does a simple name-to-image lookup. No API calls, no runtime generation.

---

## Common Pitfalls

### Pitfall 1: Breaking the Travel Grid Layout
**What goes wrong:** The UIBlocks function has a dual-render pattern for hotels+flights (desktop: 2-col grid, mobile: stacked). Any change to BlockRegistry.tsx that touches UIBlocks function structure breaks this.
**Why it happens:** Developer sees `HotelCards`/`FlightCards` referenced twice (once in BLOCK_RENDERERS, once inside UIBlocks) and tries to "clean it up."
**How to avoid:** Only modify entries in `BLOCK_RENDERERS` dict. Never touch the `UIBlocks` function logic.
**Warning signs:** If you see yourself editing code inside `export function UIBlocks(`, stop.

### Pitfall 2: "Caribbean" Text Wrapping Bug
**What goes wrong:** Long destination names like "Caribbean" wrap mid-word inside the flight PLPLinkCard route visualization row.
**Why it happens:** The row uses `text-xl font-bold tracking-wider` with `letter-spacing` expanding each character. "Caribbean" at `tracking-wider` + `text-xl` on mobile overflows its flex container.
**Root cause location:** `FlightCards.tsx` line ~93-104, the route visualization `<div className="flex items-center gap-3 mb-4">` with origin/destination spans.
**How to avoid:** Add `break-words` or `max-w-[120px] truncate` to origin/destination text spans, or reduce tracking to `tracking-normal`.
**Warning signs:** Route visualization labels wrapping across lines in Chrome DevTools mobile view.

### Pitfall 3: Image Not Lazy-Loading Correctly
**What goes wrong:** All resort card images load immediately, causing a large payload on mobile.
**Why it happens:** Default `<img>` tags load eagerly.
**How to avoid:** Add `loading="lazy"` to all resort card hero images. Do NOT add it to the first image in the list (or add `loading="eager"` to index 0 to preserve LCP behavior for first-visible card).
**Warning signs:** Network tab shows all images loading simultaneously.

### Pitfall 4: Hydration Mismatch in Image Selection
**What goes wrong:** `ResortCards` renders differently on server vs client, triggering React hydration error.
**Why it happens:** Using `Math.random()` or `Date.now()` in image selection, or accessing `window` during render.
**How to avoid:** Use deterministic name-to-image lookup (string includes check) only. No randomness.
**Warning signs:** Console shows "Hydration failed because the initial UI does not match."

### Pitfall 5: `font-serif` Removal Causing Visual Regressions
**What goes wrong:** Removing `font-serif` from headings in one component accidentally affects sibling or child elements that inherit font.
**Why it happens:** Tailwind applies `font-family` to the element directly, but prose classes in Message.tsx add `prose-headings:font-serif` globally inside the prose wrapper.
**How to avoid:** The section headers in HotelCards/FlightCards/DestinationInfo are OUTSIDE the ReactMarkdown prose wrapper — safe to change. The font change is scoped to explicit `className` on those specific elements.
**Warning signs:** The blog narrative text (ReactMarkdown) changes font unexpectedly.

### Pitfall 6: CTA Height Below 44px Touch Target
**What goes wrong:** CTAs fail tap accuracy on mobile, especially for smaller fingers.
**Why it happens:** Using `py-2` (8px top+bottom = 32px total with text) on button elements.
**How to avoid:** Use `py-3` minimum (12px top+bottom = ~44px with 18px line-height text). The existing CTA buttons use `py-3` — preserve this.
**Warning signs:** Button height < 44px in Chrome DevTools element inspector.

---

## Code Examples

Verified from actual codebase inspection:

### PLPLinkCard Current Structure (HotelCards.tsx ~line 59-114)
```typescript
// Current — no hero image, centered icon layout
<a href={hotel.search_url} className={`block border border-[var(--border)] rounded-xl p-8 ...`}>
  <div className="flex flex-col items-center text-center">
    <div className="w-16 h-16 rounded-full ... bg-[var(--primary-light)]">
      <Search size={28} className="text-[var(--primary)]" />
    </div>
    <h4 className="font-serif font-semibold text-xl mb-3 ...">
      {hotel.title}
    </h4>
    {/* dates, guests, provider badge */}
    <div className="text-xs px-3 py-1.5 rounded-full mb-6 ...">
      Powered by {hotel.provider...}
    </div>
    <button className="w-full px-5 py-3 rounded-lg ...">
      Search Properties   {/* <-- CTA label to change */}
      <ExternalLink />
    </button>
  </div>
</a>
```

### BlockRegistry Attractions Renderer (BlockRegistry.tsx ~line 113-115)
```typescript
// Current
attractions: (b) => (
    <ListBlock title={b.title ?? 'Must-See Attractions'} items={(b.data as string[]) ?? []} type="attractions" />
),
// Target: swap ListBlock to ResortCards
```

### Backend `attractions` Block Data Shape (travel_compose.py ~line 218-224)
```python
# attractions is List[str] — plain strings, no image URLs, no prices
if attractions and len(attractions) > 0:
    ui_blocks.append({
        "type": "attractions",
        "title": "Must-See Attractions",
        "data": attractions   # e.g. ["Seven Mile Beach, Negril", "Dunn's River Falls"]
    })
```

### Hotel PLPLink Data Shape (travel_search_hotels.py ~line 161-170)
```python
hotel_result = {
    "type": "plp_link",
    "provider": provider_label,          # "expedia"
    "destination": destination,          # "Caribbean"
    "search_url": search_url,
    "title": f"Hotels in {destination}",
    "check_in": check_in,
    "check_out": check_out,
    "guests": adults + children,
}
# NO image_url field — must use static fallback
```

### DestinationInfo Section Header (current — has font-serif to remove)
```typescript
// Current — font-serif on section headers
<h4 className="font-serif font-bold text-base mb-1 text-[var(--text)]">
  Weather & Climate
</h4>
// Target — sans-serif, slightly larger
<h4 className="font-sans font-bold text-[15px] text-[var(--text)] mb-1">
  Weather & Climate
</h4>
```

### Existing Fallback Images Available
```
/images/products/fallback-hotel.webp   -- already exists, used in TraditionalHotelCard
/images/products/fallback-flight.webp  -- already exists, used in TraditionalFlightCard
/images/categories/cat-travel.webp     -- exists, bold editorial travel image
```
The hotel and flight PLPLinkCard can use existing fallbacks immediately while new travel/ images are generated. `fallback-hotel.webp` is a reasonable hotel widget hero; `cat-travel.webp` could serve as resort card fallback.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dynamic hotel search (individual hotel cards) | PLP link generation only (Expedia search page links) | Phase 1 refactor | Hotel data has NO `image_url` or `rating` fields from backend |
| Inline renderXxx() in Message.tsx | BlockRegistry.tsx with BLOCK_RENDERERS dict | Phase 21+ | BlockRegistry is the extension point — do NOT touch UIBlocks function |
| DALL-E 3 image generation | Gemini Imagen 4.0 via REST API | Phase 18 (March 2026) | Use `imagen-4.0-generate-001` endpoint pattern from Phase 18 |
| `Math.random()` for variety | Deterministic static arrays | Phase 19 (MosaicHero) | Prevents SSR hydration errors |
| `overflow-hidden` | `overflow-clip` | Phase 23 | `clip` prevents scroll containment issues |

**Deprecated/outdated:**
- Individual hotel/flight card APIs (Expedia, Booking): Not implemented — all results are PLP search links. `FlightCard` and `HotelCard` TypeScript interfaces exist but backend never sends them currently.
- `product-card-hover` CSS class: was scheduled for removal in Phase 21 Plan 02. Check if already removed before using it in new components.

---

## Open Questions

1. **Should `attractions` block type stay or should a new `resort_cards` block type be added?**
   - What we know: REQUIREMENTS.md says BlockRegistry.tsx structural changes are Out of Scope ("Protected block dispatch architecture")
   - What's unclear: Whether swapping the renderer within BLOCK_RENDERERS counts as "structural change" — it likely does not, since UIBlocks function is untouched
   - Recommendation: Swap the renderer within BLOCK_RENDERERS (one line change). Do not add a new block type.

2. **Does `product-card-hover` CSS class still exist?**
   - What we know: Phase 21 Plan 02 deferred its removal. Phase 23 completed multiple plans.
   - What's unclear: Whether it was ultimately removed in Phase 23.
   - Recommendation: Wave 0 task should grep for `.product-card-hover` in globals.css before using it in new components. Use `hover:shadow-card-hover transition-shadow` pattern as safe alternative.

3. **What region does the `destination` slot contain for a Caribbean query?**
   - What we know: `slots.destination` is a city/region string like "Caribbean" or "Cancun"
   - What's unclear: Whether it's always a city name or can be a broad region ("Caribbean", "Europe")
   - Recommendation: The resort image fallback lookup should handle both: specific city name match first, then broad region keyword match, then generic beach fallback.

4. **"Caribb ean" text wrapping — is it a space in the data or a CSS wrapping issue?**
   - What we know: The CONTEXT.md specifically calls out `"Caribb ean"` with a space mid-word. This is unusual.
   - What's unclear: Whether the backend actually sends "Caribbean" with an embedded space, or whether it's a text-overflow/word-break CSS issue at a specific width.
   - Recommendation: Wave 0 should add `overflow-wrap: break-word` defensively to destination text spans, AND verify backend slot data doesn't contain spaces in destination names.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.17 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm test -- --run tests/travelUI.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRVL-01 | ResortCards renders attraction strings as cards with images | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-02 | ResortCards falls back to generic image when no match | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-03 | PLPLinkCard hotel has hero image element | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-04 | PLPLinkCard hotel CTA reads "Search on Expedia" | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-05 | PLPLinkCard flight CTA reads "Search on Expedia" | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-06 | PLPLinkCard flight destination text doesn't wrap mid-word | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| TRVL-07 | Conclusion block renders with tinted background | unit | `npm test -- --run tests/travelUI.test.tsx` | Wave 0 |
| IMG-04 | Travel hero images exist and are under 200KB | file | `npm test -- --run tests/imageAssets.test.ts` | partial (existing test needs travel/ dir assertion) |

### Sampling Rate
- **Per task commit:** `cd frontend && npm test -- --run tests/travelUI.test.tsx`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/travelUI.test.tsx` — covers TRVL-01 through TRVL-07
- [ ] `frontend/public/images/travel/` directory — needed for image fallback tests
- [ ] Extend `imageAssets.test.ts` with travel image assertions (or add to travelUI.test.tsx)

*(Existing `tests/setup.ts`, `vitest.config.ts`, and all fixtures are in place — no framework install needed.)*

---

## Sources

### Primary (HIGH confidence)
- Direct file inspection: `frontend/components/HotelCards.tsx` — full component structure, data interfaces, current CTA labels
- Direct file inspection: `frontend/components/FlightCards.tsx` — PLPLinkCard route visualization (Caribbean wrapping root cause identified)
- Direct file inspection: `frontend/components/ListBlock.tsx` — current "Must-See Attractions" renderer
- Direct file inspection: `frontend/components/DestinationInfo.tsx` — current destination info renderer with font-serif headers
- Direct file inspection: `frontend/components/blocks/BlockRegistry.tsx` — full BLOCK_RENDERERS dict and UIBlocks function
- Direct file inspection: `backend/mcp_server/tools/travel_compose.py` — confirms attractions is `List[str]`, NO image_url in any travel block
- Direct file inspection: `backend/mcp_server/tools/travel_search_hotels.py` — confirms hotel PLP link shape (no image_url)
- Direct file inspection: `backend/mcp_server/tools/travel_search_flights.py` — confirms flight PLP link shape
- Direct file inspection: `backend/mcp_server/tools/travel_destination_facts.py` — confirms attractions are plain strings from LLM
- Direct file inspection: `frontend/lib/normalizeBlocks.ts` — block normalization (type + data schema)
- Direct file inspection: `frontend/app/globals.css` — CSS variable inventory (--bold-*, --shadow-*, --primary-light, etc.)
- Direct file inspection: `frontend/tailwind.config.ts` — font-sans maps to DM Sans, font-serif maps to Instrument Serif, breakpoints are Tailwind defaults
- Direct file inspection: `frontend/public/images/products/` — existing fallback images confirmed (fallback-hotel.webp, fallback-flight.webp, cat-travel.webp)
- Direct file inspection: `.planning/STATE.md` — project decisions (no Tailwind dark: prefix, raw img tags, overflow-clip, data-theme strategy)

### Secondary (MEDIUM confidence)
- `.planning/phases/24-travel-response-ui-overhaul/24-CONTEXT.md` — PRD decisions about layout, sizing, CTA labels
- `.planning/REQUIREMENTS.md` — BlockRegistry.tsx and Message.tsx structural changes are Out of Scope

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present in package.json
- Architecture: HIGH — all component interfaces and data shapes verified by direct file inspection
- Pitfalls: HIGH — root causes traced to specific file locations and line numbers
- Image strategy: HIGH — static fallback approach confirmed correct given backend returns no image URLs

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable codebase — no external API changes affect this phase)
