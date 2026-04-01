# Pitfalls Research

**Domain:** Major visual refresh added to existing production Next.js 14 app — bold colors, AI-generated imagery, Shopify-style mosaic hero, premium product cards, CSS variable evolution
**Researched:** 2026-03-31
**Confidence:** HIGH (code-verified against live codebase + web research confirmed)

---

## Critical Pitfalls

### Pitfall 1: Breaking the Protected Design Token Contract

**What goes wrong:**
The existing `designTokens.test.ts` file enforces that specific CSS variable names (`--stream-status-size`, `--stream-status-color`, `--stream-content-color`, `--citation-color`), utility classes (`.stream-status-text`, `.stream-content-text`, `.citation-text`), and Tailwind config keys (`card-enter`, `stream`, `stream-out`, `stream-inout`) remain intact. Any rename, removal, or restructuring of `globals.css` or `tailwind.config.ts` that touches these names will fail CI and potentially break the live streaming UI.

The visual overhaul ALSO requires updating tokens (bolder shadows, stronger surfaces, more vibrant accent colors). These two operations — evolve the tokens AND preserve the contracts — create a collision if done carelessly.

**Why it happens:**
Developers doing a visual refresh tend to "clean up" CSS vars they don't recognize, rename tokens for clarity, or reorganize the `:root` block. They see `--stream-status-size: 0.875rem` and think it's safe to fold into a generic typography scale. It isn't.

The `--gpt-*` legacy variable mappings are particularly at risk: they look like dead code because no component uses `--gpt-accent` directly. But they are required by the test contract AND may be referenced by components not yet audited.

**How to avoid:**
- Run `npm run test:run` before AND after every `globals.css` edit.
- Treat the following as immutable names (rename = breaking): `--stream-status-size`, `--stream-status-color`, `--stream-content-color`, `--citation-color`, `.stream-status-text`, `.stream-content-text`, `.citation-text`, `.animate-card-enter`, `.animate-pulse`, `--gpt-accent`, `--gpt-text`, `--gpt-background`.
- When adding new tokens, only ADD to the `:root` block — never rename existing names.
- Use a "token evolution" pattern: add the new value under a new name, then point old name at new name via `var()` if a value change is needed.
- Never do a global search-and-replace of CSS variable names without running the full test suite afterward.

**Warning signs:**
- `npm run test:run` output shows failures in `designTokens.test.ts`.
- The streaming skeleton (`BlockSkeleton.tsx`) loses its pulsing animation.
- Streamed citations (`--citation-color`) render in the wrong color.
- Dark mode breaks streaming text weight/size.

**Phase to address:** Token Refinement phase (first phase). Establish the "immutable names" rule before any file is edited.

---

### Pitfall 2: AI-Generated Images Look Inconsistent Across the Site

**What goes wrong:**
The project already has 16 topic images (in `/public/images/topics/`) and 14 product/fallback images (in `/public/images/products/`). Each was likely generated in a separate session with slightly different prompts. When shown together in a mosaic hero, carousel, and category browse row, they reveal mismatched lighting directions, inconsistent color palettes, and different levels of stylization. The result reads as "random AI images" rather than a cohesive editorial system.

This is the most visible quality difference between "Shopify-level polish" and "amateur AI collage."

**Why it happens:**
AI image generators introduce subtle variation even with identical prompts. Different prompt sessions, different seeds, and different models produce: warm vs. cool background tones, hard vs. soft lighting, photorealistic vs. stylized rendering, different apparent focal lengths, and different levels of background complexity. A single catalog of images generated across multiple sessions will have all of these inconsistencies.

**How to avoid:**
- Define a canonical style prompt prefix that is prepended to every image generation call. Example: `"editorial product photography, clean white-to-warm-ivory gradient background, soft natural lighting from upper-left, shallow depth of field, 50mm lens equivalent, high resolution, no text, no people"`.
- Lock the same model, same seed (where possible), and same aspect ratio across all generations in a batch.
- Generate ALL hero/carousel/category images in one session, not across multiple days.
- After generation, do a visual audit: lay all images side by side in a browser and check that backgrounds and lighting feel like one visual system.
- For images that don't fit: regenerate them with the canonical prefix, don't "adjust" them post-hoc with different prompts.
- The existing `topics/` images may need regeneration to match any new style system established by the mosaic hero images.

**Warning signs:**
- Mosaic hero grid shows images with obviously different color temperatures side by side.
- One carousel card has a white background, the next has a gradient — no visual system.
- Category browse cards look like they came from different stock photo sources.

**Phase to address:** Image Generation phase. Establish the canonical style prefix first, generate a single test batch of 3–4 images, review together, then generate the full set.

---

### Pitfall 3: Carousel Hero Image Causes LCP Regression

**What goes wrong:**
The mosaic hero and the `ProductCarousel` are the most visually prominent elements on the homepage and discover page respectively. They are almost certainly the LCP candidates. Both currently use `<img loading="lazy">` — appropriate for below-the-fold content, catastrophic for LCP elements.

Adding larger, bolder hero images (the Shopify-style mosaic) without adding `loading="eager"` and `fetchPriority="high"` to the first visible image will cause measurable LCP regression vs. the current placeholder-icon state.

**Why it happens:**
The existing `ProductCarousel` was built with `loading="lazy"` on the `<img>` tag (verified in `/components/discover/ProductCarousel.tsx`). When the carousel was using SVG icon placeholders, LCP wasn't an image — it was likely a heading. Once real images replace the placeholders, the image becomes the LCP candidate, and lazy loading it actively delays LCP by 300–800ms on mobile.

**How to avoid:**
- The FIRST slide image in `ProductCarousel` (slide index 0) must have `loading="eager"` and `fetchPriority="high"`. All other slides keep `loading="lazy"`.
- The mosaic hero: the largest, most prominent image cell must be the `priority` candidate.
- Do NOT use `next/image` for dynamic API product images from eBay/Amazon — they require external domains to be whitelisted in `next.config.js` (`remotePatterns`). Failing to configure this causes a server error, not graceful degradation. Use plain `<img>` with explicit width/height for dynamic images.
- DO use `next/image` for the static AI-generated images in `/public/images/` — they are local assets and benefit from automatic WebP conversion and optimization.
- Verify with Lighthouse or PageSpeed Insights after the image phase ships. Target LCP under 2.5s on mobile.

**Warning signs:**
- Lighthouse flags "Largest Contentful Paint image was lazy loaded."
- PageSpeed Insights shows LCP regression vs. pre-image baseline.
- Slow network test: carousel shows gradient background for 2+ seconds before image appears.

**Phase to address:** Image Integration phase. Apply `loading="eager"` to first carousel slide during the same PR that adds real images.

---

### Pitfall 4: CSS Variable Additions Without Dark Mode Counterparts

**What goes wrong:**
The visual refresh adds new tokens — bold accent colors, stronger surface tiers, mosaic gradient variables. If these are added only to `:root` (light mode) and not to `[data-theme="dark"]`, dark mode users see the wrong colors. This is particularly damaging for the mosaic hero gradients and card accent tints (`--card-accent-1` through `--card-accent-4` already exist in light mode only).

**Why it happens:**
Dark mode is an afterthought during initial implementation. A developer adds `--mosaic-gradient-1: linear-gradient(...)` in `:root`, uses it in the hero component, and the component looks correct in light mode. Dark mode toggle shows the same warm ivory gradient on a dark blue background — visually jarring.

The project uses `data-theme="dark"` on `<html>`, not the Tailwind `.dark` class. Any Tailwind `dark:` utilities added to new components are silently inert because `tailwind.config.ts` does not configure `darkMode: ['selector', '[data-theme="dark"]']`. (This was documented in the prior PITFALLS.md as Pitfall 7.)

**How to avoid:**
- Every new CSS variable added to `:root` must have a dark mode counterpart in `[data-theme="dark"]` in the same commit.
- Bold colors like `--primary: #1B4DFF` in light mode become `--primary: #3B82F6` in dark mode — the dark override already exists and should be extended consistently for any new token.
- New components must use `bg-[var(--surface)]` not `dark:bg-slate-900`. The `dark:` prefix does not work with the `data-theme` strategy.
- For mosaic gradients: define separate gradient variables in `[data-theme="dark"]` that use deep indigo/navy tones instead of warm ivory.
- After every new token addition, manually toggle to dark mode and screenshot the affected components.

**Warning signs:**
- Dark mode shows light-colored gradients on dark backgrounds.
- New card accent tints are too bright against the dark `#0A0E1A` background.
- Any `dark:` utility in a new component's className never activates.

**Phase to address:** Token Refinement phase. Immediately after adding any new light-mode tokens.

---

### Pitfall 5: Mosaic Hero Causes Layout Shift (CLS) on Load

**What goes wrong:**
A mosaic grid of images with different heights/aspect ratios will cause cumulative layout shift if image dimensions are not specified. The browser renders placeholder space, then re-layouts when images load, pushing content below the fold. On slow connections, the page layout visibly "jumps" twice — once when the DOM renders, once when images load.

This directly hurts Core Web Vitals and is visually disruptive, contradicting the "polished editorial" goal.

**Why it happens:**
Mosaic layouts require explicitly defining aspect ratios and heights for each grid cell. If image cells use `height: auto` with no `aspect-ratio` CSS, the browser cannot reserve space. With 5–8 cells loading in parallel, each load triggers a separate layout recalculation.

**How to avoid:**
- Every mosaic image cell must specify either `aspect-ratio` CSS or explicit `width` / `height` attributes (or both).
- Use CSS `aspect-ratio: 4/3` (or whatever the target ratio is) on the container, not the `<img>` itself — this reserves space before the image loads.
- Use `object-fit: cover` so images fill the reserved space without distorting.
- All AI-generated images in the mosaic should be generated at the same target resolution and aspect ratio (e.g., all `800x600`) to avoid jitter.
- If using `next/image`, always pass both `width` and `height` props.
- Measure CLS before and after the mosaic hero ships using Lighthouse.

**Warning signs:**
- Lighthouse CLS score above 0.1 on the homepage.
- Content below the hero visibly jumps as images load.
- Grid cells start collapsed (0px height) then expand.

**Phase to address:** Hero Mosaic phase. Include CLS measurement in the acceptance criteria.

---

### Pitfall 6: Adding Framer Motion Animations to Product Cards Causes Frame Drops During Chat Streaming

**What goes wrong:**
The visual refresh calls for "subtle animations" on premium product cards. If these use Framer Motion `layout` prop, `AnimatePresence`, or non-transform properties (backgroundColor, width, height), and product cards render during active chat streaming (SSE still in flight), the combined JavaScript work — LangGraph block processing + React reconciliation + Framer Motion layout calculations — drops to below 30fps on mid-range mobile.

**Why it happens:**
Framer Motion's `layout` prop triggers expensive layout calculations on every render. During streaming, `Message.tsx` re-renders on every new SSE chunk (via the `useStreamReducer`). If product cards have `layout` animations and they're inside a streaming message, every chunk triggers layout animation work. The existing `motion.div` in `Message.tsx` already animates the message wrapper; nesting more `motion` elements inside creates a cascade.

Additionally, the project uses Framer Motion 12.x (package.json shows `^12.26.2`), which was rebranded from `framer-motion` to `motion`. Bundle size is ~34KB for the full package. Without `LazyMotion`, this is loaded even on non-animation code paths.

**How to avoid:**
- Use CSS transitions (`transition-all duration-200`) for card hover effects instead of Framer Motion `whileHover` — CSS animations run on the compositor thread and do not touch JavaScript.
- Only use Framer Motion for entrance animations (once per card, not continuous).
- Never use the `layout` prop on product cards. Use `opacity` + `translateY` only.
- The `motion.div` wrapper in `Message.tsx` (lines 112–332) is protected — do not modify it. Add card animations below it, not as nested `motion` elements inside it.
- For the carousel, the existing custom transition (CSS `transition-all duration-700`) is better than a Framer Motion animation for performance.
- Test card animations with the chat streaming active simultaneously (type a question that triggers product results, watch frame rate in Chrome DevTools Performance tab).

**Warning signs:**
- Chrome DevTools Performance panel shows "Long Tasks" (>50ms) during streaming with product cards visible.
- Product card animations stutter or skip on first render mid-stream.
- Mobile users report cards appearing choppy while the AI is still responding.

**Phase to address:** Product Cards Redesign phase. No Framer Motion layout/stagger animations inside streaming message containers.

---

### Pitfall 7: External Product Image URLs Cause `next/image` Unconfigured Host Errors

**What goes wrong:**
Product images from eBay, Amazon, and Serper come from dozens of different CDN hostnames. If the team tries to use `next/image` for these external images (to get WebP optimization), every new CDN hostname that wasn't in `remotePatterns` returns a 400 error instead of an image. In production, this means broken image tiles — a highly visible regression.

The `next.config.js` currently has no `images.remotePatterns` configuration at all, confirming no external domains are whitelisted.

**Why it happens:**
Next.js image optimization proxies external images through `/_next/image?url=...`. For security, it requires all external domains to be explicitly listed in `remotePatterns`. E-commerce product images come from a non-enumerable set of CDNs (Amazon uses `m.media-amazon.com`, `images-amazon.com`, `images-na.ssl-images-amazon.com`; eBay uses `i.ebayimg.com`; Serper returns arbitrary image URLs). You cannot enumerate them all.

**How to avoid:**
- Use plain `<img>` tags for dynamic API product images (eBay, Amazon, Serper results). This is what all existing components correctly do — do not change this.
- Use `next/image` ONLY for static local assets in `/public/` — the AI-generated product images, topic images, and fallback images. These are always local and require no domain configuration.
- Do not add a wildcard `remotePatterns` entry (`hostname: '**'`) — this disables security protections and is a known vulnerability.
- If any new component template-codes `<Image src={externalUrl} ...>`, it will fail in production even if it works in development (dev mode skips the optimization proxy).

**Warning signs:**
- `Error: Invalid src prop on next/image: hostname "i.ebayimg.com" is not configured under images in your next.config.js`.
- Product images in carousels or result cards show the Next.js broken image placeholder instead of the product photo.
- Works fine locally but breaks on Vercel (where the optimization server is stricter).

**Phase to address:** Image Integration phase. Establish the rule: `next/image` for local static assets only, `<img>` for external API images.

---

### Pitfall 8: Typography Scale Conflicts Between Existing Components and New "Bold Editorial" Heading Sizes

**What goes wrong:**
The visual refresh adds stronger typography — larger headings, more dramatic size contrasts. But the project has 30+ existing components where heading sizes are hardcoded as Tailwind classes (`text-3xl`, `text-4xl`, `text-sm`) rather than semantic variables. If the new heading sizes are applied only to new components, the site has two type scales running simultaneously: the new bold editorial scale on redesigned components and the old subdued scale on untouched components.

The mismatched scales are most visible when old and new components appear on the same page (e.g., `ProductCards.tsx` in a chat result alongside a new `TopPickBlock.tsx` redesign).

**Why it happens:**
Brownfield redesigns rarely have time to touch every component. Components get redesigned in phases. The ones touched in early phases get the new scale; later phases see the inconsistency but "it'll be fixed later." Later never comes.

**How to avoid:**
- Do NOT hardcode new heading sizes as arbitrary Tailwind values. Use CSS variable-driven font size tokens.
- Add `--heading-xl`, `--heading-lg`, `--heading-md`, `--heading-sm` tokens to `globals.css` in the Token Refinement phase, then use these in both new and existing components.
- For components not being redesigned in this milestone, do a single sweep to replace `text-xl font-bold` with the equivalent token class. This is a low-risk, high-consistency win.
- Define the modular scale once (e.g., body: 1rem, heading-sm: 1.125rem, heading-md: 1.25rem, heading-lg: 1.5rem, heading-xl: 2rem) and commit it to `globals.css` before touching any component.
- Instrument Serif (`font-serif` class) is for editorial callout headings only. Do not apply it to product card titles — that creates visual noise.

**Warning signs:**
- The browse page `CategoryHero` has a dramatically larger heading than product result card titles on the same viewport.
- Comparing `/browse/[category]` and `/chat` shows obviously different heading weights.
- Font sizes change between pages when navigating — feels like two different apps.

**Phase to address:** Token Refinement phase. Codify the type scale before any component redesign.

---

### Pitfall 9: Hardcoded Gradient Colors in Carousel Slides Conflict With Dark Mode

**What goes wrong:**
The current `ProductCarousel` in `/components/discover/ProductCarousel.tsx` has hardcoded gradient strings per slide (e.g., `gradient: 'linear-gradient(135deg, #DBEAFE 0%, #93C5FD 50%, #60A5FA 100%)'`). These are soft blue/pink/purple pastels designed for the light ivory background. In dark mode, these pastel gradients appear washed out and low-contrast against the deep navy background (`#0A0E1A`), destroying the "bold colors" effect the refresh is supposed to add.

**Why it happens:**
Carousel slide data is static JavaScript objects — they can't reference CSS variables. A developer hardcodes hex values that look right in light mode during development, then ships without checking dark mode.

**How to avoid:**
- For the mosaic hero (new component), define gradient tokens in `globals.css` for both themes rather than hardcoding in the component: `--hero-gradient-1-light` and `--hero-gradient-1-dark`, then reference `var(--hero-gradient-1)` in the component.
- For the existing carousel's hardcoded gradients: either replace with `style={{ background: 'var(--card-accent-1)' }}` tokens (which already have dark mode overrides), or define a lookup table of dark-mode-safe gradients that activates based on `data-theme`.
- The cleanest solution: add a `gradientDark` field to each `ProductSlide` object, then read `document.documentElement.getAttribute('data-theme')` in a `useState`/`useEffect` to pick the correct gradient. This avoids SSR issues while solving the dark mode problem.

**Warning signs:**
- In dark mode, carousel cards look washed out or pastel instead of bold.
- Category browse cards have the same washed-out pastel issue.
- The hero mosaic is visually striking in light mode but looks wrong in dark mode.

**Phase to address:** Carousel Redesign phase and Hero Mosaic phase simultaneously.

---

### Pitfall 10: Design Drift Between Phases

**What goes wrong:**
A 5-phase visual overhaul done over multiple sessions will drift. Phase 1 establishes the token system. By Phase 3, the token values get adjusted. By Phase 5, some components reference old token values from memory, some reference the updated values, and some have new inline styles added "just for now." The final result has invisible inconsistencies that aren't obvious in individual component views but are jarring when seeing all pages together.

**Why it happens:**
Without visual regression testing, changes to shared tokens silently alter components that haven't been retouched in the current phase. A shadow value tweak in `globals.css` affects all 30+ components simultaneously, but only the ones being currently edited are checked visually.

**How to avoid:**
- Commit a visual baseline (screenshots) at the START of the project, before any changes.
- After each phase, do a manual walk-through of homepage, browse, and chat with a screen recording or series of screenshots.
- Keep the Chrome MCP visual QA task (Task 11 in the existing plan) as the gate for the LAST phase, not an afterthought.
- If a token value changes mid-project, do an immediate sweep of affected components rather than deferring.
- For this project, Vitest + `designTokens.test.ts` already provides contract testing for the stream tokens. Extend this pattern to cover new tokens: add assertions for new variable names in the same test file.

**Warning signs:**
- Cards on `/browse` have different border radius than cards on `/chat` results.
- The carousel hero uses a different shadow value than the product result cards.
- Font weights for "Expert Score" badges differ between the carousel and the product card component.

**Phase to address:** Visual QA phase (final phase). But also: run `npm run test:run` after every single globals.css change throughout all phases.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding hex colors in slide data objects | Fast to prototype | Dark mode broken, can't be themed | Never — use CSS variable references |
| Using `<img>` with no width/height for product images | Matches existing pattern | CLS hits, LCP penalty, layout jitter | Never for hero/LCP images; acceptable for deep-in-page thumbnails |
| Generating AI images in multiple separate sessions | Flexible timing | Visual inconsistency between batches | Never for images shown side-by-side |
| Adding Framer Motion `layout` prop to cards "just to see how it looks" | Beautiful demos | Frame drops during streaming | Never inside streaming message containers |
| Adding `remotePatterns: [{ hostname: '**' }]` to fix broken image errors | Unblocks work | Security vulnerability, Vercel may reject | Never |
| Adding new CSS tokens to `:root` only | Fast | Dark mode users see wrong colors | Never — always add dark mode counterpart in same commit |
| Forking `globals.css` per page with `<style>` tags | Isolates changes | Specificity wars, token drift, hard to debug | Never |
| Skipping the visual QA phase because "it looks fine in dev" | Saves time | Ships color/shadow inconsistencies that are hard to diagnose remotely | Never for production milestone |

---

## Integration Gotchas

Common mistakes when connecting visual changes to the existing system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `next/image` with eBay/Amazon URLs | Using `<Image src={externalProductUrl}>` | Use plain `<img>` for external URLs; `next/image` only for local `/public/` assets |
| Framer Motion inside `Message.tsx` | Adding `motion.div` children inside the existing `motion.div` wrapper | Use CSS transitions inside the message container; Framer Motion only at top-level entrances |
| Carousel image `loading` attribute | Keeping `loading="lazy"` on first slide after switching to real images | Set `loading="eager"` + `fetchPriority="high"` on the first (index 0) slide only |
| `data-theme="dark"` vs `.dark` class | Writing `dark:bg-slate-900` on new components | Use `bg-[var(--surface)]` always — `dark:` utilities are silently inert with this theming strategy |
| AI-generated image dimensions | Generating images at varying sizes, importing without specifying dimensions | All static hero/carousel images must be the same resolution; specify `width`/`height` on every `<img>` |
| Legacy `--gpt-*` variable names | Renaming them during cleanup | They are tested in `designTokens.test.ts` and may be used in non-audited components — treat as read-only |
| Tailwind `shadow-card`, `shadow-float` custom tokens | Adding new shadow values in `globals.css` but forgetting to add Tailwind mappings in `tailwind.config.ts` | Add both `globals.css` variable AND `tailwind.config.ts` `boxShadow` mapping in the same commit |

---

## Performance Traps

Patterns that work at small scale but degrade on mobile during real use.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `loading="lazy"` on hero/LCP image | LCP 3–5s on mobile, Lighthouse warning | Set `loading="eager"` + `fetchPriority="high"` on first visible image | Every mobile page load |
| Framer Motion `layout` on product cards | Frame drops to ~15fps during streaming | Use CSS transitions for hover; Motion for entrance only | Any mid-range mobile during active streaming |
| Full Framer Motion bundle (~34KB) loaded on all routes | Slower TTI on non-chat pages | Wrap animated components in `LazyMotion` + `m` component for non-critical pages | All pages once bundle >500KB |
| Multiple AI images loading in parallel on initial page render | All images compete for bandwidth, all arrive late | Load only the LCP candidate eagerly; lazy-load the rest | Slow 3G / mobile connections |
| `object-cover` on a container without explicit height | Image renders at 0px until aspect-ratio kicks in | Always pair `object-cover` with `aspect-ratio` CSS or explicit `height` | Every page load |
| Auto-playing carousel at 4s interval without pausing on reduced-motion | Battery drain, distracting for cognitive accessibility users | Respect `prefers-reduced-motion` — pause auto-play or disable transitions entirely | Always |
| Generating 800x600 PNG images for carousel thumbnails (instead of WebP) | ~500KB per image, slow carousel | Generate at target display size; use WebP format if the generator supports it | Slow connections, data-limited users |

---

## Security Mistakes

Domain-specific security issues for this visual overhaul.

| Mistake | Risk | Prevention |
|---------|------|------------|
| `remotePatterns: [{ hostname: '**' }]` in next.config.js | Open proxy for any image URL through your Vercel instance; potential abuse and cost | Use plain `<img>` for external images instead |
| Embedding AI image generation API keys in frontend code for "live generation" | Key exfiltration, unlimited generation charges | AI images are pre-generated and static — no API keys in frontend ever |
| Using `dangerouslySetInnerHTML` for rich product descriptions to "support markdown" | XSS if product description text comes from external API without sanitization | Use `react-markdown` (already in package.json) with `remarkGfm` — never raw HTML from API responses |

---

## UX Pitfalls

Common visual and interaction mistakes specific to this refresh.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| "Bold" colors applied uniformly to all text elements | Text hierarchy collapses — everything looks equally important | Bold colors only for callout badges, scores, CTA buttons; body text stays on warm ink tokens |
| Hero mosaic with 8+ images all loading simultaneously | Page feels slow on mobile; no perception of "loading" | Show gradient placeholders in each cell with a subtle shimmer; images fade in once loaded |
| Micro-animations on every interactive element (hover, focus, tap) | On low-end devices, the whole page feels laggy; users are distracted | Limit Framer Motion to 2–3 meaningful interactions per page; use CSS transitions for the rest |
| Product cards with too much information density in the "premium" redesign | Users overwhelmed; scan-ability worse than before | Keep the editorial restraint: one clear winner metric (score or price), truncate descriptions to 2 lines, expand on demand |
| AI images that "look AI" (uncanny product renders, geometric shapes, generic concept imagery) | Undermines editorial credibility — looks like a content farm | Editorial style prompt: real-world objects in natural settings, not composites; reject any image that looks like concept art |
| Replacing the FunPlaceholder fallback (which has no CLS) with a shimmer skeleton that has height transitions | CLS regression when shimmer transitions to loaded image | Use `aspect-ratio` on placeholder container — height is always reserved, only opacity changes on load |

---

## "Looks Done But Isn't" Checklist

Things that appear complete in DevTools but fail on real devices or at build time.

- [ ] **Hero mosaic LCP:** Run Lighthouse mobile — verify LCP image element is NOT flagged as lazy-loaded. Target LCP < 2.5s.
- [ ] **Dark mode token coverage:** Toggle theme on every page that has new components. No light-themed gradients should be visible on dark background.
- [ ] **AI image visual consistency:** Open all hero/carousel/category images side by side in a browser tab — verify lighting direction, color temperature, and background style are visually unified.
- [ ] **Token contract tests:** `npm run test:run` passes with no failures after every `globals.css` edit, including after adding new tokens.
- [ ] **No `next/image` with external URLs:** `grep -rn "next/image" components/ app/` — every `<Image>` component should only have `src` pointing to `/public/` paths.
- [ ] **Carousel first-slide eager loading:** Inspect the DOM — first carousel slide `<img>` has `loading="eager"` and `fetchpriority="high"`.
- [ ] **Product card animations don't fire during streaming:** Type a query that returns product results, watch the cards animate in while the stream is still active — no frame drops (>55fps in Performance panel).
- [ ] **CLS < 0.1:** Lighthouse CLS score on homepage after hero mosaic ships.
- [ ] **Reduced-motion compliance:** `@media (prefers-reduced-motion: reduce)` block in `globals.css` disables carousel auto-play and card entrance animations.
- [ ] **Typography consistent across pages:** Navigate browse → chat → results — heading sizes, font weights, and text colors feel like one continuous experience.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Token contract tests break | LOW | Run `git diff globals.css tailwind.config.ts`, identify renamed/removed tokens, restore original names while keeping new values |
| AI images visually inconsistent after batch generation | MEDIUM | Re-generate the outlier images with the canonical style prefix; don't try to fix via CSS filters |
| LCP regression from hero images | LOW | Add `loading="eager"` + `fetchPriority="high"` to first hero image; 15-minute fix |
| Dark mode broken for new components | LOW | Add dark-mode token counterparts to `[data-theme="dark"]` in globals.css; 30 min per component |
| CLS from mosaic hero | LOW-MEDIUM | Add `aspect-ratio` to all image containers; verify with Lighthouse; 1-2 hours |
| Framer Motion frame drops during streaming | MEDIUM | Replace `motion.div` with CSS transition equivalents inside Message containers; may require refactoring 2–3 components |
| next/image error for external URLs | LOW | Replace `<Image src={...}>` with `<img src={...}>` for the affected external images; 15-minute fix |
| Typography scale inconsistency across pages | MEDIUM | Define type scale tokens, do a grep-and-replace sweep across all 30+ components to use token classes |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Breaking protected token contract (Pitfall 1) | Token Refinement (Phase 1) | `npm run test:run` passes after every globals.css edit |
| AI image visual inconsistency (Pitfall 2) | Image Generation (Phase 2) | Side-by-side visual audit of all images before integration |
| Carousel LCP regression (Pitfall 3) | Image Integration (Phase 3) | Lighthouse mobile LCP < 2.5s after adding real images |
| New tokens missing dark mode counterparts (Pitfall 4) | Token Refinement (Phase 1) | Toggle dark mode immediately after adding any new token |
| Mosaic hero CLS (Pitfall 5) | Hero Mosaic (Phase 4) | Lighthouse CLS < 0.1 on homepage |
| Framer Motion frame drops during streaming (Pitfall 6) | Product Cards Redesign (Phase 5) | Chrome Performance tab while streaming product results |
| next/image external URL errors (Pitfall 7) | Image Integration (Phase 3) | `grep -rn "next/image"` audit; test on Vercel preview |
| Typography scale conflict (Pitfall 8) | Token Refinement (Phase 1) | Side-by-side browse + chat + results visual check |
| Carousel dark mode gradient mismatch (Pitfall 9) | Carousel Redesign (Phase 3) | Toggle dark mode with carousel visible |
| Design drift across phases (Pitfall 10) | Visual QA (Final Phase) | Full-site screenshot walk-through; extend designTokens.test.ts |

---

## Sources

- Next.js Image Component official docs: [Optimizing Images](https://nextjs.org/docs/14/app/building-your-application/optimizing/images)
- Next.js Image unconfigured host error: [next-image-unconfigured-host](https://nextjs.org/docs/messages/next-image-unconfigured-host)
- LCP lazy-loading regression: [Next.js Image Component: Performance and CWV in Practice — Pagepro](https://pagepro.co/blog/nextjs-image-component-performance-cwv/)
- LCP preload vs. over-preload tradeoffs: [Next.js Image Optimization — DebugBear](https://www.debugbear.com/blog/nextjs-image-optimization)
- Framer Motion bundle size and LazyMotion: [Reduce bundle size — Motion.dev](https://motion.dev/docs/react-reduce-bundle-size)
- Framer Motion animation performance: [Web Animation Performance Tier List — Motion.dev](https://motion.dev/magazine/web-animation-performance-tier-list)
- CSS variable dark mode FOUC: [Understanding & Fixing FOUC in Next.js App Router — DEV Community](https://dev.to/amritapadhy/understanding-fixing-fouc-in-nextjs-app-router-2025-guide-ojk)
- AI product image inconsistency: [Why AI Product Photography Fails at Catalog Consistency — Nextbuild](https://nextbuild.co/blog/ai-product-photos-inconsistent-ecommerce)
- AI image prompt consistency for batch generation: [JSON Prompts for AI Image Generation — DualView](https://www.dualview.ai/blog/guides/json-prompts-ai-image.html)
- CLS from missing image dimensions: [Next.js Image Optimization Complete Guide — BetterLink](https://eastondev.com/blog/en/posts/dev/20251219-nextjs-image-optimization/)
- Typography CLS from font loading: [Web Font Performance Checklist — DEV Community](https://dev.to/jacobandrewsky/web-font-performance-checklist-12i6)
- CSS variables in brownfield design systems: [Developer's Guide to Design Tokens — Penpot](https://penpot.app/blog/the-developers-guide-to-design-tokens-and-css-variables/)
- Project codebase (code-verified): `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/components/discover/ProductCarousel.tsx`, `frontend/components/ProductCards.tsx`, `frontend/components/Message.tsx`, `frontend/next.config.js`, `frontend/tests/designTokens.test.ts`, `frontend/app/layout.tsx`
- Project memory: CLAUDE.md (deployment lessons), MEMORY.md (editorial theme decisions, protected patterns)

---
*Pitfalls research for: Next.js 14 visual overhaul — bold editorial, AI-generated imagery, mosaic hero, premium product cards (ReviewGuide.ai v3.0)*
*Researched: 2026-03-31*
