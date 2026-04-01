# Phase 19: Mosaic Hero - Research

**Researched:** 2026-03-31
**Domain:** CSS Grid mosaic collage hero — Next.js 14 / Tailwind CSS / `<img>` tags / Core Web Vitals
**Confidence:** HIGH (direct codebase inspection; all file paths and constraints verified from source)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| HERO-01 | User sees Shopify-style mosaic collage of product images as landing page hero background | CSS absolute-position + rotate pattern documented; 8 mosaic WebP images confirmed at `/images/products/mosaic-*.webp` |
| HERO-02 | Search bar and headline float centered over mosaic with readable contrast | Gradient overlay technique documented; `page.tsx` layout integration pattern specified |
| HERO-03 | Mosaic uses CSS Grid with tilted/overlapping cards — no additional JS library | Pure CSS pattern confirmed from FEATURES.md; full code example provided with exact rotation values |
| HERO-04 | First visible image uses `loading="eager"` to avoid LCP regression | Confirmed that ALL current carousel images use `loading="lazy"` — HERO-04 fixes this; position 0 must flip to `eager` |
</phase_requirements>

---

## Summary

Phase 19 creates `MosaicHero.tsx`, a new component in `components/discover/` that renders 8 tilted, overlapping product image cards as a full-bleed visual backdrop, with the existing headline and search bar floating over it. This is a pure CSS implementation — no new JS library, no new dependencies — using `position: absolute` within a fixed-height container, `transform: rotate()` for tilt, and a `linear-gradient` overlay for text contrast. The existing `ProductCarousel` in `components/discover/ProductCarousel.tsx` stays mounted below the mosaic as the "Recommended For You" section; the mosaic slot is an additional element injected into `page.tsx` above the headline.

All raw materials are in place: 8 mosaic WebP files (`mosaic-*.webp`) are confirmed at `frontend/public/images/products/`, the bold token system (`--heading-hero`, `--primary`, gradient variables) is live in `globals.css`, and the codebase uses raw `<img>` tags everywhere (not `next/image`). The layout integration is a surgical edit to `app/page.tsx` — a new `<MosaicHero />` block wraps behind the existing hero text, using `position: relative` on the outer wrapper and `position: absolute` on the mosaic itself to place it behind the text without pushing layout flow.

The two critical non-functional risks are LCP regression (first mosaic image must use `loading="eager"`) and CLS (all mosaic image containers must have explicit width/height or `aspect-ratio` — no lazy-loaded images shifting layout). Both are enforced at component creation, not deferred to QA.

**Primary recommendation:** Create `MosaicHero.tsx` as a new isolated component, position it absolutely behind the hero headline/search block using a wrapper in `page.tsx`, use `loading="eager"` on the first tile only, explicit pixel dimensions on all tiles, pure CSS rotation/z-index layout, and a `linear-gradient` overlay at ~40% black opacity for text readability.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CSS `position: absolute` + `transform: rotate()` | N/A (browser native) | Tile tilt and overlap layout | Project constraint: HERO-03 explicitly forbids additional JS library; pure CSS is the correct path |
| Tailwind CSS 3 JIT | Installed | Layout, spacing, responsive classes | Already installed; arbitrary value syntax `[rotate(-7deg)]` available |
| `<img>` (raw HTML) | N/A | Image rendering | Entire codebase uses `<img>` tags — mixing `next/image` would require `next.config.js` domain changes and explicit width/height props |
| `globals.css` CSS variables | In place (Phase 17) | Gradient overlay, text color tokens | Token system is the established pattern; no hardcoded hex for theme-aware values |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Framer Motion | 12.26.2 | Optional entrance animation on mosaic reveal | Use `whileInView` + `opacity: 0 → 1` on mount only — no `layout` prop, no per-tile stagger (mosaic is background, not a scannable list) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `position: absolute` layout | CSS Grid `grid-template-areas` | Grid produces regular non-overlapping layout; absolute positioning is the correct tool for overlapping tilted cards. Grid could be used for the outer structure only. |
| Raw `<img>` | `next/image` `<Image>` | `next/image` requires `next.config.js` `remotePatterns` + explicit sizes; the entire codebase uses raw `<img>`. Consistency wins. |
| Static JSX tile array | Dynamic map over array | Both work; static JSX keeps rotation values co-located with each tile and avoids the need for a lookup array. Static is slightly more readable for 8 tiles. |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Component Structure

```
frontend/
├── components/
│   └── discover/
│       ├── MosaicHero.tsx        ← NEW (this phase)
│       └── ProductCarousel.tsx   ← UNCHANGED (kept below mosaic)
└── app/
    └── page.tsx                  ← MODIFIED: wire MosaicHero into layout
```

### Pattern 1: Absolute-Position Mosaic Behind Hero Text

**What:** The mosaic sits behind the headline and search bar using CSS `position` — the outer wrapper is `relative`, the mosaic is `absolute inset-0`, and the text content is `relative z-10` to float on top.

**When to use:** Whenever a background image collage must not affect the document flow of overlaid text content.

**Example — `page.tsx` integration:**
```tsx
// app/page.tsx  (surgical edit — replaces existing hero section div only)

{/* Hero section — mosaic background + floating text */}
<div className="relative flex flex-col items-center pt-2 sm:pt-8 pb-4 overflow-hidden rounded-2xl">
  {/* Mosaic sits behind everything */}
  <div className="absolute inset-0 z-0">
    <MosaicHero />
  </div>

  {/* Gradient scrim for text readability — sits above mosaic, below text */}
  <div
    className="absolute inset-0 z-[1]"
    style={{ background: 'linear-gradient(to bottom, rgba(250,250,247,0.55) 0%, rgba(250,250,247,0.85) 60%, var(--background) 100%)' }}
  />

  {/* Text content floats on top */}
  <div className="relative z-[2] flex flex-col items-center">
    <h1
      className="font-serif text-[28px] sm:text-4xl md:text-5xl text-center leading-tight tracking-tight animate-fade-up"
      style={{ color: 'var(--text)' }}
    >
      What are you{' '}
      <span className="italic" style={{ color: 'var(--primary)' }}>
        researching
      </span>
      {' '}today?
    </h1>
    <p
      className="text-sm sm:text-[15px] text-center mt-3 max-w-md leading-relaxed"
      style={{ color: 'var(--text-secondary)' }}
    >
      Expert reviews, real data, zero fluff.
    </p>
  </div>
</div>
```

### Pattern 2: MosaicHero Component CSS Layout

**What:** 8 cards positioned absolutely within a fixed-height container. Each card has an explicit width/height, a `transform: rotate()` value, and a `z-index`. The first card uses `loading="eager"` (HERO-04). All others use `loading="lazy"`.

**When to use:** Full-bleed mosaic collage background — tilted product image cards as visual texture.

**Example — `MosaicHero.tsx` component:**
```tsx
// Source: FEATURES.md CSS collage pattern + codebase analysis

'use client'

const MOSAIC_TILES = [
  { src: '/images/products/mosaic-headphones.webp',  alt: 'Headphones',   rotate: '-7deg', x: '-22px', y: '8px',  z: 1,  eager: true  },
  { src: '/images/products/mosaic-laptop.webp',      alt: 'Laptop',       rotate: '4deg',  x: '18px',  y: '-12px', z: 3,  eager: false },
  { src: '/images/products/mosaic-sneakers.webp',    alt: 'Sneakers',     rotate: '-3deg', x: '60px',  y: '18px',  z: 2,  eager: false },
  { src: '/images/products/mosaic-espresso.webp',    alt: 'Coffee',       rotate: '6deg',  x: '-60px', y: '-6px',  z: 2,  eager: false },
  { src: '/images/products/mosaic-smartwatch.webp',  alt: 'Smartwatch',   rotate: '-5deg', x: '110px', y: '4px',   z: 1,  eager: false },
  { src: '/images/products/mosaic-camera.webp',      alt: 'Camera',       rotate: '3deg',  x: '-110px', y: '14px', z: 2,  eager: false },
  { src: '/images/products/mosaic-fitness-gear.webp',alt: 'Fitness',      rotate: '-4deg', x: '160px', y: '-8px',  z: 1,  eager: false },
  { src: '/images/products/mosaic-speaker.webp',     alt: 'Speaker',      rotate: '5deg',  x: '-160px', y: '6px',  z: 2,  eager: false },
]

export default function MosaicHero() {
  return (
    <div
      className="relative w-full overflow-hidden"
      style={{ height: 'clamp(200px, 30vw, 320px)' }}
      aria-hidden="true"
    >
      {MOSAIC_TILES.map((tile) => (
        <div
          key={tile.src}
          className="absolute top-1/2 left-1/2 rounded-xl overflow-hidden shadow-md"
          style={{
            width: '140px',
            height: '140px',
            transform: `translate(calc(-50% + ${tile.x}), calc(-50% + ${tile.y})) rotate(${tile.rotate})`,
            zIndex: tile.z,
            willChange: 'transform',
          }}
        >
          <img
            src={tile.src}
            alt={tile.alt}
            width={140}
            height={140}
            loading={tile.eager ? 'eager' : 'lazy'}
            fetchPriority={tile.eager ? 'high' : 'auto'}
            className="w-full h-full object-cover"
            style={{ display: 'block' }}
          />
        </div>
      ))}
    </div>
  )
}
```

**Key decisions in this example:**
- `aria-hidden="true"` — mosaic is decorative; screen readers skip it
- `width` and `height` on `<img>` — prevents CLS; browser reserves space before load
- `fetchPriority="high"` on first tile — browser hint for LCP candidate
- `willChange: 'transform'` — GPU layer promotion; smooth hover transitions
- `translate(calc(-50% + Xpx), calc(-50% + Ypx))` — all tiles centered on the container midpoint, then offset; reliable across all screen sizes

### Pattern 3: Gradient Scrim for Text Readability

**What:** A semi-transparent gradient div sits between the mosaic (z-index 0) and the text (z-index 2). The gradient fades from nearly transparent at the top to the background color at the bottom, creating a natural reading surface for the headline without harsh black overlay.

**When to use:** Text floating over any image background where image content is variable/unpredictable (different luminance across 8 tiles).

**Example:**
```tsx
// Light mode scrim — fades from ivory at top to full ivory at bottom
style={{ background: 'linear-gradient(to bottom, rgba(250,250,247,0.55) 0%, rgba(250,250,247,0.85) 60%, var(--background) 100%)' }}

// Dark mode scrim — same approach, adjusted for dark background
[data-theme="dark"]: background: linear-gradient(to bottom, rgba(10,12,18,0.55) 0%, rgba(10,12,18,0.85) 60%, var(--background) 100%)
```

To make the scrim theme-aware without JavaScript, add a CSS variable:
```css
/* In globals.css :root */
--mosaic-scrim: linear-gradient(to bottom, rgba(250,250,247,0.55) 0%, rgba(250,250,247,0.85) 60%, #FAFAF7 100%);

/* In globals.css [data-theme="dark"] */
--mosaic-scrim: linear-gradient(to bottom, rgba(10,12,18,0.55) 0%, rgba(10,12,18,0.85) 60%, #0A0C12 100%);
```

Then in the component: `style={{ background: 'var(--mosaic-scrim)' }}`.

### Anti-Patterns to Avoid

- **`Math.random()` for rotation values:** Causes React hydration mismatch — server and client produce different rotations. Use a static constant array (see MOSAIC_TILES above).
- **`next/image <Image>` for mosaic tiles:** Requires `next.config.js` `remotePatterns` and explicit `sizes` prop. The codebase uses raw `<img>` exclusively. Do not introduce `<Image>` for local public assets.
- **`loading="lazy"` on the first tile:** Violates HERO-04 and causes LCP regression. The first tile in the MOSAIC_TILES array MUST use `loading="eager"` and `fetchPriority="high"`.
- **CSS `transform` on container instead of individual tiles:** Setting `rotate` on the outer wrapper rotates the entire mosaic as a block. Rotation must be per-tile.
- **Adding Framer Motion `layout` prop to tiles:** Not needed; tiles are statically positioned. `layout` triggers expensive layout recalculation.
- **New CSS file for mosaic styles:** Project convention is single `globals.css` for token additions and Tailwind utilities inline on components. No `mosaic.css` file.
- **`position: fixed` on the mosaic wrapper:** Use `position: absolute` inside the `relative` hero section. `fixed` breaks when the page scrolls.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Overlapping tilted cards | Custom JS animation or canvas | CSS `transform: rotate()` + `position: absolute` + `z-index` | Browser handles GPU-accelerated transforms natively; zero JS overhead; predictable across devices |
| Gradient text scrim | Complex image analysis, dynamic opacity | Fixed `linear-gradient` CSS with `rgba()` values | Image luminance varies but a well-tuned static gradient at ~55% top / ~85% bottom covers the readable middle ground for editorial images of the type generated in Phase 18 |
| Theme-aware scrim | JS theme detection | CSS variable `--mosaic-scrim` in `:root` and `[data-theme="dark"]` | The data-theme CSS variable system is already built; this pattern is established for all other theme-sensitive values |

**Key insight:** The mosaic is decorative background texture, not an interactive product grid. CSS-only is the complete solution — no JS positioning library, no canvas, no IntersectionObserver needed.

---

## Common Pitfalls

### Pitfall 1: CLS from Images Without Explicit Dimensions

**What goes wrong:** If `<img>` tags lack `width` and `height` attributes (or `aspect-ratio` CSS), the browser renders the tile containers at 0x0 until the image loads, then reflows the layout — causing a CLS score above 0.1.

**Why it happens:** Without size hints, the browser cannot reserve space for images during HTML parsing. This is the #1 CLS cause on image-heavy pages.

**How to avoid:** Set explicit `width={140}` and `height={140}` on every `<img>` in the mosaic. The tile container also has explicit `width: 140px; height: 140px` in the inline style. Both are required.

**Warning signs:** Lighthouse CLS > 0.1 on mobile; layout appears to "jump" when tiles load.

### Pitfall 2: LCP Regression from `loading="lazy"` on Visible Images

**What goes wrong:** The current `ProductCarousel` uses `loading="lazy"` on ALL slides (confirmed at `ProductCarousel.tsx` line 193). If the mosaic hero replaces or precedes the carousel without setting `loading="eager"` on the first tile, the browser deprioritizes the first visible image. LCP measures the largest visible content element — if it is lazy-loaded, LCP time increases by 300–800ms on mobile.

**Why it happens:** `loading="lazy"` tells the browser to defer the fetch until the image enters the viewport. For above-the-fold images, this defeats the browser's preload scanner.

**How to avoid:** MOSAIC_TILES[0] (`mosaic-headphones.webp`) must use `loading="eager"` and `fetchPriority="high"`. All other tiles can remain `loading="lazy"`.

**Warning signs:** Lighthouse LCP > 2.5s on mobile; Chrome DevTools Performance panel shows first mosaic image loading after FCP.

### Pitfall 3: Dark Mode Scrim Showing Wrong Background Color

**What goes wrong:** If the scrim gradient hardcodes `#FAFAF7` (light mode ivory), dark mode users see a light band at the bottom of the mosaic section where the gradient fades to the solid background color.

**Why it happens:** Dark mode background is `#0A0C12` (deep navy-black), not ivory. A hardcoded `#FAFAF7` fade creates a light patch on dark backgrounds.

**How to avoid:** Use the CSS variable approach: add `--mosaic-scrim` to both `:root` and `[data-theme="dark"]` in `globals.css`. The component uses `style={{ background: 'var(--mosaic-scrim)' }}`.

**Warning signs:** Manually toggle dark mode in the browser — the bottom of the hero section shows a light stripe on dark backgrounds.

### Pitfall 4: Tile Overflow Clipping Content Incorrectly

**What goes wrong:** `overflow: hidden` on the mosaic container clips the rotated edges of corner tiles, making the collage look abruptly cut off rather than naturally bleeding to the viewport edge.

**Why it happens:** Rotated tiles extend slightly beyond their `width`/`height` bounding box. Container `overflow: hidden` clips at the container edge, not the tile's rotated footprint.

**How to avoid:** Set `overflow: visible` on the mosaic container (not `overflow: hidden`). The outer hero wrapper should have `overflow: hidden` with enough height to contain the visual bleed. Alternatively, add `padding` to the container to accommodate tile bleed, then use `overflow: hidden` on the wrapper one level above.

**Warning signs:** Tile edges appear sharply cut at the mosaic container boundary instead of fading naturally.

### Pitfall 5: Existing `discoverScreen.test.tsx` Tests Break

**What goes wrong:** The existing `discoverScreen.test.tsx` (DISC-01 through DISC-05) tests `render(<DiscoverPage />)` and queries for specific elements. If `MosaicHero` imports fail (wrong path, missing file) or if the `page.tsx` restructure removes the italic `researching` span or the subline text, these tests go red.

**Why it happens:** The tests verify specific DOM structure in `page.tsx`. Restructuring the hero section must preserve: the italic span containing "researching" and the text "Expert reviews, real data, zero fluff." (verified at `discoverScreen.test.tsx` lines 47–63).

**How to avoid:** Do not remove or restructure the `<h1>` text or the `<p>` subline text during the mosaic wiring in `page.tsx`. The mosaic is an additive layer, not a replacement for the text content. Run `npm run test:run` after editing `page.tsx`.

**Warning signs:** `discoverScreen.test.tsx` DISC-01 fails with "italic element not found" or "subline text not found".

---

## Code Examples

### Current `page.tsx` Hero Section (Source of Truth)

```tsx
// Current state — hero section in app/page.tsx (lines 26–43)
// Source: direct codebase read 2026-03-31
<div className="flex flex-col items-center pt-2 sm:pt-8 pb-4">
  <h1
    className="font-serif text-[28px] sm:text-4xl md:text-5xl text-center leading-tight tracking-tight animate-fade-up"
    style={{ color: 'var(--text)' }}
  >
    What are you{' '}
    <span className="italic" style={{ color: 'var(--primary)' }}>
      researching
    </span>
    {' '}today?
  </h1>
  <p
    className="text-sm sm:text-[15px] text-center mt-3 max-w-md leading-relaxed"
    style={{ color: 'var(--text-secondary)' }}
  >
    Expert reviews, real data, zero fluff.
  </p>
</div>
```

The `<h1>` content and `<p>` subline are protected — they are tested by `discoverScreen.test.tsx`. The mosaic is placed in the background of this section without touching the text nodes.

### Confirmed Available Mosaic Images

```
/images/products/mosaic-headphones.webp   ← Use for tile[0] with loading="eager"
/images/products/mosaic-laptop.webp
/images/products/mosaic-sneakers.webp
/images/products/mosaic-espresso.webp
/images/products/mosaic-smartwatch.webp
/images/products/mosaic-camera.webp
/images/products/mosaic-fitness-gear.webp
/images/products/mosaic-speaker.webp
```

All 8 confirmed present via directory listing 2026-03-31.

### CSS Variables Available for Mosaic (Phase 17 tokens — already in `globals.css`)

```css
/* Confirmed in :root — use for gradient overlay */
--background: #FAFAF7;       /* Light mode base — use for scrim fade-to */
--primary: #1B4DFF;          /* Deep Indigo-Blue — optional accent band */
--shadow-md: 0 4px 12px rgba(28,25,23,0.07), 0 2px 4px rgba(28,25,23,0.04);

/* Confirmed in [data-theme="dark"] */
--background: #0A0C12;       /* Dark mode base — use for dark scrim fade-to */
```

New tokens to add to `globals.css` for the mosaic scrim (add to both `:root` and `[data-theme="dark"]`):
```css
/* :root */
--mosaic-scrim: linear-gradient(to bottom, rgba(250,250,247,0.45) 0%, rgba(250,250,247,0.80) 55%, #FAFAF7 100%);

/* [data-theme="dark"] */
--mosaic-scrim: linear-gradient(to bottom, rgba(10,12,18,0.45) 0%, rgba(10,12,18,0.80) 55%, #0A0C12 100%);
```

### FEATURES.md Mosaic CSS Reference (verified)

```css
/* Source: .planning/research/FEATURES.md — CSS Mosaic Collage pattern */
.mosaic-hero {
  position: relative;
  height: clamp(280px, 38vw, 400px);
  overflow: visible;
}

.mosaic-card:nth-child(1) { transform: rotate(-7deg) translate(-24px, 12px); z-index: 1; }
.mosaic-card:nth-child(2) { transform: rotate(3deg) translate(0, -8px);      z-index: 3; }
.mosaic-card:nth-child(3) { transform: rotate(-3deg) translate(24px, 16px);  z-index: 2; }
```

The inline-style version (translate inside the component, rotation from static array) is preferred over CSS class nth-child because it keeps each tile's rotation co-located with its image data in the MOSAIC_TILES array.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hero: heading + carousel card stacked vertically | Mosaic background + floating text | Phase 19 | First-impression visual richness before user reads anything |
| `ProductCarousel.tsx` as sole hero visual | `MosaicHero.tsx` as background + `ProductCarousel` below | Phase 19 | Mosaic creates atmosphere; carousel retains "Recommended For You" editorial curation |
| `loading="lazy"` on all carousel images | `loading="eager"` on first visible image | Phase 19 (HERO-04) | Fixes known LCP regression risk flagged in research |

**Note:** The `ProductCarousel` (discover variant) is **kept** in `page.tsx` below the mosaic hero section. The mosaic replaces the blank space above the headline, not the carousel. The carousel retains its "Recommended For You" editorial function.

---

## Open Questions

1. **Mosaic tile hover behavior**
   - What we know: FEATURES.md documents an optional `scale(1.04)` on the center card (z-index 3) with other cards doing `scale(0.97)` — a "focus-and-retreat" effect
   - What's unclear: Whether the mosaic should be interactive at all (it's `aria-hidden="true"`; HERO-01 says "background")
   - Recommendation: Start with no hover effect (pure background). The mosaic's job is atmosphere, not interaction. Hover interaction can be added in Phase 22 (Visual QA) if it feels warranted.

2. **Exact tile rotation values and positions**
   - What we know: FEATURES.md gives 3-tile example; the component will have 8 tiles; positions need to be tuned visually
   - What's unclear: Final pixel offsets for a balanced visual composition across mobile/desktop
   - Recommendation: Use the values in the Pattern 2 code example above as a starting point; expect one visual tuning pass after first render. This is normal — the planner should include a "visual tuning" task step.

3. **Whether to show the mosaic on mobile**
   - What we know: `page.tsx` has mobile-specific padding (`pt-16 md:pt-0`); the mosaic container uses `clamp()` for height
   - What's unclear: Whether 8 tiles in a fixed-height container looks good on 375px-wide mobile screens (tiles may crowd)
   - Recommendation: Reduce to 5 tiles on mobile via responsive CSS (`hidden` on 3 outer tiles below `sm:`). Implement from the start to avoid mobile CLS investigation later.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.17 |
| Config file | `frontend/vitest.config.ts` (implied by package.json scripts) |
| Quick run command | `cd frontend && npm run test:run -- tests/discoverScreen.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HERO-01 | MosaicHero component renders in the DOM on `/` route | unit | `cd frontend && npm run test:run -- tests/discoverScreen.test.tsx` | ❌ Wave 0 gap — new test needed |
| HERO-02 | Headline and subline text remain visible and readable over mosaic (DOM order) | unit | `cd frontend && npm run test:run -- tests/discoverScreen.test.tsx` | ✅ Covered by DISC-01 (italic span + subline text assertions pass as long as text stays in DOM) |
| HERO-03 | No additional JS library imported in MosaicHero.tsx | manual | Inspect `import` statements in `MosaicHero.tsx` | ❌ Wave 0 gap — manual-only check |
| HERO-04 | First mosaic image uses `loading="eager"` attribute | unit | `cd frontend && npm run test:run -- tests/mosaicHero.test.tsx` | ❌ Wave 0 gap — new test needed |

### Sampling Rate

- **Per task commit:** `cd frontend && npm run test:run -- tests/discoverScreen.test.tsx`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/tests/mosaicHero.test.tsx` — covers HERO-01 (MosaicHero renders) and HERO-04 (first img has `loading="eager"`)
  - Test: render `<MosaicHero />`, assert at least one `img` element exists with `loading="eager"`
  - Test: assert all img elements have explicit `width` and `height` attributes (CLS prevention)
  - Test: assert `aria-hidden="true"` on the root element (accessibility)

---

## Sources

### Primary (HIGH confidence)

- Direct codebase read: `frontend/app/page.tsx` — current hero section structure, `ProductCarousel` import
- Direct codebase read: `frontend/components/discover/ProductCarousel.tsx` — `loading="lazy"` on all slide images confirmed at line 193
- Direct codebase read: `frontend/app/globals.css` — full token inventory, `--mosaic-scrim` token not yet present (Wave 0 gap), `--background` values confirmed for both light/dark
- Directory listing: `frontend/public/images/products/` — all 8 `mosaic-*.webp` files confirmed present
- `.planning/research/FEATURES.md` — CSS mosaic collage pattern with exact rotate values; stagger animation variants; pitfall documentation
- `.planning/research/ARCHITECTURE.md` — `MosaicHero.tsx` placement, naming collision warning between two ProductCarousel components, page.tsx render flow, anti-patterns
- `.planning/research/SUMMARY.md` — LCP/CLS pitfall documentation, Lighthouse targets (LCP < 2.5s, CLS < 0.1)
- `frontend/tests/discoverScreen.test.tsx` — DISC-01 assertions that must survive `page.tsx` edits (italic span + subline text)
- `frontend/tests/imageAssets.test.ts` — EXPECTED_MOSAIC_FILES list confirms all 8 mosaic filenames
- `.planning/REQUIREMENTS.md` — HERO-01 through HERO-04 requirement text

### Secondary (MEDIUM confidence)

- `.planning/research/SUMMARY.md` (Phase 3 rationale section) — `loading="eager"` + `fetchPriority="high"` recommendation for first mosaic image; Lighthouse CLS/LCP targets

---

## Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Standard stack | HIGH | Direct codebase analysis; confirmed `<img>` usage pattern; no new dependencies needed |
| Architecture | HIGH | `page.tsx` read directly; integration approach specified with exact line-level context |
| Mosaic CSS pattern | HIGH | FEATURES.md documents the exact CSS approach; confirmed against browser-native CSS (no library) |
| Pitfalls | HIGH | `loading="lazy"` on carousel images confirmed in source code; `discoverScreen.test.tsx` assertions verified; dark mode scrim issue derived from confirmed `--background` token values |
| Core Web Vitals targets | MEDIUM | LCP < 2.5s / CLS < 0.1 targets from SUMMARY.md research (sourced from Lighthouse documentation); implementation-specific values cannot be confirmed until component renders |

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable CSS pattern; no rapidly-changing dependencies)
