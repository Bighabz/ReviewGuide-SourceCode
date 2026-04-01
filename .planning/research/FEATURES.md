# Feature Research

**Domain:** E-commerce visual refresh — bold editorial product discovery UI
**Researched:** 2026-03-31
**Confidence:** HIGH (existing codebase fully inspected; CSS/animation patterns verified against current docs and live ecosystem search)

---

## Context: What Already Exists

This is a visual overhaul of an existing product, not a greenfield build. The current state determines
the true complexity of each feature.

| Component | Current State | Overhaul Target |
|-----------|---------------|-----------------|
| Homepage hero | Serif heading + category chips + carousel card + search bar (stacked vertically, modest scale) | Shopify-style mosaic product collage above the fold with bold accent band |
| Product carousel | Single-card slider with gradient hero area, auto-rotate, dot indicators | Wider cards, bolder color blocks, real imagery already wired in |
| Trending cards | 48x48 thumbnail + title/subtitle list | Larger image tiles, stronger visual hierarchy |
| ProductReview | Pros/cons/rating/affiliate links in white card | Premium spacing, better image area, cleaner "Where to Buy" section |
| TopPickBlock | Primary-bordered card with expandable pros/cons | Larger product image strip, bolder badge treatment |
| ProductCards | Editorial serif heading with rank number, inline pros/cons paragraph | Same structure, more visual separation, better image containers |
| CategoryHero | Serif h1 + stat row, flat background | Needs background image injection with gradient overlay, bolder h1 size |
| Browse pages | Category gradient chips + content rows | Background image overlays, stronger section dividers |
| Chat page | Functional, well-themed with streaming SSE | Subtle className polish only — structure is protected |

**Design token system is complete.** CSS variables are fully in place in `globals.css`.
Framer Motion v12.26.2 is installed and already used in 7 components.
22 AI-generated product images exist in `public/images/products/` and `public/images/topics/`.
10 category images exist in `public/images/categories/`. The raw material is ready.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that premium editorial shopping sites always have. Missing these makes the refresh feel unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hero that fills the viewport on load | Users judge visual quality in under 0.3 seconds; a full-bleed hero is the first signal of polish | MEDIUM | Currently the homepage stacks small components vertically. Needs a layout change to add a collage section before the search bar |
| Product images in every card | Placeholder gradient-icon cards feel unfinished; users associate images with credibility | LOW | All images already generated and on disk. The gap is wiring fallback logic uniformly across all card types |
| Consistent spacing rhythm | Inconsistent padding and gap sizes read as unpolished even when individual components look fine | LOW | Token system is in place. Mostly an audit pass to enforce spacing grid using existing Tailwind scale |
| Clear dominant price display | Price must be the most visually prominent number in any purchase-intent card | LOW | Already implemented in most cards; TopPickBlock and ProductCards need size increase toward `text-2xl` |
| Hover feedback on all interactive cards | Every card/button must give visual feedback on hover; missing feedback feels broken on a premium site | LOW | `.product-card-hover` class exists but is not applied consistently — needs an audit pass |
| Dark mode parity | Dark mode is live and user-accessible today; broken dark states undermine the premium feel | MEDIUM | Several components use hardcoded `text-green-700` / `text-red-700` / `text-emerald-600` that render poorly on dark surfaces. These need conversion to CSS variable tokens. |
| Mobile-first card sizing | Cards are sized for desktop and squeezed on mobile rather than designed mobile-first | MEDIUM | The carousel and trending cards need explicit mobile breakpoints with full-width or near-full-width layout |
| Affiliate disclosure near purchase CTAs | FTC-required disclosure must remain visible near buy buttons | LOW | Already exists as a small `text-muted` line; its placement is correct through any restyling |

### Differentiators (Competitive Advantage)

Features that set ReviewGuide apart from generic AI chat and comparison sites on first impression.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Shopify-style mosaic collage hero | Creates an immediate "premium curated product site" impression; overlapping tilted cards with bold colors trigger editorial credibility before a word is read | HIGH | Pure CSS: `transform: rotate(-Xdeg)` + `z-index` layering + `position: absolute` within a fixed-height container. No library needed. The 22 existing AI images are the raw material. High complexity relative to this milestone because it requires a new page section layout, not just component restyling. |
| AI-generated category images as browse hero backgrounds | Browse pages feel like magazine covers rather than search results; makes each category feel editorially curated | MEDIUM | Images exist in `/public/images/categories/`. CategoryHero needs background image injection with a `linear-gradient` overlay for text legibility. WCAG AA contrast must be verified against overlay. |
| Bold fluid typography scale | Fluid headings that scale from 2rem to 5rem create editorial energy at every viewport width; size contrast between headline and body is the most recognizable quality signal in editorial design | LOW | Tailwind already has `text-5xl` through `text-7xl`. The homepage h1 is currently capped at `md:text-5xl`. Push browse category heroes to `lg:text-6xl` or `clamp(2.5rem, 5vw, 4.5rem)` in globals.css. |
| Section eyebrow / label treatment | Small all-caps `tracking-widest` labels above section headings are a print-magazine pattern that signals editorial authority | LOW | Pattern already used in the carousel (`RECOMMENDED FOR YOU`) and category stats. Needs consistent application across every section header across all pages. |
| Staggered card entrance animations | Product grids that reveal with per-card stagger delay feel alive versus a static content dump; this is now a baseline expectation from well-funded competitors like Wirecutter and Perplexity | LOW | Framer Motion stagger is already used. Apply `staggerChildren: 0.05` + `y: 12 → 0` to ProductCards and TrendingCards. Keep total duration under 300ms (6 items × 50ms) to feel elegant not slow. |
| Rank number as large decorative element | Wirecutter uses large rank numbers as visual anchors; makes ranked lists scannable and feels authoritative versus a flat list | LOW | Already exists as inline `{displayRank}.` in ProductCards. Increase to `text-4xl` in `text-muted` as a decorative offset aside, not inline with the title text. |
| "Where to Buy" max-3 with clean merchant labels | Cluttered affiliate link sections with raw merchant identifiers like "eBay (lawrenow-0)" look amateur; 3 clean, labeled options with visual separation feel premium | LOW | Merchant name cleaning regex already exists in ProductReview.tsx. Enforce max-3 rule at render level and add merchant icon/logo hints using a small lookup map. |
| Per-category accent color injection | Electronics feels blue, Travel feels amber, Fitness feels green — each browse page has a distinct mood while sharing identical component structure | LOW | `CategoryHero` already accepts `heroGradient` and extracts an accent color. This pattern needs to flow down to section dividers, card left borders, and stat text on browse pages. The `[data-accent]` system in globals.css is already fully implemented for the full site mood; per-category is a scoped subset of that. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full page transition animations | Feels modern and app-like | Framer Motion `AnimatePresence` page transitions in Next.js 14 App Router frequently cause hydration mismatches and content flicker, especially with SSR. The effort-to-reward ratio is poor for a content site where users mostly stay on one page per session. | Use per-component enter animations (cards, heroes). These are contained, safe, and provide 90% of the perceived quality. |
| Auto-playing video backgrounds | Creates strong visual impact | Video backgrounds destroy Core Web Vitals (LCP, CLS). Mobile browsers often block autoplay entirely. The animated logo MP4 that already exists in `/public/images/` should remain off the critical render path. | Use AI-generated static images with a CSS `scale` on-load transition (transform-only, GPU-accelerated, 600ms ease-out). |
| Infinite scroll on product lists | Feels modern | ReviewGuide responses are bounded — the AI returns 3-8 products per query. Infinite scroll infrastructure adds significant complexity for zero payoff on bounded lists. | Keep explicit lists; use stagger animations to make bounded lists feel dynamic. |
| Real-time price scraping in product cards | Live pricing feels more trustworthy | Not feasible without Amazon PA-API approval. Stale scraped prices violate affiliate terms and mislead users. | Display prices only from affiliate API responses (already implemented); show "Check price" CTA when price is unavailable. |
| Glassmorphism across all card surfaces | Trendy, feels premium | `backdrop-filter: blur()` causes severe performance degradation on mobile and low-end Android. The existing `.glass` utility is correctly scoped to the floating topbar only. | Reserve glass effect to the topbar and modal overlays. Use opaque white/surface-elevated cards everywhere else. |
| Custom cursor / pointer effects | High-end editorial sites use these | Adds continuous JS overhead on every mouse move event. Breaks for keyboard and switch-access users. Feels out of place for a utilitarian research tool where users are in decision-making mode, not exploring a portfolio. | Achieve premium feel through typography scale, spacing rhythm, and color confidence rather than cursor tricks. |
| Structural changes to chat page | Chat is the core product; visual refresh should reach it | The SSE streaming logic in ChatContainer.tsx and Message.tsx is complex and fragile. MEMORY.md explicitly marks render functions in Message.tsx as protected. Any structural wrapping risks breaking the streaming pipeline. | Apply `className` polish only to chat: update colors, borders, spacing. Never add motion.div wrappers or restructure the render tree inside Message.tsx. |

---

## Feature Dependencies

```
Mosaic Collage Hero
    └──requires──> AI-generated product images (DONE — 22 images on disk)
    └──requires──> Fixed-height collage container section (new layout in page.tsx)
    └──requires──> CSS rotation transforms per card (no new dependency)

Bold Typography Scale
    └──requires──> Instrument Serif loaded (DONE — in layout.tsx)
    └──enhances──> CategoryHero (larger h1)
    └──enhances──> Mosaic Collage Hero (oversized heading adjacent to collage)

Staggered Card Animations
    └──requires──> Framer Motion (DONE — v12.26.2 installed)
    └──enhances──> ProductCards list
    └──enhances──> TrendingCards grid
    └──conflicts──> Chat page SSE streaming (DO NOT apply stagger inside Message.tsx renders)

Category Accent Color System
    └──requires──> CSS variable token system (DONE)
    └──enhances──> CategoryHero section dividers
    └──enhances──> Browse ContentRow headers
    └──enhances──> ProductCards rank number color

"Where to Buy" Deduplication
    └──requires──> Affiliate link data from backend API (existing)
    └──enhances──> ProductReview merchant section
    └──enhances──> TopPickBlock buy CTA

AI-Generated Category Hero Backgrounds
    └──requires──> Category images on disk (DONE — 10 images in /public/images/categories/)
    └──requires──> Gradient overlay for text legibility
    └──requires──> WCAG AA contrast verification against overlay+image combination

Dark Mode Parity
    └──requires──> Converting hardcoded Tailwind color classes to CSS var() tokens
    └──blocks──> any release if skipped — dark mode is live today
```

### Dependency Notes

- **Mosaic collage hero is unblocked.** All 22 images exist on disk. The only work is the new layout section in `page.tsx` and the CSS positioning.
- **Stagger animations must not touch chat.** The chat SSE renderer builds DOM dynamically during streaming. Framer Motion AnimatePresence wrapping these nodes risks unmounting/remounting mid-stream. Apply stagger only to pre-rendered static lists.
- **Dark mode parity blocks any release.** Dark mode is live and user-toggled today. Hardcoded `text-green-700`, `text-red-700`, `text-emerald-600` in ProductReview.tsx, TopPickBlock.tsx, and ProductCards.tsx appear at full saturation on dark near-black surfaces. Must convert to `var(--success)`, `var(--accent)`, and `var(--error)` using the existing token system. The data-theme="dark" tokens for these values are already defined in globals.css.

---

## MVP Definition

### Launch With (this milestone — bold visual refresh)

- [ ] Mosaic collage hero on homepage — first-impression differentiator; 3 tilted overlapping cards over a bold accent band, CSS only
- [ ] Bold typography scale — push h1 to `clamp(2.5rem, 5vw, 4.5rem)` on browse heroes; cheapest high-impact change
- [ ] ProductReview premium polish — better image sizing, tighter "Where to Buy" (max 3, clean merchant names)
- [ ] Category hero background images — 10 images exist; applying them with gradient overlay transforms browse pages
- [ ] Dark mode hardcoded-color fixes — live issue today; must ship before any refresh claims to be complete
- [ ] Staggered card entrance animations on product grids — Framer Motion already installed; 20 lines of code for high perceived-quality return

### Add After Validation (v1.x)

- [ ] Section eyebrow label consistency audit — trigger: QA pass after core refresh ships; ensure all section headers use the `UPPERCASE 11px tracking-widest` pattern from the carousel
- [ ] Accent color per browse category flowing to dividers/borders — trigger: once category hero backgrounds are live, extend accent color downstream
- [ ] "Where to Buy" max-3 enforcement — trigger: when affiliate providers return multiple sources for the same product (currently eBay-only, so rarely triggered)
- [ ] Rank number as large decorative element — trigger: user testing feedback on product list scannability

### Future Consideration (v2+)

- [ ] Mosaic collage personalized to user query context — requires session state and dynamic image selection; defer until user accounts exist
- [ ] Video hero (animated logo or product reel) — Core Web Vitals impact requires measurement infrastructure before enabling; not yet worth the risk
- [ ] Full per-category theme (complete page mood via `[data-accent]`) — the token system is ready; wiring it to browse category routing is a v2 feature when vertical coverage expands

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Dark mode hardcoded-color fixes | HIGH | LOW | P1 |
| Bold typography scale (h1 increase) | HIGH | LOW | P1 |
| Category hero background images | HIGH | LOW | P1 |
| ProductReview premium card polish | HIGH | LOW | P1 |
| Mosaic collage hero (homepage) | HIGH | MEDIUM | P1 |
| Staggered card entrance animations | MEDIUM | LOW | P1 |
| "Where to Buy" dedup + max-3 | MEDIUM | LOW | P1 |
| Section eyebrow label consistency | LOW | LOW | P2 |
| Accent color per category (dividers) | MEDIUM | LOW | P2 |
| Rank number as decorative element | LOW | LOW | P2 |
| Mosaic hero personalization | MEDIUM | HIGH | P3 |
| Video hero backgrounds | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for this milestone — constitutes the "bold editorial refresh"
- P2: Polish pass after core ships — improves consistency without risk
- P3: Future milestone — requires infrastructure not worth building now

---

## Competitor Feature Analysis

| Feature | Wirecutter (NYT) | Shopify Free Trial Page | Our Approach |
|---------|-----------------|------------------------|--------------|
| Hero | Large editorial serif h1 (48px+), subhead, no product imagery in hero | Product mosaic collage — multiple images overlapping at angles over a bold saturated color band | Hybrid: mosaic collage as the image section, editorial serif heading overlaid or adjacent. Bold but does not obscure search bar. |
| Product cards | Clean ranked list, large decorative rank number, tight prose description, single "See it" CTA | Not applicable (marketing page) | Rank number as large serif aside, prose pros/cons, single gradient CTA — already structurally close. Need size up and image area improvement. |
| Category landing | Section headings with accent rule, editorial prose intro paragraph | — | Accent bar already exists in CategoryHero. Need to size up the heading and add background image with overlay. |
| Typography contrast | Very large h1, dramatic contrast between h1 and body text | Bold headline over collage | Push h1 to `lg:text-6xl` on browse heroes. Homepage h1 can stay restrained since the collage provides visual energy. |
| Animations | Subtle hover state on cards only; no entrance animations | Subtle parallax on mosaic scroll | Framer Motion stagger entrance on product grids. No scroll parallax — too heavy for mobile. |
| Color | Black/white with amber accent; strong value contrast | Bold saturated brand blue + white | Maintain warm ivory base. Inject bold accent bands (terracotta or deep indigo) behind the collage hero. Product cards stay on white surfaces. |

---

## Key CSS and Animation Patterns (Implementation Reference)

### Mosaic Collage — CSS Implementation

No JavaScript or library needed. Cards use `position: absolute` within a `position: relative`
fixed-height container. `transform: rotate()` creates the tilt. `z-index` layering creates overlap.
`will-change: transform` ensures GPU layer promotion.

```css
.mosaic-hero {
  position: relative;
  height: clamp(280px, 38vw, 400px);
  overflow: visible; /* let edge cards bleed slightly beyond container */
}

/* Alternating rotations per card create rhythm without looking random */
.mosaic-card:nth-child(1) { transform: rotate(-7deg) translate(-24px, 12px); z-index: 1; }
.mosaic-card:nth-child(2) { transform: rotate(3deg) translate(0, -8px);      z-index: 3; }
.mosaic-card:nth-child(3) { transform: rotate(-3deg) translate(24px, 16px);  z-index: 2; }
```

On hover, the centered card (z-index 3) can `scale(1.04)` with a `transition: transform 300ms ease`.
The other cards can simultaneously `scale(0.97)` to create a focus-and-retreat effect.
All transitions must use `transform` and `opacity` only — no width/height/top/left transitions.

### Bold Typography — CSS Clamp

```css
/* globals.css — fluid editorial headline for browse pages */
.editorial-hero-h1 {
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  font-family: var(--font-instrument), Georgia, serif;
  letter-spacing: -0.03em;
  line-height: 1.05;
}
```

The homepage h1 is currently `text-[28px] sm:text-4xl md:text-5xl`. Push the desktop ceiling to
`lg:text-6xl` on browse heroes. The homepage heading can remain restrained because the mosaic
collage provides the visual energy — the heading there is a supporting element, not the hero.

### Stagger Animation — Framer Motion Pattern

```typescript
// Parent motion container variant
const listVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
}

// Individual item variant
const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } }
}

// Usage on a product grid
<motion.div variants={listVariants} initial="hidden" animate="show">
  {products.map(p => (
    <motion.div key={p.id} variants={itemVariants}>
      <ProductCard product={p} />
    </motion.div>
  ))}
</motion.div>
```

Keep total stagger duration under 300ms (6 items × 50ms = 300ms max). Beyond that, late cards
feel slow rather than elegant. Omit `AnimatePresence` for static product grids that always render —
it adds overhead and is only needed when items can conditionally unmount.

### Dark Mode Color Fix Pattern

ReviewGuide uses `[data-theme="dark"]` attribute, not Tailwind's `dark:` class strategy.
Use CSS variables for any color that must respect theme:

```tsx
// Before — breaks in dark mode (saturated green on near-black surface)
<h4 className="text-green-700">Pros</h4>

// After — uses existing success token from globals.css
<h4 style={{ color: 'var(--success)' }}>Pros</h4>

// Alternatively, define utility class in globals.css
.text-pros  { color: var(--success); }
.text-cons  { color: var(--error); }
```

Do not use Tailwind `dark:text-green-400` style variants — the theme system uses `data-theme`
attributes which Tailwind's dark mode doesn't know about unless `darkMode: ['attribute', '[data-theme="dark"]']`
is added to tailwind.config.ts. Adding that would require an audit of all existing `dark:` usages
to ensure no conflicts. Using CSS variables is the safer path.

---

## Sources

- Codebase inspection: `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/components/ProductReview.tsx`, `frontend/components/TopPickBlock.tsx`, `frontend/components/ProductCards.tsx`, `frontend/components/discover/ProductCarousel.tsx`, `frontend/components/discover/TrendingCards.tsx`, `frontend/components/browse/CategoryHero.tsx`, `frontend/app/page.tsx`, `frontend/package.json`
- Project context: `.planning/PROJECT.md`, `docs/superpowers/plans/2026-03-29-frontend-visual-overhaul.md`
- [Mosaic Layouts with CSS Grid — Axel Valdez, Medium](https://medium.com/@axel/mosaic-layouts-with-css-grid-d13f4e3ed2ae)
- [CSS 3D Perspective Animation Tutorial — Frontend.fyi](https://www.frontend.fyi/tutorials/css-3d-perspective-animations)
- [CSS Responsive Image Mosaic — 30 Seconds of Code](https://www.30secondsofcode.org/css/s/image-mosaic/)
- [Framer Motion stagger documentation — motion.dev](https://motion.dev/)
- [Framer Motion + Tailwind: The 2025 Animation Stack — DEV Community](https://dev.to/manukumar07/framer-motion-tailwind-the-2025-animation-stack-1801)
- [Creating Dynamic Product Cards in Next.js with Framer Motion — DEV Community](https://dev.to/nathlowe/my-code-chronicles-2-creating-a-dynamic-product-card-component-in-nextjs-using-framer-motion-3agh)
- [Premium product card design patterns — FoxEcom](https://foxecom.com/blogs/all/product-card-design)
- [10 Card UI Design Examples That Actually Work in 2025 — Bricx Labs](https://bricxlabs.com/blogs/card-ui-design-examples)
- [Typography Trends 2025 — Today Made](https://www.todaymade.com/blog/typography-trends)
- [25 Editorial Website Design Examples — Subframe](https://www.subframe.com/tips/editorial-website-design-examples)
- [Bold Type in Website Design — Designmodo](https://designmodo.com/bold-type-website-design/)
- [Shopify Horizon Theme Customization Guide 2026 — Neat Digital](https://neat.digital/blogs/blogs/shopify-horizon-theme-customisation-guide-2026)

---

*Feature research for: ReviewGuide.ai v3.0 Bold Editorial Visual Refresh*
*Researched: 2026-03-31*
