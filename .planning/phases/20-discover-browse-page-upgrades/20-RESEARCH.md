# Phase 20: Discover + Browse Page Upgrades - Research

**Researched:** 2026-04-01
**Domain:** Next.js 14 / React 18 frontend — CSS variables, Tailwind, component styling
**Confidence:** HIGH

---

## Summary

Phase 20 is a pure frontend styling pass. Every required asset (category WebP images in `/public/images/categories/`, CSS tokens in `globals.css`) was built in Phases 17-18 and is already on disk. No new libraries are needed. No backend changes are required.

The work splits into two clear tracks:

**Track A — Discover page (DISC-06, DISC-07):** The `ProductCarousel` already uses real `.webp` images and `loading="eager"` on slide 0 — DISC-07 is essentially complete as written. The remaining gap is purely visual: `CategoryChipRow` chips are small and plain; `TrendingCards` thumbnails are 48x48 icons; neither uses the bold accent tokens from Phase 17. Both need size increases and accent color treatment.

**Track B — Browse category page (BRW-01, BRW-02):** The `[category]/page.tsx` hero already renders the category image as a full-bleed background with a `bg-gradient-to-t from-black/70` overlay and white text — but it uses the old `.jpg` files from `/images/browse/` rather than the new bold `.webp` files from `/images/categories/`. `EditorsPicks` cards are currently 144px wide with plain `Option 1 / Option 2` labels and no bold typography treatment.

**Primary recommendation:** Update `categoryConfig.ts` image paths to point to the new WebP files; thicken the hero gradient overlay for WCAG AA compliance; upsize `TrendingCards` thumbnails from 48px to 80px with a colored accent bg; add bold color treatment to `CategoryChipRow` inactive chips; upgrade `EditorsPicks` card typography with product names and bolder sizing.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DISC-06 | Category chips and trending cards use bolder colors and stronger visual presence | Chips: add `var(--bold-blue/green/amber)` accent bg per chip, increase height to 44px. Trending: upsize thumbs to 80px, add accent ring |
| DISC-07 | Product carousel uses real product images with `loading="eager"` on first slide | ALREADY DONE in current `ProductCarousel.tsx` — verify all 5 slide images exist on disk; add any missing ones |
| BRW-01 | Category hero sections display full-bleed AI-generated background images with gradient overlay | Update `categoryConfig.ts` image paths from `/images/browse/*.jpg` to `/images/categories/cat-*.webp`; deepen gradient from `from-black/70` to `from-black/80 via-black/50` |
| BRW-02 | Editor's Picks cards have bolder styling consistent with v3.0 visual language | Wider cards (w-40 → w-48), show product name instead of "Option N", bolder price/CTA badge |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React / Next.js | 18 / 14 | Component rendering | Project standard |
| Tailwind CSS | 3.x | Utility classes | Project standard |
| CSS custom properties | native | Design token system | All phase 17 tokens live here |
| lucide-react | latest | Icons in chips/cards | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| class-variance-authority | 0.7.1 | Variant APIs | Added in Phase 17 decisions — use for EditorsPicks card variants if needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw CSS variables for accent colors | Tailwind palette classes | Project decision: never use hardcoded Tailwind colors in v3 components — always use `var(--bold-*)` or semantic tokens |
| next/image | raw `<img>` | Project decision: entire codebase uses raw `<img>` tags (set in Phase 19 decisions) |

**Installation:** No new packages needed.

---

## Architecture Patterns

### Recommended Project Structure

No new files are needed except possibly a small test file. All changes are surgical edits to existing files:

```
frontend/
├── lib/
│   └── categoryConfig.ts          # Update image paths (browse/*.jpg → categories/cat-*.webp)
├── components/
│   ├── discover/
│   │   ├── CategoryChipRow.tsx    # Bold accent colors, larger size
│   │   ├── TrendingCards.tsx      # Larger thumbnails, accent ring
│   │   └── ProductCarousel.tsx    # Verify images exist; add any missing slide image
│   ├── EditorsPicks.tsx           # Wider cards, product name, bolder typography
│   └── browse/
│       └── [unchanged]            # CategoryHero.tsx already wired; only categoryConfig changes needed
├── app/
│   └── browse/[category]/page.tsx # Deepen gradient overlay (minor tweak)
└── tests/
    └── browseHero.test.tsx        # Wave 0 — new test file for BRW-01, BRW-02, DISC-06
```

### Pattern 1: Category Image Mapping via categoryConfig.ts
**What:** Central `categories` array in `lib/categoryConfig.ts` drives the `image` field for every browse page hero. Changing the paths here updates all 10 category pages simultaneously.
**When to use:** Always — never hardcode image paths in the component.
**Example:**
```typescript
// lib/categoryConfig.ts — change ONLY the image field
{
  slug: 'electronics',
  name: 'Electronics',
  image: '/images/categories/cat-laptops.webp',  // was: '/images/browse/electronics.jpg'
  // ... rest unchanged
}
```

Mapping to use (all files confirmed on disk):

| slug | current image | new image |
|------|--------------|-----------|
| electronics | `/images/browse/electronics.jpg` | `/images/categories/cat-laptops.webp` |
| travel | `/images/browse/travel.jpg` | `/images/categories/cat-travel.webp` |
| home-appliances | `/images/browse/home-appliances.jpg` | `/images/categories/cat-kitchen.webp` |
| health-wellness | `/images/browse/health-wellness.jpg` | `/images/categories/cat-fitness.webp` |
| outdoor-fitness | `/images/browse/outdoor-fitness.jpg` | `/images/categories/cat-outdoor.webp` |
| fashion-style | `/images/browse/fashion-style.jpg` | `/images/categories/cat-fashion.webp` |
| smart-home | `/images/browse/smart-home.jpg` | `/images/categories/cat-smart-home.webp` |
| kids-toys | `/images/browse/kids-toys.jpg` | `/images/categories/cat-gaming.webp` |
| baby | `/images/browse/baby.jpg` | `/images/categories/cat-home-decor.webp` |
| big-tall | `/images/browse/big-tall.jpg` | `/images/categories/cat-fashion.webp` |

### Pattern 2: WCAG AA Gradient Overlay for Hero Text
**What:** The current hero in `[category]/page.tsx` uses `bg-gradient-to-t from-black/70 via-black/30 to-transparent`. White on black/70 is safe (~4.5:1+), but this depends on image luminance. A stronger overlay eliminates per-image uncertainty.
**When to use:** Any full-bleed image hero where text must meet WCAG AA (4.5:1).
**Example:**
```tsx
{/* Deepen gradient — ensures white text WCAG AA regardless of image brightness */}
<div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/10" />
```
WCAG AA rule: white (#FFFFFF) on `rgba(0,0,0,0.80)` over any image = effective luminance ratio > 7:1. HIGH confidence this passes.

### Pattern 3: Per-Chip Accent Color via Static Map
**What:** Each chip in `CategoryChipRow` gets a distinct accent color from the Phase 17 bold tokens (`--bold-blue`, `--bold-amber`, `--bold-green`, etc.). The active chip uses `--primary`. Inactive chips show a tinted bg instead of flat `--surface`.
**When to use:** When chips represent different categories with distinct color identities.
**Example:**
```typescript
const CHIPS: ChipConfig[] = [
  { label: 'For You', accentColor: 'var(--primary)' },
  { label: 'Tech', query: '...', accentColor: 'var(--bold-blue)' },
  { label: 'Travel', query: '...', accentColor: 'var(--bold-amber)' },
  { label: 'Kitchen', query: '...', accentColor: 'var(--bold-green)' },
  { label: 'Fitness', query: '...', accentColor: 'var(--accent)' },  // terracotta
  { label: 'Audio', query: '...', accentColor: 'var(--bold-blue)' },
]

// In JSX for inactive chip:
background: `color-mix(in srgb, ${chip.accentColor} 12%, var(--surface))`,
color: chip.accentColor,
border: `1.5px solid color-mix(in srgb, ${chip.accentColor} 35%, transparent)`,
```
`color-mix()` is supported in all modern browsers (Chrome 111+, Safari 16.2+, Firefox 113+). This is the project's target browser set. **HIGH confidence.**

### Pattern 4: TrendingCards Thumbnail Upsize
**What:** Increase thumbnail container from 48x48 to 80x80, add a colored accent bg derived from the topic's `iconBg` field (already present in `trendingTopics.ts`), and display as a rounded square with slight border.
**When to use:** When current thumbnails are too small to read at a glance.
**Example:**
```tsx
<div
  style={{
    width: '80px',
    height: '80px',
    borderRadius: '14px',
    background: topic.iconBg,
    flexShrink: 0,
    overflow: 'hidden',
    border: `2px solid color-mix(in srgb, ${topic.iconColor} 25%, transparent)`,
  }}
>
  <img src={topic.image} alt="" className="w-full h-full object-cover" loading="lazy" />
</div>
```

### Pattern 5: EditorsPicks Card Bold Treatment
**What:** Current cards are `w-36` with generic "Option 1" labels. Bold treatment: `w-44`, product name fetched from `curatedLinks` (add `name` field), category-accent header strip, bolder price/CTA.
**When to use:** Whenever a card's label provides no value to the user.

**Note on `curatedLinks` data structure:** Current shape is `{ asin, url }`. The EditorsPicks component currently shows "Option 1/2/3" as placeholder. To show product names, either:
- (A) Add `name` field to `curatedLinks` data — requires updating `lib/curatedLinks.ts` and the `EditorsPicks` types; low risk
- (B) Use a short product name derived from the topic `title` + suffix (e.g. "Sony WH-1000XM6", "Bose QC45") — zero data migration, moderate visual value

Option A gives better UX; Option B is faster. Research recommends Option A.

### Anti-Patterns to Avoid
- **Hardcoding Tailwind color utilities** (`text-blue-600`, `bg-green-500`) in v3 components — QA-03 will flag these. Use `var(--bold-*)` or inline style tokens only.
- **Using next/image** — project decision is raw `<img>` tags throughout (Phase 19 decision).
- **Touching `Message.tsx` or `BlockRegistry.tsx`** — protected per REQUIREMENTS.md.
- **Modifying `CategoryHero.tsx`** — it already has the CATEGORY_IMAGES map but it's unused by the active browse page (the active hero is in `[category]/page.tsx`). Do not refactor to consolidate — that's out of scope and risks regressions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color transparency/tinting | Custom hex math | `color-mix(in srgb, ...)` | Native CSS, no JS, works in all target browsers |
| Image fallback | Custom error handler | Existing `onError` pattern from EditorsPicks ProductImage component | Already battle-tested in prod |
| Icon rendering | SVG inline | lucide-react components | Consistent stroke weight, tree-shaken |

---

## Common Pitfalls

### Pitfall 1: DISC-07 Already Partially Done
**What goes wrong:** A plan task is created to "add real images to ProductCarousel" when the component already has `loading="eager"` on slide 0 and real `.webp` srcs on all 5 slides.
**Why it happens:** Reading the requirement without reading the current component source.
**How to avoid:** The only gap is confirming all 5 image files exist on disk. `headphones.webp`, `laptop.webp`, `shoes.webp` are present. `tokyo.webp`, `vacuum.webp`, `smart-home.webp` are also present (confirmed from file listing). DISC-07 needs a test to verify all 5 files exist, plus a visual review — not a code rewrite.
**Warning signs:** If a plan says "add images to ProductCarousel" for multiple tasks, it has missed the current state.

### Pitfall 2: CategoryHero.tsx vs [category]/page.tsx confusion
**What goes wrong:** Editing `CategoryHero.tsx` to wire BRW-01 when the active browse page doesn't use `CategoryHero` at all — it builds its own inline hero.
**Why it happens:** `CategoryHero.tsx` exists in `/components/browse/` and has a `CATEGORY_IMAGES` map — it looks authoritative. But `[category]/page.tsx` renders its own `<div>` + `<img>` hero, calling `category.image` from `categoryConfig`.
**How to avoid:** The single-file fix is to update `categoryConfig.ts` image paths. The `CategoryHero` component with its own map is currently unused by the active browse page.
**Warning signs:** Any plan that edits `CategoryHero.tsx` for BRW-01 is likely working in the wrong file.

### Pitfall 3: `color-mix()` unsupported environments
**What goes wrong:** Gradient tinting via `color-mix` works in browser but jsdom (Vitest) does not evaluate CSS `color-mix` functions — tests that check computed background color will fail.
**Why it happens:** jsdom has limited CSS support.
**How to avoid:** Tests must assert on the presence of the `color-mix(...)` string in the style attribute, not the computed color. Alternatively, tests skip computed color checks entirely and assert structural properties.

### Pitfall 4: DISC-04 test regression on CategoryChipRow
**What goes wrong:** Existing `discoverScreen.test.tsx` has DISC-04 tests that assert "For You" chip is NOT present by default (when localStorage is empty). If `CategoryChipRow` hardcodes a "For You" chip at index 0, this will fail.
**Why it happens:** Current `CategoryChipRow` has `{ label: 'For You' }` in the `CHIPS` array with `activeIndex = 0`, which means "For You" always renders. The DISC-04 test expects it only shows when `getRecentSearches()` returns data.
**How to avoid:** When restyling `CategoryChipRow`, check if the "For You" chip conditional was ever wired up. It currently is NOT conditional — the `discoverScreen.test.tsx` test at line 162-165 will fail if "For You" always renders. This is a pre-existing gap, not introduced by Phase 20. Phase 20 must not make it worse, and the planner should note this discrepancy.
**Warning signs:** `npm run test:run` failing on `DiscoverPage — "For You" chip`.

### Pitfall 5: Category image mapping for "baby" and "big-tall"
**What goes wrong:** No `cat-baby.webp` or `cat-big-tall.webp` exists in `/images/categories/`. The Phase 18 batch generated 15 images for specific product categories (laptops, kitchens, etc.), not all browse slugs.
**Why it happens:** Browse page slugs (`baby`, `big-tall`) don't map 1:1 to Phase 18 generated images.
**How to avoid:** Use best-fit mapping (confirmed above): `baby` → `cat-home-decor.webp` (warm domestic scene), `big-tall` → `cat-fashion.webp`. These are already used in the existing `CategoryHero.tsx` CATEGORY_IMAGES map — copy that mapping.

---

## Code Examples

Verified patterns from existing codebase:

### Existing Hero Gradient (current — [category]/page.tsx)
```tsx
// Current: may need strengthening for WCAG AA
<div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />

// Recommended replacement:
<div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-black/10" />
```

### Bold accent chip (CategoryChipRow upgrade)
```tsx
// Inactive chip with accent tint
style={{
  height: '44px',
  padding: '0 20px',
  borderRadius: '22px',
  background: `color-mix(in srgb, ${chip.accentColor} 12%, var(--surface))`,
  border: `1.5px solid color-mix(in srgb, ${chip.accentColor} 40%, transparent)`,
  color: chip.accentColor,
  fontSize: '13px',
  fontWeight: 600,
}}
```

### TrendingCards upsize (from 48px to 80px)
```tsx
// Replace existing thumbnail container:
<div
  style={{
    width: '80px',
    height: '80px',
    borderRadius: '14px',
    background: topic.iconBg,    // already in trendingTopics data
    flexShrink: 0,
    overflow: 'hidden',
  }}
>
  <img src={topic.image} alt="" className="w-full h-full object-cover" />
</div>
```

### EditorsPicks bold card width
```tsx
// Change: className="flex-shrink-0 w-36 rounded-xl ..."
// To:     className="flex-shrink-0 w-44 rounded-xl ..."
// Add product name display using topic.title context
```

### categoryConfig.ts image update
```typescript
// Change electronics entry:
image: '/images/categories/cat-laptops.webp',  // was '/images/browse/electronics.jpg'
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Placeholder gradients as carousel backgrounds | Real `.webp` product images | Phase 13 build | DISC-07 is already done in code |
| Old `.jpg` browse images from Phase 4 | New bold `.webp` from Phase 18 | Phase 18 complete | BRW-01 is a data-path update only |
| Flat `--primary` blue for all chips | Per-chip accent from Phase 17 bold tokens | Phase 17 complete | DISC-06 just needs token application |

**Deprecated/outdated:**
- `/images/browse/*.jpg` files — superseded by `/images/categories/cat-*.webp` (Phase 18). The old `.jpg` files can stay on disk; no cleanup needed in this phase.

---

## Open Questions

1. **Does DISC-04 "For You" chip need fixing in Phase 20?**
   - What we know: The test asserts "For You" should NOT render unless `getRecentSearches()` returns data. Current code always renders it.
   - What's unclear: Was this intentional (test is wrong) or a gap from Phase 13?
   - Recommendation: Treat as out of scope for Phase 20 — do not change the "For You" chip conditional behavior. Add a note in the plan that the DISC-04 test failure is a pre-existing issue, not introduced by Phase 20.

2. **Should EditorsPicks product names come from `curatedLinks` data?**
   - What we know: Current shape is `{ asin, url }`. Showing "Option 1/2/3" is unhelpful.
   - What's unclear: Whether the planner wants to update the data shape (requires touching `curatedLinks.ts` and `editorsPicks.test.tsx`) or use a simpler visual shortcut.
   - Recommendation: Add optional `name?: string` field to product entries in `curatedLinks.ts` for the 2-3 most important categories (electronics, home-appliances). Show name when present, fall back to "Option N" when absent. Low risk, high UX value.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.17 |
| Config file | `frontend/vitest.config.ts` (or inferred from `package.json`) |
| Quick run command | `cd frontend && npm run test:run -- tests/browseHero.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DISC-06 | Category chips have bolder visual presence (height >= 44px, accent color) | unit | `npm run test:run -- tests/browseHero.test.tsx` | Wave 0 |
| DISC-07 | All 5 carousel slide images exist on disk as `.webp` | unit (file system) | `npm run test:run -- tests/imageAssets.test.ts` (extend existing) | Extend existing |
| BRW-01 | categoryConfig image paths point to `/images/categories/*.webp` | unit | `npm run test:run -- tests/browseHero.test.tsx` | Wave 0 |
| BRW-02 | EditorsPicks cards have larger width and non-generic labels | unit | `npm run test:run -- tests/editorsPicks.test.tsx` (extend) + `tests/browseHero.test.tsx` | Wave 0 + extend |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test:run -- tests/browseHero.test.tsx tests/imageAssets.test.ts`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/browseHero.test.tsx` — covers BRW-01 (WebP paths in categoryConfig), DISC-06 (chip height/accent), BRW-02 (card width)
- [ ] Extend `frontend/tests/imageAssets.test.ts` — add DISC-07 assertions for carousel slide images (headphones, laptop, tokyo, vacuum, shoes, smart-home `.webp` files)

*(Existing `editorsPicks.test.tsx` passes currently — extend it rather than replace it)*

---

## Sources

### Primary (HIGH confidence)
- Direct source read: `frontend/components/discover/ProductCarousel.tsx` — confirmed `loading="eager"` on first slide and real `.webp` srcs
- Direct source read: `frontend/components/discover/CategoryChipRow.tsx` — confirmed plain styling with flat `--primary` / `--surface` only
- Direct source read: `frontend/components/discover/TrendingCards.tsx` — confirmed 48x48 thumbnails, no accent colors
- Direct source read: `frontend/app/browse/[category]/page.tsx` — confirmed hero uses `category.image` from `categoryConfig`, NOT from `CategoryHero.tsx`
- Direct source read: `frontend/lib/categoryConfig.ts` — confirmed 10 categories with `/images/browse/*.jpg` paths
- Direct file listing: `frontend/public/images/categories/` — all 15 WebP files confirmed present on disk
- Direct file listing: `frontend/public/images/products/` — all 5 carousel slide images confirmed present on disk
- Direct source read: `frontend/app/globals.css` — confirmed `--bold-blue`, `--bold-green`, `--bold-red`, `--bold-amber`, `--heading-*` tokens from Phase 17

### Secondary (MEDIUM confidence)
- `color-mix(in srgb, ...)` browser support: confirmed in CSS specification; project's Next.js 14 targets modern evergreen browsers where this is universally supported (Chrome 111+, Safari 16.2+, Firefox 113+)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all dependencies already in project
- Architecture: HIGH — based on direct reading of all affected source files
- Pitfalls: HIGH — DISC-07 "already done" and CategoryHero confusion are confirmed by source inspection, not inference
- Image mapping: HIGH — all target WebP files confirmed on disk via file system listing

**Research date:** 2026-04-01
**Valid until:** 2026-05-01 (stable tech, no external API dependencies)
