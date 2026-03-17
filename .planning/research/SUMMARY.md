# Project Research Summary

**Project:** ReviewGuide.ai v2.0 Frontend UX Redesign
**Domain:** Mobile-first AI product research assistant — Discover → Chat → Results flow (brownfield Next.js 14 redesign)
**Researched:** 2026-03-16
**Confidence:** HIGH

## Executive Summary

ReviewGuide.ai v2.0 is a brownfield frontend redesign, not a greenfield build. The entire backend pipeline (LangGraph, SSE streaming, affiliate product search, travel, comparison, multi-turn clarification) is production-ready and must not be touched. The work is to layer a mobile-first, app-like UX over what already exists: replace the split Browse/Chat experience with a unified Discover → Chat → Results flow, introduce a bottom tab navigation shell for mobile, and add a dedicated Results screen for completed research sessions. Every competitor (Amazon Rufus, ChatGPT Shopping, Google AI Mode, Perplexity) uses mobile app conventions — bottom tabs, compact inline product cards, suggestion chips — and ReviewGuide's anonymous, editorial-first, cross-retailer positioning is a genuine differentiator that the v2.0 UX needs to visually reinforce.

The recommended approach is strictly additive and conservative: one new npm dependency (`tailwindcss-safe-area`), all other new capability drawn from libraries already installed (framer-motion 12.26.2, clsx, tailwind-merge, lucide-react 0.294). New components are isolated in `components/nav/`, `components/discover/`, and `components/results/` folders. The existing streaming pipeline, block rendering system, `chatApi.ts`, `useStreamReducer`, and all block renderers are treated as read-only. The build order — Navigation Shell first, then Discover, then Chat modifications, then Results, then placeholder routes — is dictated by hard component dependencies and cannot be safely reordered.

The primary risks are all mobile-browser-specific. The iOS virtual keyboard burying the chat input behind the newly-added bottom tab bar is the highest-probability defect, requiring `h-dvh` instead of `h-screen` plus explicit `env(safe-area-inset-bottom)` clearance from day one. A close second is SSE stream interruption when users switch tabs mid-response — this requires an architectural decision before tab navigation is built, not after. Dark-mode styling failures are a near-certainty unless new components exclusively use CSS variables (`var(--*)`) rather than Tailwind `dark:` utilities, which do not fire with the project's `data-theme` strategy.

---

## Key Findings

### Recommended Stack

The existing stack handles everything the redesign requires. The only new install is `tailwindcss-safe-area@^0.8.0`, which provides composable Tailwind classes (`pb-safe`, `h-safe`) for iOS notch and home-indicator clearance on the fixed bottom tab bar. All animation, routing, icon, and styling needs are already covered by framer-motion 12.26.2, lucide-react 0.294.0, clsx, tailwind-merge, and Next.js 14 built-ins.

**Core technologies:**
- **Next.js 14 App Router** — route structure for `/results/:id`, `/saved`, `/compare`, `/profile`; `useSelectedLayoutSegment` for active tab state (the correct App Router hook, not `usePathname` string matching)
- **Tailwind CSS 3** — all layout, responsive breakpoints (`md:hidden` for mobile-only nav, `lg:grid-cols-[1fr_400px]` for split panel), bottom nav and FAB positioning
- **framer-motion 12.26.2** — FAB spring animation, bottom nav active indicator via `layoutId`, page transitions via `template.tsx` pattern (NOT `AnimatePresence` in layouts — layouts do not unmount in App Router)
- **tailwindcss-safe-area 0.8.0** — the only new install; enables `pb-safe` on fixed bottom nav for iPhone home indicator clearance

**Critical version constraints:**
- Do NOT upgrade lucide-react mid-milestone — icon renames occurred between 0.294 and 0.577 and would break 20+ components
- Do NOT use the `viewTransition` experimental flag — requires Next.js ≥15.2.0; project is locked to 14.x
- `tailwindcss-safe-area@0.8.0` explicitly supports Tailwind v3; do not install the latest version if v3 support has been dropped

**What NOT to use:** shadcn/ui (conflicts with editorial design system), Radix Tabs for bottom nav (wrong ARIA semantics for navigation), `react-resizable-panels` (split panel is fixed proportion — 10 characters of Tailwind covers it), embla-carousel (CSS scroll snap achieves the same result at zero bundle cost).

### Expected Features

All backend features are already built. Feature scope is purely frontend surface — which UX surfaces must exist, which must be deferred, and which are anti-patterns for this product category.

**Must have for v2.0 launch (P1):**
- Unified Discover screen at `/browse` — single entry point replaces the current split browse/chat experience
- Bottom tab navigation (mobile only, 5 tabs: Discover, Saved, Ask FAB, Compare, Profile)
- Central FAB "Ask" button — 48px, center-bottom, navigates to `/chat?new=1`
- Compact inline product cards in chat — 80px height, horizontal layout; replaces the current full `ProductCards` blocks that overwhelm mobile chat
- Suggestion chips with auto-submit — horizontal scroll row below AI messages; backend already returns `next_suggestions`, needs pill styling
- Fix: review source URLs broken after `product_compose` refactor at commit `bd4b5c3` — must be resolved before source citation panel can display anything
- Source citation panel — collapsible, below summary; depends on the bug fix above
- Results screen `/results/:id` — desktop split panel, mobile full-width; dedicated shareable research view; no competitor offers this
- Rank badges (Top Pick, Best Value, contextual labels) — backend compose prompt already generates these contextually
- Placeholder routes: `/saved`, `/compare`, `/profile`

**Should have for v2.1 (P2):**
- Curated product grid on Discover — 120+ real products already exist in `curatedLinks.ts`; defer until v2.0 layout is stable
- Animated skeleton loading states (card-shaped, not generic `BlockSkeleton`)
- "More like this / Not interested" feedback buttons on inline product cards

**Defer to v3+ (out of scope for this milestone):**
- User accounts / login — anonymous-first is an explicit project constraint; accounts require months of auth, GDPR, and notification infrastructure
- Price alerts — requires accounts
- Cross-retailer price comparison via Skimlinks
- Voice input

**Anti-features to reject:**
- Full-page overlay modals for product detail (use the Results screen instead — same content, no UX trap)
- Paginated results (breaks conversation context — use a "See more alternatives" chip instead)
- Hamburger-only navigation on mobile (20% lower engagement than bottom tabs per NNGroup; hidden nav kills feature discovery)
- Real-time price refresh in chat (live price APIs are unreliable; use static curated prices labeled with a verification date)

### Architecture Approach

The redesign is layered over the existing codebase using a `NavLayout` wrapper component as the single point of nav decision — it renders `UnifiedTopbar` on desktop (≥1024px) and `BottomTabBar + ChatHeader` on mobile (<768px). Pages are nav-agnostic. The Results screen is a read-only view: it calls `fetchConversationHistory()` from the existing `chatApi.ts`, finds the last assistant message, runs it through `normalizeBlocks()`, and renders through the existing `UIBlocks` / `BlockRegistry` pipeline. No new streaming, no duplicated state. The `window.dispatchEvent(CustomEvent('sendSuggestion'))` pattern remains the only inter-component channel for suggestion chip clicks, but chips on any screen outside a mounted `ChatContainer` must use the URL-param route pattern (`/chat?q=...&new=1`) instead of dispatching the event.

**Major new components:**
1. `BottomTabBar` (`components/nav/`) — 5-tab mobile nav with central FAB; CSS `lg:hidden`; `useSelectedLayoutSegment` for active state; `pb-safe` for iPhone home indicator
2. `NavLayout` (`components/nav/`) — breakpoint-aware nav wrapper; renders `UnifiedTopbar` or `BottomTabBar + ChatHeader` per viewport; injected into route layouts, not root layout
3. `ChatHeader` (`components/nav/`) — mobile chat screen header with back, title, and expand-to-Results icon
4. `ResultsPage` (`app/results/[sessionId]/`) — reads session from localStorage or backend API; renders `ResultsHeader + SourcesPanel + CompactProductCard + UIBlocks`; no streaming
5. `TrendingCard` + `CategoryChips` (`components/discover/`) — Discover screen content; chip taps navigate via URL params, not `sendSuggestion`

**Reused without modification (protected):**
`chatApi.ts`, `useStreamReducer`, `normalizeBlocks.ts`, `BlockRegistry`, all block renderers, `ConversationSidebar`, `ErrorBanner`, `MessageRecoveryUI`

### Critical Pitfalls

1. **iOS virtual keyboard buries chat input behind the bottom tab bar** — Use `h-dvh` (not `h-screen`/`100vh`) on all full-height containers; add `viewport-fit=cover` to the layout viewport; position chat input at `bottom: calc(64px + env(safe-area-inset-bottom))`; use `tailwindcss-safe-area` for `pb-safe`. Must be verified on a real iOS device, not DevTools emulation. Phase: Navigation Shell.

2. **SSE stream killed when user navigates between tabs mid-response** — `ChatContainer` holds all stream state in local component state; navigation unmounts it and kills the stream. Architectural decision required before implementing tab navigation: parallel routes / persistent layout, or stream state in a context that survives route changes, or a warning banner when streaming. Do NOT modify `chatApi.ts` or `useStreamReducer`. Phase: this decision must be made in Phase 1 and cannot be retrofitted in Phase 3.

3. **Tailwind `dark:` utilities are inert — new components appear broken in dark mode** — The project uses `data-theme="dark"` on `<html>`, not the `.dark` class that Tailwind expects by default. Use CSS variables exclusively: `bg-[var(--surface)]`, `text-[var(--text)]`, `border-[var(--border)]`. Phase: Navigation Shell (before writing any new component).

4. **`h-screen` layout hides the last chat message behind the bottom tab bar** — The fixed tab bar overlays content without reducing the `h-screen` container. Add `pb-16 lg:pb-0` to the chat message scroll area immediately after adding the tab bar. A CSS custom property `--bottom-bar-height: 64px` (or `0px` on desktop) centralizes the fix. Phase: Navigation Shell.

5. **Hydration mismatch rendering bottom tab bar conditionally on SSR** — Never gate tab bar render on `window.innerWidth`; use CSS breakpoints only (`lg:hidden`). Active tab state uses `usePathname()` which is SSR-safe. Verify with `next build && next start`, not dev mode. Phase: Navigation Shell.

6. **`sendSuggestion` CustomEvent fires with no listener when chips are outside the `/chat` route** — Trending card taps on Discover and follow-up chips on Results must navigate via `/chat?q=...&new=1` URL params. The CustomEvent is only valid when `ChatContainer` is guaranteed to be mounted. Phase: Discover Screen.

7. **`useSearchParams()` without Suspense boundary causes full-page CSR bailout** — All new routes must wrap `useSearchParams()` consumers in `<Suspense>`. Follow the `chat/page.tsx` pattern. Verify with `next build` — new routes must show "(Static)" not "ƒ". Phase: New Routes Scaffolding.

---

## Implications for Roadmap

The build order is fixed by hard component dependencies. Navigation Shell must come before everything else because it establishes the layout context all other screens require. The SSE stream preservation decision must be made during Phase 1 because retrofitting a parallel-routes architecture after Phase 3 would require significant rework.

### Phase 1: Navigation Shell

**Rationale:** `BottomTabBar`, `NavLayout`, and `ChatHeader` are zero-dependency components that unblock all subsequent work. The Tailwind dark-mode strategy decision, iOS safe area setup, and `h-dvh` vs `h-screen` fix must happen here — before any other component is written — or every subsequent component will have the same defects. The SSE stream-on-tab-switch architectural decision must also be resolved in this phase, because it determines whether `/chat` needs a persistent layout.

**Delivers:** Mobile bottom tab navigation with 5 tabs and central FAB; correct iOS safe area clearance; `h-dvh` layout baseline; `tailwindcss-safe-area` installed and configured; `viewport-fit=cover` in `layout.tsx`; `NavLayout` wrapper ready for all routes; `UnifiedTopbar` self-hidden on mobile.

**Addresses:** Table-stakes bottom tab nav (P1), FAB button (P1), 44px touch targets (table stakes)

**Avoids:** Pitfalls 1, 2, 3, 4, 5 (all concentrated in the Navigation Shell phase)

**Research flag:** Standard — well-documented Next.js App Router patterns. No research phase needed.

---

### Phase 2: Discover Screen

**Rationale:** The Discover screen replaces `/browse` and becomes the app's entry point. It depends on `NavLayout` (Phase 1) for correct layout context. New components (`CategoryChips`, `TrendingCard`) have no streaming or data dependencies, making this low-risk to build before touching the Chat screen. Trending card and hero search input taps use the existing `/chat?q=...&new=1` URL-param flow — no new backend integration required.

**Delivers:** Unified entry point at `/browse`; category chip row (8 chips, horizontal scroll); 3 seeded trending research cards; hero search input; recent searches carried over from existing implementation.

**Addresses:** "What do I ask?" discovery problem (P1), category entry points (P1), unified single-surface product experience (P1)

**Avoids:** Pitfall 6 (chip taps use URL params, not `sendSuggestion` CustomEvent)

**Research flag:** Standard — pure UI work over existing routing patterns. No research phase needed.

---

### Phase 3: Chat Screen Modifications

**Rationale:** Modifying the Chat screen (adding `ChatHeader` on mobile, changing `Message.tsx` bubble CSS, updating `ChatContainer` welcome screen) depends on `NavLayout` being in place (Phase 1). This phase touches live streaming UI, so scope is deliberately limited to CSS-only changes and component composition — no logic modifications. Compact inline product cards represent the highest-impact mobile UX change in the entire milestone.

**Delivers:** `ChatHeader` on mobile (back button + expand-to-Results icon); restyled message bubbles; compact inline product cards in chat (80px height, horizontal layout); suggestion chips with pill styling and auto-submit; real-time chat header status ("Researching • N sources analyzed"); rank badges (Top Pick, Best Value); updated `ChatContainer` welcome screen.

**Addresses:** Compact inline product cards (P1), suggestion chips (P1), rank badges (P1), chat header status (P1)

**Avoids:** Pitfall 4 (horizontal carousel inside `overflow:hidden` ancestors — must be tested during this phase)

**Note:** The bug fix for broken `review_sources` URLs (broken after the `product_compose` refactor at commit `bd4b5c3`) must be included in this phase, because the Source Citation Panel in Phase 4 depends on it.

**Research flag:** The `review_sources` bug fix needs targeted investigation. The root cause is known (field dropped after `product_compose` refactor) but the exact field path in the LangGraph output that stopped being populated needs to be traced before writing the SourcePanel component. A targeted debug session is recommended before implementation starts.

---

### Phase 4: Results Screen

**Rationale:** The Results screen (`/results/:sessionId`) depends on the Chat screen having a working expand icon (`ChatHeader` from Phase 3). It reuses `ConversationSidebar`, `UIBlocks`, and `normalizeBlocks` unchanged. The desktop split panel uses pure CSS Grid — no resize library. This is the highest-complexity phase (new route, new data fetching, new layout) and benefits from all prior phases being stable.

**Delivers:** `/results/:id` route; `ResultsHeader` with share/save/refresh; collapsible `SourcesPanel` with source citation dots; `CompactProductCard` carousel (170px mobile / 200px desktop); desktop split panel (`lg:grid-cols-[320px_1fr]`); `ResultsSidebar` wrapping existing `ConversationSidebar`; mobile full-width layout.

**Addresses:** Results screen (P1), source citation panel (P1, requires Phase 3 bug fix)

**Avoids:** Anti-pattern of duplicating SSE logic in ResultsPage — Results is read-only via `fetchConversationHistory()`, never streams

**Research flag:** `fetchConversationHistory()` currently returns all messages for a session. For ResultsPage to be production-reliable at scale, confirm whether a `?limit=` param or a dedicated `/last-result` endpoint is needed. Light research recommended before building the Results data layer.

---

### Phase 5: Placeholder Routes and QA

**Rationale:** `/saved`, `/compare`, and `/profile` are layout-only stubs that activate the corresponding bottom tab items. These must not throw errors or expose session data. The `useSearchParams()` Suspense wrapper pattern from `chat/page.tsx` must be applied to every new page. `next build` verification is the acceptance gate for the entire milestone.

**Delivers:** `/saved`, `/compare`, `/profile` placeholder pages with bottom tab integration; `next build` passes cleanly with all new routes as static; "Looks Done But Isn't" checklist completed on real iOS Safari (keyboard overlap, carousel swipe, dark mode, stream-on-tab-switch).

**Addresses:** All placeholder route requirements; full-milestone mobile QA

**Avoids:** Pitfall 7 (Suspense wrappers on all new pages), broken Vercel preview deploys, `throw new Error("not implemented")` in placeholder routes

**Research flag:** Standard — static placeholder pages. No research needed.

---

### Phase Ordering Rationale

- **Phase 1 before everything:** `NavLayout` is a build-time dependency of every subsequent route. Dark mode strategy and `h-dvh` are retroactively expensive to fix across multiple components — set the pattern before writing anything else.
- **Phase 2 before Phase 3:** Discover screen is pure UI with no streaming risk; safer to validate the nav shell and discover layout before touching the streaming Chat screen.
- **Phase 3 before Phase 4:** Results screen requires the Chat → Results expand navigation wired in `ChatHeader`, which is delivered in Phase 3.
- **Phase 5 last:** Placeholder routes are dependency-free stubs; building them last avoids polluting earlier phases with stub routes that could mask routing bugs.
- **SSE stream decision in Phase 1 (critical):** The stream-preservation architecture (parallel routes vs persistent layout vs warning banner) must be resolved before Phase 3 modifies the Chat screen. A Phase 3 retrofit of routing architecture carries high rework risk and is the single most expensive mistake possible in this milestone.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 3 (review_sources bug fix):** The broken `review_sources` field is confirmed but the exact field path in the LangGraph output needs to be traced before writing the `SourcesPanel` component. Recommend a targeted debug session — inspect `product_compose` tool output and confirm where `review_sources` is being dropped — before planning Phase 3 tasks.
- **Phase 4 (session history API):** `fetchConversationHistory()` currently returns all messages. For ResultsPage production reliability, confirm whether a `?limit=` param or `/last-result` endpoint is needed. Low-complexity research but worth confirming before building the Results data layer.

Phases with standard patterns (skip research-phase):

- **Phase 1 (Navigation Shell):** Bottom tab navigation, safe areas, `h-dvh`, CSS-only responsive nav — all have well-documented patterns in Next.js 14 official docs and framer-motion docs.
- **Phase 2 (Discover Screen):** Pure UI components over existing routing. No new integrations.
- **Phase 5 (Placeholder Routes):** Static page scaffolding. No research needed.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing codebase confirmed via `package.json` and `package-lock.json`. One new dependency (`tailwindcss-safe-area`) verified on npm with correct Tailwind v3 compatibility. Version constraints (lucide-react, framer-motion) confirmed against actual installed files. |
| Features | HIGH | Primary sources: direct competitor analysis (Rufus, ChatGPT Shopping, Perplexity, Google AI Mode), Figma design spec, full codebase audit. Feature dependencies explicitly mapped. Known bug (`review_sources`) identified and scoped. |
| Architecture | HIGH | Based on direct codebase analysis of all major files. Component boundaries, data flows, and anti-patterns drawn from the actual implementation. Build order derived from real component dependencies, not speculation. |
| Pitfalls | HIGH | 8 critical pitfalls identified; all code-verified against the current codebase. iOS keyboard overlap, hydration mismatches, and SSE stream interruption confirmed against real Next.js 14 / iOS Safari behavior. Phase-to-pitfall mapping is specific and actionable. |

**Overall confidence:** HIGH

### Gaps to Address

- **SSE stream-on-tab-switch architecture decision:** Three options exist (Next.js parallel routes, persistent layout via React context/Zustand, warning banner with graceful interruption). Each has different Phase 1 scope implications. This must be decided before the roadmap is finalized — the research documents the options but the decision requires a product input on the acceptable UX tradeoff.

- **`review_sources` bug root cause:** The bug is confirmed (broken after `product_compose` refactor at commit `bd4b5c3`) but the exact field path in the LangGraph output that stopped being populated has not been traced. Phase 3 implementation should begin with this investigation.

- **Session ID security on `/results/:id`:** PITFALLS.md flags that using the raw `sessionId` in the URL enables session hijacking if URLs are shared. An opaque result ID separate from the chat session ID would be more secure. The v2.0 scope does not include sharing features, but the route design choice should be intentional.

- **lucide-react upgrade path:** Pinned at 0.294.0 to avoid mid-milestone icon renames. A dedicated upgrade task should be scheduled after v2.0 ships to bring it current (~0.577.0).

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — `frontend/app/`, `frontend/components/`, `frontend/lib/`, `frontend/tailwind.config.ts`, `package.json`, `package-lock.json` — direct analysis
- Next.js official docs — `useSelectedLayoutSegment`, `useSearchParams` Suspense requirement, `viewTransition` version requirement
- npm package registry — `tailwindcss-safe-area@0.8.0` Tailwind v3 compatibility confirmed
- Tailwind CSS docs — scroll snap, safe area classes
- CLAUDE.md, MEMORY.md — project constraints, known pitfalls, component protection rules
- Figma spec — "ReviewGuide.ai — New UX Concept" (`frontendredesign.txt` in project root)

### Secondary (MEDIUM confidence)

- framer-motion App Router `template.tsx` pattern — community-validated, widely used, no official framer-motion docs for this specific pattern
- lucide-react icon rename risk (0.294 → 0.577) — inferred from release notes pattern across the release history
- iOS virtual keyboard behavior with fixed elements — documented by Samuel Kraft (safari-15-bottom-tab-bars-web) and DEV.to (VisualViewport fix)
- Tailwind dark mode selector strategy with `data-theme` — confirmed via project `globals.css` + Medium article (asyncme/mastering-custom-dark-mode)
- Competitor UX analysis — Amazon About page, OpenAI blog, Engadget, Think with Google

### Tertiary (LOW confidence)

- Framer Motion mobile optimization guidance — studyraid.com (secondary aggregation site; treat as directional, not authoritative)
- NNGroup hamburger vs bottom tab engagement figure (20% lower engagement) — referenced via UXmatters; original NNGroup study not directly verified

---

*Research completed: 2026-03-16*
*Ready for roadmap: yes*
