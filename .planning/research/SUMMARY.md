# Project Research Summary

**Project:** ReviewGuide.ai v3.0 — Bold Editorial Visual Overhaul
**Domain:** Brownfield Next.js 14 frontend visual refresh — editorial luxury product discovery UI
**Researched:** 2026-03-31
**Confidence:** HIGH

## Executive Summary

ReviewGuide.ai v3.0 is a brownfield visual overhaul of an existing production product, not a greenfield build. The existing stack (Next.js 14, React 18, Tailwind CSS 3, Framer Motion 12.26.2, editorial design token system) is fully capable of delivering the target "Shopify meets Wirecutter" aesthetic with a single new dependency (`class-variance-authority@0.7.1`). All raw materials — 22 AI-generated product images, 10 category hero images, a complete CSS variable token system, and two installed typefaces — are already in place. The scope is entirely frontend: new component creation, visual property upgrades on existing components, CSS token additions, and image wiring. No backend changes are required.

The recommended approach is to execute in a strict dependency order that protects the production system: establish the CSS token foundation first (adding bold tokens without disturbing the protected `designTokens.test.ts` contract), generate AI images in a single consistent batch before integrating them, build the new `MosaicHero` component in isolation, then upgrade discover/browse page components, and finally polish the chat-layer product cards. The highest-risk single boundary is `Message.tsx` / `BlockRegistry.tsx` — the chat SSE rendering pipeline is explicitly protected and must not be touched structurally during this milestone. Only the leaf components (`ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx`) are safe for visual-only changes.

The primary risks are non-functional quality regressions: LCP regression from switching hero images from SVG placeholders to real PNGs without setting `loading="eager"`; CLS from mosaic grid cells without explicit `aspect-ratio`; dark mode breakage from adding new CSS variables to `:root` without corresponding `[data-theme="dark"]` overrides; and visual inconsistency across phases from design token drift. All are low recovery cost if caught early but become expensive if they accumulate across multiple phases before detection. The mitigation strategy is to run `npm run test:run` after every `globals.css` edit and manually toggle dark mode after every new token addition.

---

## Key Findings

### Recommended Stack

The existing stack requires no new frameworks. One new library is justified: `class-variance-authority@0.7.1` adds a typed variant API for the premium `ProductCard` component where three or more visual modes (compact/standard/featured, default/loading/highlighted) would otherwise require brittle ad-hoc conditional logic. Beyond that, all layout, animation, and image optimization needs are covered by existing installations.

A critical API deprecation affects image generation: DALL-E 3 was retired March 4, 2026. All AI image generation must use `gpt-image-1` with `quality="medium"` — the Python `client.images.generate()` interface is unchanged, only the model name differs. The `openai` Python SDK is already installed in the backend. Images should be pre-generated and committed as static PNGs, never generated at runtime on page load.

**Core technologies:**
- **Next.js 14 `next/image`** — local static image optimization with LQIP blur placeholders; use only for `/public/` assets. Use plain `<img>` for external eBay/Amazon/Serper URLs (no `remotePatterns` configured and enumerating all CDNs is not feasible).
- **Tailwind CSS 3 JIT** — CSS Grid `grid-template-areas` with arbitrary values for mosaic layout; `group-hover:scale-[1.04]`; `aspect-[4/3]` tile sizing. No new grid library needed.
- **Framer Motion 12.26.2** — `whileInView` + `viewport={{ once: true }}` for scroll entrances; `staggerChildren: 0.07` for grid reveals; spring physics (`stiffness: 400, damping: 28`) for premium card hover lift.
- **`class-variance-authority@0.7.1`** — typed variant API for ProductCard multi-mode component; composable with existing `tailwind-merge`.
- **`gpt-image-1` via Python `openai`** — pre-generated editorial imagery at $0.015/image; generate once and commit as static PNGs to `/public/images/products/`.

### Expected Features

**Must have (table stakes — ships this milestone):**
- Shopify-style mosaic collage hero on homepage — first-impression differentiator; pure CSS with absolute positioning and `transform: rotate()`; all 22 images already on disk
- Bold typography scale — push browse `CategoryHero` h1 to `clamp(2.5rem, 5vw, 4.5rem)`; homepage h1 stays restrained because the mosaic provides visual energy
- Category hero background images — 10 images exist on disk; applying them with `linear-gradient` overlay transforms browse pages into a magazine-cover feel
- Dark mode hardcoded-color fixes — `text-green-700`, `text-red-700`, `text-emerald-600` in `ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx` are live regressions today; must convert to `var(--success)` / `var(--error)` tokens before any refresh can claim to be complete
- `ProductReview` premium card polish — better image sizing, tighter "Where to Buy" section (max 3, clean merchant names)
- Staggered card entrance animations — `staggerChildren: 0.05` + `y: 12 → 0` on product grids; total duration under 300ms; never inside streaming message containers

**Should have (v1.x polish pass after validation):**
- Section eyebrow label consistency audit — enforce `UPPERCASE 11px tracking-widest` pattern across all section headers
- Per-category accent color flowing to section dividers and borders
- Rank number as large decorative element in ProductCards (`text-4xl` serif aside, not inline with title)
- "Where to Buy" max-3 enforcement at render level

**Defer (v2+):**
- Mosaic collage personalized to user query context — requires session state; defer until user accounts exist
- Video hero backgrounds — Core Web Vitals impact requires measurement infrastructure first
- Full per-category page theme via `[data-accent]` routing — token system is ready; v2 when vertical coverage expands

**Anti-features to avoid:**
- Full page transition animations — `AnimatePresence` in App Router causes hydration mismatches on SSR pages; use per-component entrance animations instead
- Auto-playing video backgrounds — destroys Core Web Vitals, blocked on mobile browsers
- Glassmorphism on product cards — `backdrop-filter: blur()` causes severe mobile performance degradation; reserve to topbar only
- Any structural modifications to `Message.tsx` or `ChatContainer.tsx` — streaming pipeline is protected per MEMORY.md

### Architecture Approach

The visual overhaul is a pure frontend overlay on a stable existing system. The architecture is a single-token system (`globals.css` CSS variables → `tailwind.config.ts` mappings → component Tailwind classes) with a dual-theme strategy (`data-theme="dark"` attribute on `<html>`, not Tailwind `.dark` class). All components receive theme through CSS variables; `dark:` Tailwind utilities are silently inert with this strategy and must not be used on new components. The critical architectural constraint is a two-level component boundary: (1) `BlockRegistry.tsx` dispatches to leaf chat components — modify only the leaf components visually, never the registry; (2) there are two different `ProductCarousel` components that must not be confused — `components/discover/ProductCarousel.tsx` (discover page slideshow) and `components/ProductCarousel.tsx` (chat response carousel used by BlockRegistry).

**Major components for v3.0:**
1. **`MosaicHero.tsx` (new)** — Shopify-style collage hero at `components/discover/MosaicHero.tsx`; CSS absolute positioning + rotation transforms; reads from hardcoded image paths in `/public/images/products/`
2. **`globals.css` token additions** — new bold editorial tokens added to `:root` AND `[data-theme="dark"]` simultaneously; never remove legacy `--gpt-*` vars; `designTokens.test.ts` is the validation gate
3. **Leaf chat product components** — `ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx` receive visual-only upgrades (padding, spacing, image size, color token conversions); interface/props contracts are frozen

### Critical Pitfalls

1. **Breaking the protected design token contract** — `designTokens.test.ts` enforces specific CSS variable names (`--stream-status-*`, `--citation-color`, `--gpt-*` legacy vars) and utility class names. Renaming during "cleanup" breaks CI and the live streaming UI. Prevention: run `npm run test:run` after every `globals.css` edit; only ADD tokens, never rename existing names.

2. **AI-generated images visually inconsistent across the site** — Images from different generation sessions have mismatched lighting, color temperature, and stylization. In a side-by-side mosaic hero this reads as "amateur AI collage" not "editorial system." Prevention: define a canonical style prompt prefix before generating any image; generate the entire hero/carousel/category batch in one session; do a side-by-side visual audit before integration.

3. **Carousel hero LCP regression** — Switching from SVG icon placeholders to real images without setting `loading="eager"` + `fetchPriority="high"` on the first slide causes a 300–800ms LCP regression on mobile. The existing `ProductCarousel` uses `loading="lazy"` on all slides (verified in source). Prevention: set eager loading on slide index 0 in the same PR that introduces real images.

4. **New CSS tokens without dark mode counterparts** — Any `--mosaic-gradient-*` or `--card-highlight` token added only to `:root` appears as a light-mode gradient on dark backgrounds. `dark:` Tailwind utilities are silently inert with the `data-theme` strategy. Prevention: add every new token to both `:root` and `[data-theme="dark"]` in the same commit; manually toggle dark mode after each addition.

5. **Framer Motion `layout` prop on product cards during streaming** — Adding `layout` prop or `AnimatePresence` to cards inside the streaming message container triggers layout calculations on every SSE chunk, dropping to ~15fps on mid-range mobile. Prevention: use CSS `transition` for hover effects inside streaming containers; use Framer Motion only for top-level entrance animations on pre-rendered static lists.

---

## Implications for Roadmap

The combined research reveals a clear dependency graph that dictates phase ordering. The CSS token foundation must come first because all components inherit from it. Image generation must complete before any component that references those images can be finalized. The `MosaicHero` component is the flagship deliverable but has no unusual dependencies once tokens and images are ready. Chat-layer card polish is independent of discover-page work and can proceed in parallel but must be gated by the dark mode fix requirement from Phase 1.

### Phase 1: Token Foundation + Dark Mode Fixes

**Rationale:** Every component in every subsequent phase depends on the CSS token system being correct. The dark mode hardcoded-color bugs are live production regressions that must not survive into a visual refresh release. Establishing the type scale tokens here prevents typography inconsistency across later phases (Pitfall 8). This phase defines the rules all subsequent phases follow.
**Delivers:** Updated `globals.css` with new bold editorial tokens (all with dark mode counterparts); conversion of hardcoded `text-green-700`/`text-red-700`/`text-emerald-600` to semantic tokens in `ProductReview.tsx`, `TopPickBlock.tsx`, `ProductCards.tsx`; bold type scale tokens (`--heading-xl` through `--heading-sm`); `designTokens.test.ts` passing after all changes
**Addresses:** Dark mode hardcoded-color fixes (P1 table stakes); typography scale codification
**Avoids:** Pitfalls 1 (token contract), 4 (new tokens without dark counterparts), 8 (typography scale conflict), 10 (design drift)

### Phase 2: AI Image Generation Batch

**Rationale:** Images must be generated as a unified visual batch before any component integration to prevent the visual inconsistency pitfall. This is a one-time creative production task with a hard prerequisite: the canonical style prompt prefix must be written and reviewed against a 3–4 image test batch before generating the full set. Technically independent of Phase 1 but should not start until the target aesthetic established by Phase 1 tokens is clear.
**Delivers:** Complete batch of hero/carousel/category images generated with a single canonical style prefix; visual audit confirming consistent lighting and color temperature; images saved at consistent resolution to `/public/images/products/`; all existing topic images assessed for compatibility with the new visual system
**Addresses:** Mosaic collage hero raw material; category hero backgrounds; carousel upgrade imagery
**Avoids:** Pitfall 2 (AI image inconsistency)

### Phase 3: MosaicHero Component + Discover Page Wiring

**Rationale:** The mosaic hero is the single highest-impact first-impression change and the flagship deliverable of the v3.0 milestone. It is blocked on Phase 1 (tokens) and Phase 2 (images). Creating it as an isolated new component (`MosaicHero.tsx`) rather than modifying the existing discover `ProductCarousel.tsx` is the low-risk path — both can coexist in `page.tsx` during development. CLS and LCP acceptance criteria must be in the phase definition, not deferred to QA.
**Delivers:** `components/discover/MosaicHero.tsx` with CSS absolute-position + rotation mosaic; wired into `app/page.tsx`; `loading="eager"` + `fetchPriority="high"` on the first visible mosaic image; explicit `aspect-ratio` on all image containers; Lighthouse CLS < 0.1 and LCP < 2.5s verified on mobile
**Uses:** Phase 1 tokens; Phase 2 images; CSS Grid arbitrary values; no new dependencies
**Avoids:** Pitfalls 3 (LCP regression), 5 (CLS from mosaic), 7 (next/image external URL errors)

### Phase 4: Discover + Browse Page Visual Upgrades

**Rationale:** With the hero mosaic shipped, the surrounding discover page components (carousel, trending cards, search bar, category chips) and browse category heroes need visual parity. CategoryHero background image injection with gradient overlay is one of the highest-value/lowest-cost changes in the entire milestone. This phase can run in parallel with Phase 5 since it touches separate component files.
**Delivers:** Upgraded `ProductCarousel.tsx` (discover) with bold slide visuals and `loading="eager"` on first slide; `TrendingCards.tsx` with larger image tiles; `CategoryHero.tsx` with background image injection + gradient overlay; bold h1 typography at `clamp(2.5rem, 5vw, 4.5rem)` on browse heroes; per-category accent injection to section dividers; WCAG AA contrast verified on category hero overlays
**Uses:** Phase 2 images; Phase 1 typography tokens; existing `CategoryHero` gradient prop system
**Avoids:** Pitfall 9 (carousel dark mode gradient mismatch — use CSS variable gradients, not hardcoded hex values in slide objects)

### Phase 5: Chat-Layer Product Card Polish

**Rationale:** Chat product cards (`ProductReview`, `TopPickBlock`, `ProductCards`, `InlineProductCard`, `ResultsProductCard`) share the same dark mode token fixes already completed in Phase 1 as their primary blocker. This phase is the visual polish layer: better image sizing, cleaner "Where to Buy" section, bolder card elevation, stagger entrance animations on static product grids. The Framer Motion constraint (no `layout` prop, no `AnimatePresence` inside streaming containers) is the key risk to manage.
**Delivers:** Premium product card visual treatment across all 5 chat/results card variants; staggered entrance animations using `staggerChildren: 0.05` on pre-rendered lists only; "Where to Buy" max-3 enforcement with clean merchant labels; `ResultsMainPanel` grid layout upgrade; 55+ fps verified during active streaming in Chrome DevTools Performance panel
**Uses:** Phase 1 tokens; Framer Motion `whileInView` + `staggerChildren` (NOT `layout` prop, NOT `AnimatePresence` inside message containers)
**Avoids:** Pitfall 6 (Framer Motion frame drops during streaming)

### Phase 6: Visual QA + Consistency Pass

**Rationale:** A 5-phase brownfield visual overhaul will accumulate invisible inconsistencies that only appear when viewing all pages in sequence. This phase is the hard gate before any release claim. The existing `designTokens.test.ts` must be extended to cover new tokens added in Phase 1. The Chrome MCP visual QA task from the existing plan is the correct mechanism for this phase.
**Delivers:** Extended `designTokens.test.ts` covering new bold editorial tokens; full site screenshot walk-through (homepage → browse → chat → results) with documented sign-off; `prefers-reduced-motion` compliance verified; section eyebrow label consistency audit completed; all 10 checklist items from PITFALLS.md "Looks Done But Isn't" checklist confirmed green
**Addresses:** P2 features (eyebrow labels, accent color consistency, rank number treatment)
**Avoids:** Pitfall 10 (design drift across phases)

### Phase Ordering Rationale

- **Tokens before components** — every component change in Phases 3–5 inherits CSS tokens; an incorrect token foundation silently breaks dark mode site-wide
- **Images before integration** — the visual consistency pitfall is unrecoverable after components ship; it must be solved at the generation stage before a single component references the images
- **New component before modification** — creating `MosaicHero.tsx` as a new file rather than modifying the existing `ProductCarousel.tsx` means the discover page can ship the mosaic while the carousel remains functional as a fallback during development
- **Discover and chat in parallel phases** — Phases 4 and 5 touch entirely separate component trees with no shared files; they can be implemented concurrently if resources allow
- **Visual QA as a hard gate** — without a final full-site pass, design token value adjustments mid-project will ship undetected as visual drift

### Research Flags

Phases with well-documented patterns (standard implementation, skip additional research):
- **Phase 1 (Token Foundation):** CSS variable extension pattern is fully codified in ARCHITECTURE.md and verified against the live codebase. Pattern: only ADD to `:root` and `[data-theme="dark"]` simultaneously.
- **Phase 3 (MosaicHero):** CSS absolute positioning + rotation mosaic is a pure CSS pattern with complete code examples in FEATURES.md; no library research needed.
- **Phase 5 (Card Polish):** Framer Motion stagger pattern is code-complete in FEATURES.md with exact variant objects; constraints are clearly defined.

Phases that benefit from a brief targeted research pass during planning:
- **Phase 2 (Image Generation):** The canonical style prompt prefix should be validated against a 3–4 image test batch before committing to the full set. `gpt-image-1` quality and pricing parameters are MEDIUM confidence (official docs returned 403 during research; inferred from community sources). Validate with an actual API call before budgeting.
- **Phase 4 (Browse Upgrades):** WCAG AA contrast verification of text on category hero background images with gradient overlay requires a measurement pass during implementation. The correct overlay opacity depends on each image's luminance profile and cannot be pre-calculated.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Direct codebase inspection; all library versions verified against `package.json`; DALL-E 3 retirement confirmed via multiple community sources; `gpt-image-1` pricing is MEDIUM (403 on official docs page) |
| Features | HIGH | Full codebase audit of all components; feature complexity assessments based on actual file inspection, not estimates; competitor analysis against Wirecutter and Shopify confirms patterns |
| Architecture | HIGH | Every integration point verified by reading source files; naming collision between two `ProductCarousel` components confirmed by directory inspection; protected file list cross-referenced against CLAUDE.md and MEMORY.md |
| Pitfalls | HIGH | Code-verified: `loading="lazy"` on carousel confirmed in source; `designTokens.test.ts` existence confirmed; `next.config.js` missing `remotePatterns` confirmed; `dark:` utility inertness confirmed against `tailwind.config.ts` |

**Overall confidence:** HIGH

### Gaps to Address

- **`gpt-image-1` exact pricing and quality parameters:** Official docs returned 403 during research; pricing ($0.015/image) and quality param values (`low`/`medium`/`high`) inferred from community discussion. Validate against an actual API call before budgeting image generation costs for the full batch.
- **WCAG AA contrast ratios for category hero overlays:** The research identifies that gradient overlays are needed for text legibility on hero background images but does not pre-calculate specific opacity values. Run WCAG AA contrast checks against actual generated images during Phase 4 implementation — the correct opacity depends on each image's luminance.
- **LazyMotion bundle optimization:** PITFALLS.md flags the full Framer Motion bundle (~34KB) as a potential TTI concern once the bundle grows. `LazyMotion` wrapping for non-critical pages is recommended but not in the current milestone scope. Flag for post-launch performance review if Lighthouse TTI degrades.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/app/page.tsx`, `frontend/components/discover/ProductCarousel.tsx`, `frontend/components/ProductCards.tsx`, `frontend/components/Message.tsx`, `frontend/next.config.js`, `frontend/tests/designTokens.test.ts`
- framer-motion v12 `whileInView` + `staggerChildren` — [motion.dev/docs/react-use-in-view](https://motion.dev/docs/react-use-in-view)
- `class-variance-authority@0.7.1` — [npmjs.com/package/class-variance-authority](https://www.npmjs.com/package/class-variance-authority)
- Next.js `remotePatterns` — [nextjs.org/docs/messages/next-image-unconfigured-host](https://nextjs.org/docs/messages/next-image-unconfigured-host)
- CSS Grid `grid-template-areas` with Tailwind arbitrary values — [tailwindcss.com/docs/grid-template-areas](https://tailwindcss.com/docs/grid-template-areas)
- Framer Motion bundle size and LazyMotion — [motion.dev/docs/react-reduce-bundle-size](https://motion.dev/docs/react-reduce-bundle-size)
- DALL-E 3 retirement (March 4, 2026) — OpenAI Developer Community + OpenAI Cookbook `gpt-image-1` example

### Secondary (MEDIUM confidence)
- `gpt-image-1` pricing ($0.015/image) and quality params — WebSearch multiple community sources, 2026
- LCP lazy-loading regression — [pagepro.co](https://pagepro.co/blog/nextjs-image-component-performance-cwv/), [debugbear.com](https://www.debugbear.com/blog/nextjs-image-optimization)
- AI image batch consistency — [nextbuild.co](https://nextbuild.co/blog/ai-product-photos-inconsistent-ecommerce)
- sharp `blurDataURL` generation — [buildwithmatija.com](https://www.buildwithmatija.com/blog/payload-cms-base64-blur-placeholders-sharp)
- Framer Motion animation performance tier list — [motion.dev/magazine/web-animation-performance-tier-list](https://motion.dev/magazine/web-animation-performance-tier-list)

### Tertiary (contextual reference)
- Project planning context: `.planning/PROJECT.md`, `docs/superpowers/plans/2026-03-29-frontend-visual-overhaul.md`
- Project memory: `CLAUDE.md`, `MEMORY.md` (editorial theme decisions, protected patterns, deployment lessons)

---

*Research completed: 2026-03-31*
*Ready for roadmap: yes*
