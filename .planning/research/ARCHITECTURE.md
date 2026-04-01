# Architecture Research

**Domain:** Visual overhaul integration — Next.js 14 App Router frontend (v3.0 Bold Editorial milestone)
**Researched:** 2026-03-31
**Confidence:** HIGH (direct codebase analysis — all files read from source)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          layout.tsx (RootLayout)                     │
│   Fonts: DM Sans + Instrument Serif via next/font                   │
│   Theme: data-theme attr injected by inline script (no FOUC)        │
│   Wraps: NavLayout → ChatStatusProvider                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       NavLayout.tsx                                  │
│  Desktop: UnifiedTopbar (sticky, md+)                               │
│  Mobile:  MobileHeader (fixed top) + MobileTabBar (fixed bottom)    │
│  Routes excluded from chrome: /admin /privacy /terms /login         │
└───┬──────────────┬─────────────────────┬──────────────────┬─────────┘
    │              │                     │                  │
┌───▼────┐  ┌──────▼──────┐  ┌──────────▼──────┐  ┌───────▼──────┐
│  /     │  │  /browse    │  │  /chat          │  │  /results    │
│ page   │  │  /[category]│  │  page           │  │  /[id]       │
│ (Dis-  │  │  page       │  │  ChatContainer  │  │  Results-    │
│ cover) │  │  BrowseLayout│  │  + MessageList  │  │  MainPanel   │
└───┬────┘  └──────┬──────┘  └──────────┬──────┘  └──────────────┘
    │              │                    │
    │    DiscoverSearchBar        Message.tsx +
    │    ProductCarousel          BlockRegistry
    │    CategoryChipRow          (17 block types)
    │    TrendingCards
    │    CategorySidebar
    │
    ▼
template.tsx — Framer Motion fade transition wraps all routes
```

### CSS Variable Theme Architecture

```
globals.css
├── :root                  — Light mode tokens (default)
├── [data-theme="dark"]    — Dark mode token overrides
├── [data-accent="ocean"]  — Accent palette overrides (6 variants)
├── [data-accent="sunset"] — Primary + accent + shadow-float only
├── [data-accent="neon"]
├── [data-accent="forest"]
├── [data-accent="berry"]
└── Legacy mappings        — --gpt-* vars → semantic vars (MUST PRESERVE)

tailwind.config.ts
├── colors.primary/accent/surface/border/ink — map to CSS vars
├── boxShadow.card/float/editorial/elevated  — map to CSS vars
├── fontFamily.sans/serif/heading             — map to CSS font vars
└── animation.fade-up/card-enter/slide-in    — Tailwind keyframes
```

### Component Responsibility Map

| Component | Location | Responsibility | Touch for v3.0? |
|-----------|----------|---------------|-----------------|
| `NavLayout` | components/ | Layout chrome, theme context | No — stable wrapper |
| `UnifiedTopbar` | components/ | Desktop nav, search, theme toggle | Minor — font weight/sizing only |
| `MobileHeader` | components/ | Mobile top bar | Minor — same as topbar |
| `MobileTabBar` | components/ | Mobile bottom nav | No |
| `layout.tsx` | app/ | Font loading, data-theme init | No — protected |
| `template.tsx` | app/ | Framer Motion page transition | No |
| `page.tsx` (Discover) | app/ | Discover page layout | YES — mosaic hero integration |
| `ProductCarousel` (discover) | components/discover/ | Sliding hero card (5 slides) | YES — major visual upgrade |
| `TrendingCards` | components/discover/ | Grid of topic thumbnails | YES — image upgrade |
| `CategoryChipRow` | components/discover/ | Horizontal chip row | Minor — typography |
| `DiscoverSearchBar` | components/discover/ | Main search input | Minor — border/focus styling |
| `CategoryHero` | components/browse/ | Browse page hero with stats | Minor — typography weight |
| `ResultsProductCard` | components/ | Product card on results panel | YES — major visual upgrade |
| `ResultsMainPanel` | components/ | Right panel on results page | YES — grid/spacing |
| `ProductReview` | components/ | Chat response product card | YES — polish pass |
| `TopPickBlock` | components/ | Featured product block in chat | YES — polish pass |
| `ProductCards` | components/ | Chat product list cards | YES — polish pass |
| `InlineProductCard` | components/ | Compact product row in chat | Minor — padding/image size |
| `BlockRegistry` | components/blocks/ | Dispatches all block types to components | No — logic-only, do not touch |
| `Message.tsx` | components/ | Message bubble + block rendering | No — protected per MEMORY.md |

---

## Integration Points for v3.0 Visual Overhaul

### Integration Point 1: Mosaic Hero on Discover Page

**What exists:** `app/page.tsx` renders a centered single-column layout with:
- `h1` title ("What are you _researching_ today?")
- `CategoryChipRow`
- `ProductCarousel` (a single sliding card component)
- `DiscoverSearchBar`

**What changes:** The mosaic hero replaces or augments the ProductCarousel. The `ProductCarousel` in `components/discover/` is a standalone slideshow component with 5 hardcoded `SLIDES` entries. Images already exist at `public/images/products/*.png`.

**Integration approach:** Create a new `MosaicHero` component at `components/discover/MosaicHero.tsx`. The existing `ProductCarousel` remains for the chat-style block rendering system (the `carousel` block type in `BlockRegistry.tsx` points to a different `components/ProductCarousel.tsx` — note the two ProductCarousel files).

**Naming collision to avoid:** There are TWO `ProductCarousel` components:
1. `components/discover/ProductCarousel.tsx` — the Discover page slideshow (5 slides, hero visual)
2. `components/ProductCarousel.tsx` — the chat response carousel (affiliate product cards, used by BlockRegistry)

These are different components with different interfaces. The v3.0 mosaic hero replaces/augments `components/discover/ProductCarousel.tsx` only.

### Integration Point 2: Product Card Visual Upgrade

**Affected components and their data sources:**

| Component | Data Source | Block Type | Notes |
|-----------|------------|------------|-------|
| `ResultsProductCard` | `ExtractedProduct` from `lib/extractResultsData` | N/A (Results page direct) | Uses `resolveProductImage()` fallback chain |
| `ProductReview` | `product` prop with `affiliate_links[]` | `product_review` | Has image, pros/cons, affiliate links |
| `TopPickBlock` | Named props | `top_pick` | Primary featured card, 140x140 image |
| `ProductCards` | `ProductCard[]` — dual old/new format | `product_cards` | List view with gradient CTA button |
| `InlineProductCard` | `ProductItem[]` | `inline_product_card` | Compact 64px row format |
| `ProductCarousel` (chat) | `Product[]` with affiliate data | `carousel`, `products` | Horizontal scroll carousel |

**Safe to upgrade:** All visual properties (padding, borders, shadows, image size, typography classes). The interface/props contracts must not change.

**Unsafe to touch:** Any logic in `BlockRegistry.tsx`, the `NormalizedBlock` data mapping, or `Message.tsx` render functions.

### Integration Point 3: Bold Color System

**Current token architecture:**
- `globals.css :root` defines all tokens
- `tailwind.config.ts` references them via `var(--*)` syntax
- 6 accent themes override only `--primary`, `--primary-hover`, `--primary-light`, `--accent`, `--accent-hover`, `--accent-light`, `--shadow-float`
- Dark mode overrides backgrounds, text, borders, and semantic colors

**How to add bolder accents:**
New tokens can be added alongside existing ones in `:root`. Do NOT rename or remove existing tokens — the `--gpt-*` legacy mappings must remain (protected by `frontend/tests/designTokens.test.ts`). New tokens for "bold editorial" palette additions (e.g., `--accent-bold`, `--hero-gradient-start`, `--card-highlight`) are safe to add.

**Token test contract (from plan doc):**
Must preserve: `--stream-status-size`, `--stream-status-color`, `--stream-content-color`, `--citation-color`, `--gpt-accent`, `--gpt-text`, `--gpt-background` and utility classes `.stream-status-text`, `.stream-content-text`, `.citation-text`.

### Integration Point 4: AI-Generated Images

**Current image storage structure:**
```
frontend/public/images/
├── products/               — product shots for carousel + trending (PNG)
│   ├── headphones.png      — used by discover carousel + trendingTopics.ts
│   ├── laptop.png
│   ├── shoes.png
│   ├── smart-home.png
│   ├── tokyo.png
│   ├── vacuum.png
│   ├── fallback-*.png      — category fallback icons (6 files)
│   └── bluetooth-speakers.png  — trending topic images (16 files)
│       noise-cancelling-headphones.png
│       robot-vacuums.png
│       ... (16 topic-specific images)
├── topics/                 — same topic images, alternate directory
│   └── (16 files — same as products/ topic set)
├── categories/             — browse category hero images (JPG)
│   ├── electronics.jpg
│   ├── health-wellness.jpg
│   └── ... (10 category images)
└── trending/               — (empty — reserved)
```

**Image references wired in code:**
- `lib/trendingTopics.ts` — 6 entries hardcode `/images/products/*.png` paths
- `components/discover/ProductCarousel.tsx` (discover) — 5 slides hardcode `/images/products/*.png`
- `lib/productImages.ts` — `CATEGORY_PLACEHOLDERS` hardcodes `/images/products/fallback-*.png`
- `components/browse/CategoryHero.tsx` — receives `heroGradient` as CSS gradient string (no image, just color)
- `lib/categoryConfig.ts` — may contain category image paths (check before adding)

**Adding new AI-generated images:**
1. Save to `frontend/public/images/products/[name].png` — this is the established convention
2. For topic-specific images: same directory, named after the topic slug
3. Reference via `/images/products/[name].png` (no `next/image` component used — all are `<img>` tags)
4. Update `lib/trendingTopics.ts` or `components/discover/ProductCarousel.tsx` to reference new paths

**No `next/image` optimization:** The codebase uses raw `<img>` tags throughout, not Next.js `<Image>`. This means no automatic WebP conversion or responsive sizes. Images should be pre-optimized (PNG, reasonable file size ~100-300KB max per image).

---

## Recommended Project Structure (for new v3.0 components)

```
frontend/
├── components/
│   └── discover/
│       ├── MosaicHero.tsx        ← NEW: Shopify-style mosaic hero
│       ├── ProductCarousel.tsx   ← MODIFY: upgraded slides
│       ├── TrendingCards.tsx     ← MODIFY: bolder image presentation
│       ├── CategoryChipRow.tsx   ← MODIFY: typography/spacing
│       └── DiscoverSearchBar.tsx ← MODIFY: border/focus styling
├── app/
│   └── page.tsx                  ← MODIFY: wire MosaicHero into layout
├── public/
│   └── images/
│       └── products/
│           └── [new-ai-images].png ← NEW: generated product imagery
└── app/globals.css               ← MODIFY: new bold color tokens only
```

### Structure Rationale

- **components/discover/:** All new Discover-page components go here. Keeps page-specific components separate from shared chat components.
- **No new CSS files:** All styling goes into existing `globals.css` token additions or Tailwind utility classes inline. Avoids CSS fragmentation.
- **No new lib/ files:** Image paths and topic data already live in `trendingTopics.ts` — extend those rather than creating new data files.

---

## Architectural Patterns

### Pattern 1: CSS Variable Token Extension

**What:** Add new semantic tokens to `:root` in `globals.css` without modifying existing ones.
**When to use:** Adding new color ranges (bold palette), new spacing scales, or new gradient presets.
**Trade-offs:** Keeps backward compat with legacy `--gpt-*` mappings. New tokens aren't automatically dark-mode aware — must add overrides in `[data-theme="dark"]` block too.

**Example:**
```css
/* In :root — safe additions for Bold Editorial */
--hero-bg-start: #1B4DFF;
--hero-bg-end: #E85D3A;
--card-highlight: rgba(27, 77, 255, 0.08);
--bold-heading-weight: 800;

/* Also add in [data-theme="dark"] */
[data-theme="dark"] {
  --hero-bg-start: #3B82F6;
  --hero-bg-end: #F59E0B;
}
```

### Pattern 2: Component Wrapper (not modification)

**What:** For the mosaic hero, create `MosaicHero.tsx` as a new component rather than heavily modifying `ProductCarousel.tsx` (discover).
**When to use:** When the visual treatment is substantially different (mosaic grid vs. single card slideshow).
**Trade-offs:** `page.tsx` decides which to render. Both components can coexist. Reduces risk of breaking existing carousel behavior.

**Example:**
```tsx
// app/page.tsx
import MosaicHero from '@/components/discover/MosaicHero'
// or swap with existing:
// import ProductCarousel from '@/components/discover/ProductCarousel'

// Render as replacement for the carousel slot
<div className="mt-4 max-w-xl mx-auto w-full">
  <MosaicHero />
</div>
```

### Pattern 3: Inline Style for Dynamic Gradients, Tailwind for Static Structure

**What:** Use `style={{ background: gradient }}` for per-product color values. Use Tailwind classes for layout, spacing, border-radius, and typography.
**When to use:** Everywhere. This is the established pattern in `ProductCarousel`, `ResultsProductCard`, `TrendingCards`.
**Trade-offs:** Consistent with existing code. Avoids Tailwind JIT purge issues with dynamic color strings. The `cn()` utility is not in use — use template literals or className concatenation.

**Example:**
```tsx
// Correct — matches existing patterns
<div
  className="rounded-2xl overflow-hidden product-card-hover"
  style={{ background: 'linear-gradient(135deg, #EEF2FF, #E0E7FF)' }}
>
```

### Pattern 4: Avoid `Math.random()` in SSR

**What:** All deterministic values (gradients, badge colors, product ordering) must use stable inputs — index, id, or slug — not `Math.random()`.
**When to use:** Always, on any component that could be server-rendered or hydrated.
**Trade-offs:** Required. `Math.random()` in SSR causes React hydration errors per CLAUDE.md.

**Example:**
```tsx
// Correct — index-based
const GRADIENT_BGS = ['linear-gradient(135deg, #EEF2FF, #E0E7FF)', ...]
const gradient = GRADIENT_BGS[index % GRADIENT_BGS.length]
```

---

## Data Flow

### Discover Page Render Flow

```
page.tsx (SSR shell)
  └── CategorySidebar (static, sidebar)
  └── h1 + subtitle (static text)
  └── CategoryChipRow (static data from lib/)
  └── ProductCarousel / MosaicHero
        └── hardcoded SLIDES array (no API call)
        └── images from /public/images/products/
  └── TrendingCards
        └── trendingTopics from lib/trendingTopics.ts (static)
  └── DiscoverSearchBar
        └── router.push('/chat?q=...') on submit
```

### Chat Response Block Rendering

```
ChatContainer (SSE stream)
  └── MessageList
        └── Message.tsx (per message)
              └── UIBlocks (from BlockRegistry.tsx)
                    └── BLOCK_RENDERERS map
                          └── ProductReview / TopPickBlock / ProductCards
                                └── Product data from LangGraph backend
                                └── resolveProductImage() for fallback images
```

### Image Resolution Fallback Chain

```
API response image_url
  └── valid URL? → use it
  └── null/error?
        └── lookupCuratedImage(name) — match against curatedLinks topic titles
              └── found ASIN? → https://images-na.ssl-images-amazon.com/...
              └── not found?
                    └── detectCategory(name) → /images/products/fallback-[category].png
```

---

## Scaling Considerations

These are frontend-only visual concerns — scaling is irrelevant at this layer. Performance considerations for v3.0:

| Concern | Current Approach | v3.0 Risk | Mitigation |
|---------|-----------------|-----------|------------|
| Image file sizes | Raw PNG, no optimization | Bold editorial images may be larger | Pre-compress to <250KB, use PNG-8 where possible |
| Framer Motion bundle | Already in use (template.tsx, UnifiedTopbar) | Adding more animations increases JS | Reuse existing motion variants, avoid new dependencies |
| CSS specificity | Flat CSS var system | New tokens could conflict with accent overrides | Add to all theme selectors (`:root`, dark, accents) |
| CLS (layout shift) | No `next/image`, no size hints | Large mosaic images can shift layout | Set explicit width/height on all `<img>` tags in mosaic |

---

## Anti-Patterns

### Anti-Pattern 1: Modifying BlockRegistry.tsx or Message.tsx

**What people do:** Touch block rendering logic when upgrading visual polish of product cards.
**Why it's wrong:** `BlockRegistry.tsx` is the central dispatch for all 17 chat block types. `Message.tsx` has explicit protection in project memory ("All render functions in Message.tsx are protected"). Breaking these breaks all chat responses.
**Do this instead:** Modify only the leaf components that BlockRegistry calls: `ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx`, `InlineProductCard.tsx`. Change their visual output, not their interfaces.

### Anti-Pattern 2: Creating a New CSS File

**What people do:** Create `mosaic.css` or `hero-styles.css` for new components.
**Why it's wrong:** The project uses a single `globals.css` for all token definitions and a single `tailwind.config.ts` for utilities. Fragmentation causes specificity conflicts and makes dark mode/accent overrides miss new styles.
**Do this instead:** All new tokens in `globals.css`. All layout/spacing in Tailwind classes inline on components.

### Anti-Pattern 3: Using `next/image` for New Images

**What people do:** Switch to `<Image>` from `next/image` thinking it's "best practice."
**Why it's wrong:** The entire codebase uses raw `<img>` tags. `next/image` requires explicit width/height props and a configured `domains` whitelist in `next.config.js` for external URLs. Mixing `<Image>` and `<img>` creates inconsistency. External product images (Amazon CDN, eBay) would require domains config changes.
**Do this instead:** Use `<img>` consistently. Pre-optimize images before saving to `public/`. For CLS prevention, add explicit `width` and `height` attributes on images where dimensions are known.

### Anti-Pattern 4: Hardcoding Colors Instead of Using CSS Variables

**What people do:** Write `bg-blue-600` or `color: '#1B4DFF'` in new components.
**Why it's wrong:** The theme system (light/dark + 6 accents) is entirely CSS-variable-driven. Hardcoded colors break dark mode and accent switching.
**Do this instead:** Use `var(--primary)`, `var(--accent)`, `var(--surface)` etc. For per-card gradient arrays (like `GRADIENT_BGS` in ResultsProductCard), hardcoded gradient values are acceptable because they're decorative accents that don't participate in the theme system.

### Anti-Pattern 5: Adding Data Fetching to Discover Page

**What people do:** Fetch trending data from an API to make the Discover page "live."
**Why it's wrong:** The Discover page is intentionally static (no backend calls). All content is hardcoded in `trendingTopics.ts` and the `SLIDES` array. Adding fetch introduces loading states, SSR complexity, and potential hydration issues.
**Do this instead:** Update the static data in `lib/trendingTopics.ts` and the `SLIDES` array in `ProductCarousel.tsx` when content needs updating.

---

## Build Order (Dependency Graph)

The visual overhaul has clear dependency relationships. This is the correct sequencing:

```
1. CSS Tokens (globals.css additions)
        ↓ (all components inherit)
2. AI-Generated Images (save to public/images/products/)
        ↓ (carousel + trending reference these)
3. MosaicHero component (new — no dependencies on other new work)
        ↓ (wired into page.tsx)
4. ProductCarousel upgrade (discover) — uses new images
        ↓ (parallel with 3)
4. TrendingCards upgrade — uses new images
        ↓ (parallel with 3, 4)
5. page.tsx layout (wires MosaicHero, adjusts spacing)
        ↓ (depends on 3, 4, 4)
6. ResultsProductCard upgrade (chat/results product cards)
        ↓ (parallel)
6. TopPickBlock upgrade (parallel)
        ↓
6. ProductReview upgrade (parallel)
        ↓
7. Browse page: CategoryHero typography upgrade (lowest priority)
```

**Phase grouping for implementation:**

| Phase | Work | Dependencies |
|-------|------|-------------|
| Phase 1 | CSS token additions (globals.css) | None — do first |
| Phase 2 | AI image generation + saving to public/ | None — parallel with Phase 1 |
| Phase 3 | MosaicHero component creation | Phase 1 (tokens), Phase 2 (images) |
| Phase 4 | Discover page wiring (page.tsx + carousel/trending upgrades) | Phase 3 |
| Phase 5 | Product card polish (ProductReview, TopPickBlock, ProductCards) | Phase 1 only |
| Phase 6 | Browse/results polish (CategoryHero, ResultsProductCard) | Phase 1 only |

---

## Integration Summary: New vs Modified Components

### New Components (create from scratch)

| File | Purpose | Dependencies |
|------|---------|-------------|
| `components/discover/MosaicHero.tsx` | Shopify mosaic grid hero | CSS tokens, new images |

### Modified Components (visual changes only — no interface changes)

| File | Change Scope | Risk | Notes |
|------|------------|------|-------|
| `app/globals.css` | Add new tokens to `:root` and `[data-theme="dark"]` | Low | Must not remove legacy `--gpt-*` vars |
| `app/page.tsx` | Swap or augment ProductCarousel with MosaicHero | Low | Layout adjustment only |
| `components/discover/ProductCarousel.tsx` | Bold visual upgrade, leverage existing images | Low | Static SLIDES array — no data contract |
| `components/discover/TrendingCards.tsx` | Larger thumbnails, bolder typography | Low | Static data from trendingTopics.ts |
| `components/discover/CategoryChipRow.tsx` | Typography/color tokens | Very low | Style-only |
| `components/discover/DiscoverSearchBar.tsx` | Border, focus ring, input height | Very low | Style-only |
| `components/ResultsProductCard.tsx` | Image area, badge styling, spacing | Low | Uses resolveProductImage() — preserve |
| `components/ResultsMainPanel.tsx` | Grid layout, card spacing | Low | Product card grid wrapper |
| `components/ProductReview.tsx` | Card elevation, spacing, image size | Low | Props interface unchanged |
| `components/TopPickBlock.tsx` | Card prominence, image size | Low | Props interface unchanged |
| `components/ProductCards.tsx` | List card polish, CTA button | Low | Dual-format data handling preserved |
| `components/UnifiedTopbar.tsx` | Font weight, subtle spacing | Very low | Logic and nav links unchanged |

### Do Not Touch

| File | Reason |
|------|--------|
| `components/blocks/BlockRegistry.tsx` | Central dispatch — logic protected |
| `components/Message.tsx` | Render functions protected per project memory |
| `app/layout.tsx` | Font loading and data-theme init — stable |
| `app/template.tsx` | Framer Motion transition — stable |
| `lib/normalizeBlocks.ts` | Block normalization logic |
| `lib/chatApi.ts` | SSE streaming client |
| `components/ChatContainer.tsx` | Streaming logic — do not modify |
| `frontend/tests/designTokens.test.ts` | Test contract — must pass after globals.css changes |

---

## Sources

- Direct source analysis: `frontend/app/globals.css`, `tailwind.config.ts`, `app/layout.tsx`, `app/page.tsx`
- Component inventory: `components/discover/`, `components/browse/`, `components/blocks/BlockRegistry.tsx`
- Image asset survey: `frontend/public/images/` directory listing
- Plan document: `docs/superpowers/plans/2026-03-29-frontend-visual-overhaul.md`
- Project context: `.planning/PROJECT.md`
- Next.js config: `frontend/next.config.js`

---
*Architecture research for: ReviewGuide.ai v3.0 Visual Overhaul — Next.js 14 frontend integration*
*Researched: 2026-03-31*
