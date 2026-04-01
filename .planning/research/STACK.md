# Stack Research

**Domain:** v3.0 Visual Overhaul — Shopify-style mosaic hero, AI-generated product images, premium animated cards (brownfield Next.js 14 + Tailwind + Framer Motion)
**Researched:** 2026-03-31
**Confidence:** HIGH

---

## Context: What Already Exists (Do Not Re-Research)

Prior research (2026-03-16) validated the full stack. No changes to:

- Next.js 14 App Router (`^14.2.35`)
- React 18 + TypeScript
- Tailwind CSS 3 (`^3.3.6`) with editorial design tokens
- framer-motion `^12.26.2` — already in use across ProductCarousel, UnifiedTopbar
- lucide-react `^0.294.0` — stay pinned (icon renames between 0.294 and 0.577)
- clsx `^2.1.1` + tailwind-merge `^3.4.0` — already installed
- sharp `^0.33.5` — already installed (used by Next.js image optimizer)
- `@tailwindcss/typography` — already installed
- `tailwindcss-safe-area` — added in v2.0 milestone

This document covers only **new stack additions** for v3.0.

---

## Recommended Stack

### Core Technologies — No New Frameworks

The existing stack handles all layout and animation needs. No additional frameworks.

| Technology | Current Version | Role in v3.0 |
|------------|-----------------|--------------|
| Next.js `next/image` | built-in 14.2.35 | Hero mosaic images with `priority`, `blurDataURL` LQIP, `remotePatterns` for external product images. `sharp` (already installed) is Next.js's native image optimization backend. |
| Tailwind CSS 3 | ^3.3.6 | CSS Grid `grid-template-areas` for mosaic layout, `group-hover:scale-[1.04]` image zoom, `aspect-[4/3]` tiles, `overflow-hidden rounded-2xl` card shells |
| framer-motion | ^12.26.2 | `whileInView` + `viewport={{ once: true }}` for card entrance on scroll, `staggerChildren` for mosaic tile reveal, `AnimatePresence` for product card hover expansion, `layoutId` for smooth hero transitions |

### New Additions Required

| Library | Version to Install | Purpose | Why This Over Alternatives |
|---------|-------------------|---------|---------------------------|
| `class-variance-authority` | `^0.7.1` | Typed variant API for the premium ProductCard component — size (`compact`/`standard`/`featured`), state (`default`/`loading`/`highlighted`) | The project already has `clsx` + `tailwind-merge` for ad-hoc class merging. CVA adds the structured variant layer needed when one component has 3+ visual modes. 0.7.1 is the stable release (10k+ npm dependents). No new CSS-in-JS runtime — compiles to plain Tailwind strings. |

That is the only new frontend `npm install` this milestone requires.

---

### Supporting Libraries — All Already Present

| Library | Installed Version | How It Serves v3.0 |
|---------|------------------|---------------------|
| `framer-motion` | 12.26.2 | `whileInView` for scroll-triggered card entrances (use `viewport={{ once: true, margin: "-50px" }}` to avoid re-triggering). `staggerChildren: 0.07` on mosaic grid parent for tile-by-tile reveal. `whileHover={{ y: -2 }}` + `transition={{ type: "spring", stiffness: 400, damping: 25 }}` for premium card lift feel. |
| `sharp` | ^0.33.5 | Already installed as Next.js image backend. Also usable as a build-time script to generate `blurDataURL` base64 strings for local static images (resize to 8px wide → base64). Run once, commit the strings. |
| `tailwind-merge` | ^3.4.0 | Merge dynamic Tailwind classes safely in CVA compound variants — the two are designed to work together. |
| `clsx` | ^2.1.1 | Conditional class logic in card render paths. |
| `next/image` | built-in | Use `placeholder="blur"` + `blurDataURL` for hero mosaic tiles. For static local files (`/images/products/*.png`), Next.js auto-generates blurDataURL. For remote images, generate manually with sharp at build time or use a 10px inline base64 fallback. |

---

## Image Generation: Backend Script (Not Frontend Dependency)

AI-generated product images are a **backend generation task** (run once, commit PNGs), not a runtime frontend dependency.

| Component | Approach | Notes |
|-----------|----------|-------|
| Image generation model | `gpt-image-1` via `openai` Python SDK | DALL-E 3 was retired March 4, 2026. The replacement is `gpt-image-1` (same `client.images.generate()` call, `model="gpt-image-1"`). $0.015 per 1024×1024 image vs $0.040 for DALL-E 3. Parameters: `quality="medium"`, `size="1024x1024"`, `output_format="png"`. |
| Storage | `/frontend/public/images/topics/` | Already exists. 20 editorial images already committed here (verified via `ls`). Add new ones to same directory — no CDN or external storage needed for static editorial images. |
| Backend dependency | `openai>=1.0.0` | Already in backend requirements for GPT-4o. No new Python package needed. |
| Image spec for hero | 1024×1024 PNG, bold color, editorial product photography style, white/gradient background | Matches the existing topic images pattern (robot-vacuums.png, espresso-machines.png, etc.) |

Do NOT add a client-side image generation library. Images are pre-generated assets, not runtime API calls.

---

## Mosaic Layout: Pure CSS Grid (No New Library)

The Shopify-style mosaic hero is achievable with CSS Grid and Tailwind arbitrary values — no new grid library needed.

**Pattern (tailwind classes):**

```
/* 2-column grid where tile 1 spans 2 rows */
grid grid-cols-2 grid-rows-2

/* Tile 1: tall left panel */
row-span-2 aspect-[4/5] overflow-hidden rounded-2xl

/* Tiles 2+3: right column */
aspect-[4/3] overflow-hidden rounded-2xl
```

For layouts requiring named areas (3-panel asymmetric), use Tailwind's arbitrary CSS:

```html
<div class="grid [grid-template-areas:'a_b''a_c'] grid-cols-[3fr_2fr] gap-3">
  <div class="[grid-area:a]">...</div>
  <div class="[grid-area:b]">...</div>
  <div class="[grid-area:c]">...</div>
</div>
```

This pattern requires no new dependency — Tailwind 3's JIT mode handles arbitrary values.

---

## Animation Patterns: Framer Motion (No New Library)

All required animations are in the existing framer-motion 12.26.2 install.

**Mosaic tile stagger reveal:**
```typescript
// Parent
<motion.div
  initial="hidden"
  animate="visible"
  variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
>
// Each tile
<motion.div
  variants={{
    hidden: { opacity: 0, scale: 0.96 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } }
  }}
>
```

**Card scroll reveal:**
```typescript
<motion.div
  initial={{ opacity: 0, y: 16 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-50px" }}
  transition={{ duration: 0.35, ease: "easeOut" }}
>
```

**Premium card hover lift (spring physics):**
```typescript
<motion.div
  whileHover={{ y: -3, boxShadow: "var(--shadow-lg)" }}
  transition={{ type: "spring", stiffness: 400, damping: 28 }}
>
```

Do NOT add `react-spring`, `@formkit/auto-animate`, or any other animation library. framer-motion 12 covers all these patterns.

---

## Image Quality Priority: next/image Configuration

The PROJECT.md specifies image priority order: Serper/Google > Amazon > eBay. Implement in `next.config.js` via `remotePatterns`:

```javascript
images: {
  remotePatterns: [
    { protocol: 'https', hostname: '**.serpapi.com' },
    { protocol: 'https', hostname: '**.serper.dev' },
    { protocol: 'https', hostname: 'images-na.ssl-images-amazon.com' },
    { protocol: 'https', hostname: 'm.media-amazon.com' },
    { protocol: 'https', hostname: 'i.ebayimg.com' },
  ]
}
```

Use `next/image` with `onError` fallback to static editorial images in `/public/images/products/`. The `ImageWithFallback` component at `components/ui/ImageWithFallback.tsx` already handles error state — extend it to use `next/image` instead of `<img>` for optimization.

---

## Installation

```bash
# Only new frontend dependency
cd frontend && npm install class-variance-authority@^0.7.1
```

No backend package changes needed. `openai` is already installed for GPT-4o. Use `gpt-image-1` model name in the image generation script.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `class-variance-authority` (CVA) | `tailwind-variants` | Both solve the same problem. CVA is more established (0.7.1, 10k+ dependents, 1 year since last release means stable API). `tailwind-variants` is newer with more features but the API surface CVA provides is sufficient. Either works — CVA was chosen for simplicity. |
| CSS Grid arbitrary values | `react-masonry-css` or `masonry-layout` | Masonry (variable height) is different from a mosaic (fixed-height tiles in a defined pattern). The hero mosaic uses defined slot shapes, not auto-height columns. CSS Grid with defined template areas is the right tool — no JS layout library needed. |
| Pre-generated static images | Runtime DALL-E/gpt-image-1 API calls on page load | Runtime generation costs money on every page view and adds ~2-4s latency. These are editorial category images, not personalized content — generate once, commit, serve as static files. |
| `next/image` with `remotePatterns` | Raw `<img>` tags | `next/image` gives WebP conversion, size optimization, lazy loading, and LQIP blur placeholder automatically. The performance benefit is significant for a product mosaic with 5-8 images. `sharp` is already installed so optimization is free. |
| framer-motion `whileInView` | `react-intersection-observer` + custom logic | `react-intersection-observer` adds 3.5kb for functionality already in framer-motion's `useInView` hook (0.6kb). Since framer-motion is already in the bundle, `whileInView` is zero cost. |
| framer-motion spring physics for card hover | CSS `transition: transform 200ms ease` | Both work, but spring physics (`stiffness: 400, damping: 28`) produces the "premium" feel that CSS ease curves cannot replicate. framer-motion is already in bundle — use it where the feel matters. Use plain CSS transitions for non-premium secondary elements. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `react-spring` | Duplicate animation library — framer-motion 12.26.2 already covers all spring animation needs. Adds ~27kb for zero capability gain. | framer-motion (existing) |
| `swiper` / `embla-carousel` | The existing ProductCarousel already handles auto-rotate, touch swipe, and arrows without a carousel library. The mosaic hero is a static grid, not a carousel. | Pure CSS scroll snap + existing carousel logic |
| `@mui/x-data-grid` or similar for product comparison | MUI is already in the bundle for admin-only routes. Do not expand its usage into the main product UI — it conflicts with the editorial design system. | Existing `ComparisonTable.tsx` with styled Tailwind tables |
| `next/font` with new typefaces | DM Sans + Instrument Serif are already loaded in `layout.tsx` via `next/font/google`. Adding new fonts increases FOUT and bundle size. | Existing font variables (`var(--font-dm-sans)`, `var(--font-instrument)`) |
| DALL-E 3 (`dall-e-3` model) | Retired March 4, 2026. API calls will fail. | `gpt-image-1` model with same `client.images.generate()` interface |
| Inline `style` for hover shadows | Cannot be animated by Tailwind's transition system. Bypasses the design token system (`--shadow-*` vars). | framer-motion `whileHover={{ boxShadow: "..." }}` or Tailwind `hover:shadow-elevated` with CSS var tokens |
| `images.domains` in `next.config.js` | Deprecated in Next.js 14, less secure (no protocol/path scoping). | `images.remotePatterns` with explicit hostname matching |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `class-variance-authority@0.7.1` | React 18, TypeScript 5.x, tailwind-merge 3.x | Composable with `tailwind-merge` — pass CVA output through `twMerge()` to handle override conflicts. Standard pattern: `const cls = cva(...); return <div className={twMerge(cls({ variant }))} />` |
| `framer-motion@12.26.2` | Next.js 14 App Router, React 18 | `whileInView` + `viewport` prop stable since framer-motion v6. `staggerChildren` in `variants.transition` stable since v4. No version-specific concerns for v3.0 patterns. |
| `next/image` with `blurDataURL` | Next.js 14, sharp 0.33.5 | Static local imports auto-generate blurDataURL. Remote images need explicit `blurDataURL` string — generate at build time with the existing `sharp` package. |
| `gpt-image-1` model | `openai>=1.0.0` (Python) | Same `client.images.generate()` interface as DALL-E 3. Model name changed from `"dall-e-3"` to `"gpt-image-1"`. `quality` param changed from `"standard"/"hd"` to `"low"/"medium"/"high"`. |

---

## Sources

- framer-motion v12 `whileInView` + `staggerChildren` — [motion.dev/docs/react-use-in-view](https://motion.dev/docs/react-use-in-view) — HIGH confidence
- framer-motion layout animations — [motion.dev/docs/react-layout-animations](https://motion.dev/docs/react-layout-animations) — HIGH confidence
- DALL-E 3 retirement (March 4, 2026), `gpt-image-1` as replacement — [OpenAI Developer Community thread](https://community.openai.com/t/openai-is-making-a-huge-mistake-by-deprecating-dall-e-3/1367228) + [OpenAI Cookbook gpt-image example](https://cookbook.openai.com/examples/generate_images_with_gpt_image) — HIGH confidence (multiple sources agree)
- `gpt-image-1` pricing ($0.015/image), quality params (`low`/`medium`/`high`), size options — [WebSearch multiple sources, 2026] — MEDIUM confidence (official docs page returned 403, inferred from community discussion + third-party docs)
- `class-variance-authority@0.7.1` npm — [npmjs.com/package/class-variance-authority](https://www.npmjs.com/package/class-variance-authority) — HIGH confidence
- Next.js `remotePatterns` vs deprecated `domains` — [nextjs.org/docs/messages/next-image-unconfigured-host](https://nextjs.org/docs/messages/next-image-unconfigured-host) — HIGH confidence
- CSS Grid `grid-template-areas` with Tailwind arbitrary values — [Tailwind CSS docs](https://tailwindcss.com/docs/grid-template-areas) — HIGH confidence
- sharp `blurDataURL` generation pattern — [buildwithmatija.com](https://www.buildwithmatija.com/blog/payload-cms-base64-blur-placeholders-sharp) — MEDIUM confidence (third-party, but consistent with Next.js docs pattern)
- `framer-motion` react-intersection-observer comparison — [motion.dev/docs/inview](https://motion.dev/docs/inview) — HIGH confidence

---

*Stack research for: ReviewGuide.ai v3.0 Visual Overhaul — Bold Editorial*
*Researched: 2026-03-31*
