# Pitfalls Research

**Domain:** Mobile-first frontend redesign — Next.js 14, chat/browse unification, bottom tab navigation, SSE streaming preservation
**Researched:** 2026-03-16
**Confidence:** HIGH (code-verified + web research confirmed)

---

## Critical Pitfalls

### Pitfall 1: iOS Virtual Keyboard Buries the Chat Input Behind the Bottom Tab Bar

**What goes wrong:**
When the soft keyboard opens on iOS Safari, fixed elements anchored at `bottom: 0` do not move — they stay glued to the layout viewport bottom, which is now hidden behind the keyboard. The chat input bar disappears, the bottom tab bar overlaps the input, and the user cannot type.

**Why it happens:**
iOS Safari (before 15.4) does not resize the layout viewport when the keyboard opens — only the visual viewport shrinks. Any `position: fixed; bottom: 0` element is anchored to the layout viewport, so it stays pinned behind the keyboard. This is compounded when there are two stacked fixed elements: the bottom tab bar AND the chat input bar both fight for `bottom: 0` z-space.

The current chat page already uses `h-screen flex flex-col overflow-hidden` which can partially mitigate this, but the new bottom tab bar introduces a second fixed layer that wasn't there before.

**How to avoid:**
- Use `h-dvh` (dynamic viewport height, Tailwind) on full-height containers instead of `h-screen` — `dvh` accounts for the keyboard's visual viewport changes.
- Add `viewport-fit=cover` to the viewport meta tag in `layout.tsx` so `env(safe-area-inset-bottom)` works for notched iPhones.
- Give the bottom tab bar `padding-bottom: env(safe-area-inset-bottom)` to clear the iPhone home indicator.
- Position the chat input bar using `bottom: calc(64px + env(safe-area-inset-bottom))` when the tab bar is visible, so it sits above the tab bar.
- On the `/chat` route specifically, consider hiding the bottom tab bar when the keyboard is open (listen to `visualViewport` resize events) or use the `interactive-widget=resizes-content` viewport option (Chrome Android only).
- Do NOT use `100vh` for any full-height layouts in the redesign — replace with `h-dvh` or `min-h-dvh`.

**Warning signs:**
- In Chrome DevTools mobile emulation: chat input bar appears covered or zero-height when keyboard is simulated.
- On real iOS device: typing in chat scrolls the page instead of keeping the input in view.
- Bottom tab bar icon labels cut off — indicates safe area inset is missing.

**Phase to address:** Navigation Shell phase (bottom tab bar creation). Must be verified on real iOS device before shipping.

---

### Pitfall 2: Hydration Mismatch When Rendering Bottom Tab Bar Conditionally on SSR

**What goes wrong:**
The bottom tab bar is mobile-only. If you render it conditionally based on `window.innerWidth` or a `useMediaQuery` hook that reads `window` during SSR, Next.js will throw a hydration mismatch: server renders the tab bar absent, client renders it present (or vice versa), React bails out.

**Why it happens:**
Next.js renders components on the server where `window` is undefined. The server produces HTML without the tab bar. The client re-renders with the tab bar visible. React detects the mismatch and throws. This already burned the project once (noted in CLAUDE.md: "Avoid Math.random() in SSR").

The UnifiedTopbar already has mobile-detection logic (`mobileSearchOpen` state) but it gates rendering inside `useEffect`. The new bottom tab bar will need the same discipline.

**How to avoid:**
- Never gate the tab bar render on `window.innerWidth` — use CSS only (`lg:hidden` Tailwind class) to hide/show it. Let the DOM element exist on both server and client; CSS controls visibility.
- If the tab bar must be dynamically imported (e.g., it uses a browser-only API), use `next/dynamic` with `{ ssr: false }`.
- The tab bar's `active` state (which tab is highlighted) can use `usePathname()` safely — it's SSR-safe in Next.js App Router.
- Never read `localStorage` to determine initial tab bar state during render — move to `useEffect`.

**Warning signs:**
- Browser console: "Hydration failed because the initial UI does not match" — usually identifies the specific component.
- Tab bar flashes in/out on initial page load (FOUC pattern).
- `suppressHydrationWarning` appearing in tab bar JSX is a red flag — it masks the problem rather than fixing it.

**Phase to address:** Navigation Shell phase. Verify with `next build && next start` (not dev mode — dev mode is more forgiving).

---

### Pitfall 3: SSE Stream Killed When User Navigates Between Browse and Chat Tabs

**What goes wrong:**
The new unified flow means users can tap the "Discover" tab mid-stream while the AI is still generating a response. The SSE connection in `ChatContainer` is tied to component mount. If the user navigates away, the component unmounts, the stream aborts, and the response is lost. When the user taps back to Chat, they see a blank or partial message.

**Why it happens:**
`ChatContainer` holds all stream state in local component state (`useStreamReducer`, `messages`, etc.). Navigation unmounts the component, which runs cleanup (`useEffect` returns). The `useStreamReducer` watchdog fires `STREAM_INTERRUPTED`. Redis halt-state does not save mid-stream content — it saves only the state when `HaltStateManager` is explicitly called by the backend (clarification halts), not mid-generation.

The existing SSE reconnection logic handles network drops but not intentional navigation away.

**How to avoid:**
- Keep `ChatContainer` mounted while on the `/chat` route — do not put it inside a conditional that unmounts it during tab switches.
- If the Discover tab and Chat tab render separate page components, use Next.js parallel routes or a persistent layout so `ChatContainer` is never unmounted when switching between Discover and Chat.
- Alternatively: persist stream state to a React context (or Zustand store) that survives route changes, and re-attach UI to it on mount.
- At minimum: detect `isStreaming` and warn the user before navigating away (a subtle "AI is still responding..." banner in the tab bar is sufficient).
- Do NOT modify `chatApi.ts` streaming logic or `useStreamReducer` — per project constraints. Work around them at the routing layer.

**Warning signs:**
- In DevTools Network tab: SSE connection shows "canceled" on every tab switch.
- `STREAM_INTERRUPTED` fires immediately when navigating away even mid-response.
- Users report "my answer disappeared when I switched tabs."

**Phase to address:** Routing Unification phase (merging Browse/Chat). Must be architectural decision before implementing tab navigation.

---

### Pitfall 4: Blocking `overflow: hidden` on a Parent Container Kills Horizontal Product Carousel Touch Scroll

**What goes wrong:**
When adding the split-panel desktop layout (sidebar + content), a parent container gains `overflow: hidden` to clip the sidebar. This silently breaks horizontal swipe/scroll on product carousels inside the content area — the touch gesture is consumed by the clipping ancestor.

The existing `ProductCarousel` uses `overflow: hidden` on its container with CSS `transform: translateX()` pagination (not native scroll). The new design spec calls for CSS `scroll-snap` horizontal carousels on mobile. If any ancestor has `overflow: hidden`, the native horizontal scroll stops working.

**Why it happens:**
CSS `overflow: hidden` on a containing block establishes a new stacking context. Touch events for horizontal scroll inside that block work, but CSS scroll-snap and `overflow-x: auto` carousels inside it are clipped and the scroll container becomes invisible to touch handlers if the parent overflow clips it.

Specifically: the chat page uses `overflow-hidden` on `<div className="h-screen flex flex-col overflow-hidden">`. Product blocks render inside `<main className="flex-1 flex flex-col overflow-hidden">`. Nested `overflow-hidden` containers already exist — any horizontal scroll carousel must be tested in this exact nesting.

**How to avoid:**
- Use CSS-only horizontal scroll: `overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch` with `scroll-snap-align: start` on children. This is more mobile-reliable than the current JS-pagination approach.
- On the carousel container itself: `overscroll-behavior-x: contain` to prevent scroll chaining to the vertical page scroll.
- Avoid `overflow: hidden` on layout ancestors when horizontal carousels are descendants — use `overflow: clip` instead (clips but does not establish scroll container, so nested scroll elements still work).
- Test the carousel on actual touch device, not just DevTools — DevTools does not accurately simulate scroll containment bugs.

**Warning signs:**
- Carousel shows arrows but swipe does nothing on mobile.
- Touch events "stick" or scroll the page vertically instead of the carousel horizontally.
- Carousel scrolls fine in DevTools but fails on iPhone Safari.

**Phase to address:** Product Cards Redesign phase. Also re-test in the Results split-panel layout phase.

---

### Pitfall 5: The `sendSuggestion` CustomEvent Pattern Breaks if the Chat Container is Not Mounted

**What goes wrong:**
The codebase uses `window.dispatchEvent(new CustomEvent('sendSuggestion', ...))` as the follow-up chip click mechanism. This works when `ChatContainer` is mounted and listening. In the new unified flow, if suggestion chips appear on a Results page or anywhere outside the active `/chat` route, dispatching the event fires into the void — no listener exists, the message is never sent, the user gets no feedback.

**Why it happens:**
The pattern is a window-level pub/sub. It works because currently all suggestion chips only appear inside `ChatContainer`'s render tree, which is always mounted on `/chat`. Once the redesign adds suggestion chips on the Discover screen (trending queries) or Results pages, the dispatch can happen before `ChatContainer` has mounted its listener.

**How to avoid:**
- Before adding suggestion chips on any screen outside `/chat`, audit whether `ChatContainer` is guaranteed to be mounted.
- For cross-page chip taps: route to `/chat?q=<query>&new=1` instead of dispatching the CustomEvent — use the existing URL-param flow (`initialQuery` prop) which already handles this case correctly.
- The `sendSuggestion` CustomEvent should only be used for chips rendered INSIDE a mounted `ChatContainer`. Chips outside it should use router navigation.
- Do NOT change the existing `sendSuggestion` listener in `ChatContainer.tsx` — per project constraints. Only change the dispatch sites.

**Warning signs:**
- Clicking a trending query chip on the Discover screen does nothing.
- No console errors (event dispatches silently with no listeners).
- Only manifests when the user is on a non-chat route.

**Phase to address:** Discover Screen Unification phase. Any chip component that may render outside ChatContainer must use the URL-param route pattern instead.

---

### Pitfall 6: `useSearchParams()` Without Suspense Boundary Causes Full-Page CSR Bailout on New Routes

**What goes wrong:**
The chat page already wraps `useSearchParams()` in a `<Suspense>` boundary (see `ChatPage` in `chat/page.tsx`). But the new routes (`/results/:id`, `/saved`, `/compare`, `/profile`) are placeholder pages. If any of them — or any component they import — calls `useSearchParams()` without a Suspense wrapper, Next.js 14 bails out the entire route into client-side rendering, breaking static prerendering and causing a blank flash on initial load.

**Why it happens:**
In Next.js 14 App Router, `useSearchParams()` opts the nearest Suspense boundary (or entire page) into CSR. This is documented but easy to miss when building placeholder pages quickly. Even importing a component that internally uses `useSearchParams()` (like the UnifiedTopbar if it reads search params) can trigger this.

**How to avoid:**
- Every new page that uses `useSearchParams()` (directly or transitively) must wrap the component in `<Suspense fallback={...}>`.
- Pattern to follow: the existing `ChatPage` wrapper in `chat/page.tsx` — it exports a bare `ChatPage` that returns `<Suspense><ChatPageContent /></Suspense>`.
- For placeholder pages (`/saved`, `/compare`, `/profile`): if they don't need search params, don't import any component that reads them.
- Run `next build` before each phase ships — the build output shows "x" (static) vs "ƒ" (dynamic) per route. New routes should be static unless they need dynamic data.

**Warning signs:**
- Build output shows new routes marked "ƒ" (server-rendered on each request) unexpectedly.
- Initial page load shows blank flash before content appears.
- Console warning: "useSearchParams() should be wrapped in a suspense boundary."

**Phase to address:** New Routes Scaffolding phase. Apply the Suspense wrapper template from `chat/page.tsx` to every new page.

---

### Pitfall 7: Tailwind `dark:` Utilities Are Inert Because the Project Uses `data-theme` Not `.dark` Class

**What goes wrong:**
The project uses `document.documentElement.setAttribute('data-theme', 'dark')` for theming, not the `.dark` class Tailwind expects by default. Any new component written with `dark:bg-gray-900` or `dark:text-white` utilities will not respond to the theme toggle — those utilities only activate when a `.dark` class is on `<html>`.

**Why it happens:**
Tailwind's default dark mode strategy is `class` (looking for `.dark`). The project chose CSS variable-based theming via `data-theme="dark"` on the root element. The `globals.css` defines `[data-theme="dark"]` CSS variable overrides. But if a developer writes Tailwind `dark:` utilities, those require `darkMode: ['selector', '[data-theme="dark"]']` in `tailwind.config.ts` — and that config line is currently missing.

The existing components work because they use CSS variables directly (`bg-[var(--surface)]`), not `dark:` utilities. New bottom tab bar or navigation components built with `dark:` utilities will be visually broken in dark mode.

**How to avoid:**
- Use CSS variables exclusively: `bg-[var(--background)]`, `text-[var(--text)]`, `border-[var(--border)]` — not `dark:` Tailwind utilities.
- If `dark:` utilities are needed, add `darkMode: ['selector', '[data-theme="dark"]']` to `tailwind.config.ts` first and verify no existing components regress.
- Establish a linting rule or PR checklist: no `dark:` prefix in new components without first confirming the selector strategy is configured.

**Warning signs:**
- New component looks correct in light mode but has incorrect colors in dark mode.
- Toggling theme in the browser changes the `data-theme` attribute but new components don't respond.
- The new bottom tab bar is light-colored when dark mode is active.

**Phase to address:** Navigation Shell phase — before any new component is written, decide the strategy and document it.

---

### Pitfall 8: `h-screen` on the Chat Layout Causes Double Scrollbars When the Bottom Tab Bar Is Added

**What goes wrong:**
The current chat page uses `<div className="h-screen flex flex-col overflow-hidden">`. The entire layout fits inside the viewport. Adding a `64px` bottom tab bar as a fixed overlay reduces visible content area by 64px but does not reduce the `h-screen` container — the chat message list scrolls behind the tab bar, and the last message is permanently hidden under it.

**Why it happens:**
`h-screen` is `100vh` which equals the total viewport height. A fixed-position tab bar (not in document flow) doesn't reduce this. The chat scroll area's bottom padding needs to account for the tab bar height. This is the same class of bug as the keyboard overlap — fixed elements overlay content without shrinking the layout container.

**How to avoid:**
- Add `pb-16` (64px) to the chat message list container — or use CSS `padding-bottom: calc(64px + env(safe-area-inset-bottom))` on the scrollable messages area.
- On `/chat` route specifically, where the tab bar is visible, the `ChatContainer` scroll area needs explicit bottom padding to not be hidden under the tab bar.
- Use a CSS custom property `--bottom-bar-height: 64px` (or `0px` on desktop) that gets applied as padding to all scrollable content areas — this centralizes the fix.
- Desktop: tab bar is hidden (`hidden lg:flex` pattern for tab bar) so no padding needed.

**Warning signs:**
- Last message in chat is cut off at the bottom.
- User has to scroll up slightly to see the send button or last AI message.
- In DevTools: `.messages-scroll-area` has no bottom padding while the tab bar is visible.

**Phase to address:** Navigation Shell phase — immediately after bottom tab bar is added, audit every scrollable content area for bottom clearance.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `Math.random()` for tab bar item keys | Quick to write | Hydration crash on SSR | Never — use index or deterministic ID |
| Adding `suppressHydrationWarning` to hide mismatches | Silences console errors | Masks real SSR bugs that become user-facing | Never for layout components |
| Copy-pasting ChatContainer into a new Results page | Fast to build Results view | Two sources of truth for stream state; bugs diverge | Never — extract shared logic to a context |
| Using `window.innerWidth` checks in render for responsive behavior | Familiar React pattern | Hydration mismatches on every SSR page | Never — use CSS breakpoints or `useEffect` |
| Hardcoding `bottom: 64px` everywhere tab bar appears | Simple | Breaks if tab bar height changes or is hidden on desktop | Never — use a CSS variable |
| `position: fixed` for bottom tab bar without `z-index` planning | Works initially | Overlapped by modals, drawers, or the SSE skeleton overlay | OK only if z-index map is created in the same PR |
| Placeholder routes that `throw new Error("not implemented")` | Marks as TODO | Crashes production if user navigates there | Never — use minimal placeholder UI instead |

---

## Integration Gotchas

Common mistakes when connecting to the existing system during the redesign.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `window.dispatchEvent(new CustomEvent('sendSuggestion'))` | Dispatching from Discover screen chips | Route to `/chat?q=...&new=1` — CustomEvent only works inside mounted ChatContainer |
| `useStreamReducer` hook | Wrapping ChatContainer in a new Context provider that also manages stream state | `useStreamReducer` is self-contained; new state should compose with it, not replace it |
| `normalizeBlocks` + `UIBlocks` dispatcher (BlockRegistry) | Rendering blocks with a custom renderer "just for the Results page" | Always go through `BlockRegistry` — it is the authoritative block renderer |
| Dark mode toggle in `UnifiedTopbar` | Adding `dark:` Tailwind classes to new components | Use CSS variables (`var(--*)`) — `dark:` classes don't activate with `data-theme` strategy |
| `ConversationSidebar` in split-panel Results layout | Re-implementing conversation list with own API calls | `ConversationSidebar` already handles API fetching; pass `currentSessionId` prop and reuse |
| Vercel preview URL CORS | New routes trigger new preview URL deployments | `CORS_ORIGIN_REGEX` on Railway already covers `*.vercel.app` — no action needed per route, but verify it's still set |
| SSE `MAX_RETRIES` / reconnect logic in `chatApi.ts` | Modifying retry config to "fix" mobile stream drops | Do not modify `chatApi.ts` streaming logic — if stream drops on mobile tab switch, handle at routing layer |

---

## Performance Traps

Patterns that work in testing but degrade on mobile hardware.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Framer Motion `layout` prop on chat message list | Smooth in dev, janky on low-end Android | Only animate `opacity` and `translateY` — never `layout` on frequently-updating lists | Any device below ~4 CPU cores |
| Framer Motion `AnimatePresence` wrapping every product card in a carousel | Cards animate beautifully in lab | 6+ animated cards simultaneously causes frame drops | Mobile with 5+ products visible |
| `window.addEventListener('resize', ...)` for responsive carousel (existing ProductCarousel) | Works on desktop | Fires continuously on mobile scroll (iOS triggers resize as URL bar hides/shows) | Always on iOS — use `ResizeObserver` instead |
| Loading product images without explicit `width`/`height` attributes | Fast to write | Layout shift (CLS) during chat stream as images load | Every page load with product cards |
| Importing all icon components from `lucide-react` in the tab bar | Convenient | Adds ~200KB to tab bar bundle if tree-shaking fails | Build bundles over ~1MB |
| `motion.div` on every chat message with `initial={{ opacity: 0, y: 8 }}` | Nice entrance effect | Re-runs animation when messages array is rebuilt (on session switch) | On conversation load with 20+ history messages |

---

## Security Mistakes

Domain-specific security issues for this redesign.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing `sessionId` in URL params on new `/results/:id` route | Session hijacking if URL is shared | `sessionId` must stay in `localStorage` only — `/results/:id` should use an opaque result ID, not the chat session ID |
| Exposing affiliate link click tracking in the URL on tab navigation (e.g., appending UTM params on every route change) | Affiliate tracking abuse if URLs are scraped | `trackAffiliate` calls happen on click events, not on route changes — do not add route-level affiliate tracking |
| New `/profile` placeholder page rendered without checking it doesn't expose session data | Page leaks conversation metadata | Even placeholder pages must not render localStorage contents in the DOM |
| Adding `target="_blank"` to bottom tab bar links | Irrelevant risk, but opens new tab instead of navigating | Use `<Link href="...">` from Next.js — tab bar nav must use router, not `<a>` tags |

---

## UX Pitfalls

Common user experience mistakes specific to this redesign domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bottom tab bar on desktop (≥1024px) | Looks like a broken mobile app on wide screens | Hide tab bar with `lg:hidden`; desktop uses existing UnifiedTopbar |
| Active tab indicator not matching route for `/results/:id` | User doesn't know which tab is active after viewing results | `/results/:id` should highlight the Chat tab (it's a chat result) or none; define explicit route-to-tab mapping upfront |
| FAB ("Ask" center button) always navigating to new chat | Frustrates user mid-research if they accidentally tap it | FAB should be a "New Research" action with a 500ms hold-to-confirm on mobile, or show a confirmation chip |
| Follow-up chips clipped by bottom tab bar | User can't tap the last chip | Chat input and chip row need `padding-bottom` equal to tab bar height + safe area |
| Horizontal scroll carousels with no scroll indicator on mobile | User doesn't know they can scroll | Use scroll-snap with visible dots (already in ProductCarousel) or a fade-out gradient on the right edge |
| Replacing the current desktop sidebar with a bottom tab bar everywhere | Desktop users lose the category sidebar navigation | The sidebar must remain on desktop — bottom tab bar is mobile-only |
| Framer Motion page transition animations between tabs | Feels app-like in demos | On low-end devices, transitions cause perceived lag — make them opt-in via `prefers-reduced-motion` |

---

## "Looks Done But Isn't" Checklist

Things that appear complete in browser DevTools but fail on real devices or at build time.

- [ ] **Bottom tab bar:** Verify on real iPhone (not DevTools emulation) that the keyboard doesn't overlap the chat input and the home indicator safe area is respected.
- [ ] **Horizontal carousels:** Verify swipe works on iOS Safari — DevTools touch emulation does not test scroll containment accurately.
- [ ] **Dark mode:** Verify new tab bar and navigation components respond to theme toggle using `data-theme="dark"`, not `.dark` class.
- [ ] **New routes deployed to Vercel:** Check that `/saved`, `/compare`, `/profile` do not 404 on Vercel (dynamic routes have known deploy issues).
- [ ] **Stream not killed on tab switch:** With the AI responding, tap Discover tab, then tap Chat tab — the stream must either still be running or show a graceful "response was interrupted" state.
- [ ] **Last message not hidden:** After a long AI response, scroll to bottom — verify the last paragraph is not obscured by the tab bar.
- [ ] **Suggestion chips:** Tap a follow-up chip from the chat response — verify it submits correctly even when the page has been scrolled down.
- [ ] **`next build` passes cleanly:** Run `npm run build` and verify no hydration warnings or "deopted to CSR" messages for new routes.
- [ ] **Browse → Chat URL-param flow still works:** Type a query on the Discover screen, press send — it must navigate to `/chat?q=...&new=1` and auto-submit.
- [ ] **ProductCarousel bottom disclosure text:** The affiliate disclosure line must not be clipped by the tab bar on mobile.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| iOS keyboard overlap after tab bar ships | MEDIUM | Add `h-dvh` and `pb-[calc(64px+env(safe-area-inset-bottom))]` to affected containers; 1-2 hour fix |
| Hydration mismatch on tab bar | LOW | Wrap tab bar in `dynamic(() => import('./BottomTabBar'), { ssr: false })` as emergency fallback |
| SSE stream killed on navigation | HIGH | Requires routing architecture change — either parallel routes or persistent layout; plan for this, don't improvise |
| `dark:` utilities not working | LOW | Add `darkMode: ['selector', '[data-theme="dark"]']` to `tailwind.config.ts`; test all existing components for regressions |
| New route 404 on Vercel | LOW | Verify `app/route-name/page.tsx` file exists and is not a dynamic segment missing `generateStaticParams` |
| `sendSuggestion` event misfires | LOW | Change dispatch sites to URL-param navigation; 30-minute fix per location |
| Double scrollbar / last message hidden | LOW | Add `padding-bottom: 64px` to message scroll container; 15-minute fix |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| iOS keyboard buries chat input (Pitfall 1) | Navigation Shell | Test on real iOS device with keyboard open in chat |
| Hydration mismatch on bottom tab bar (Pitfall 2) | Navigation Shell | `next build && next start` — check console for hydration errors |
| SSE stream killed on tab navigation (Pitfall 3) | Routing Unification | Manually test: stream mid-response, switch tabs, switch back |
| Horizontal carousel scroll broken by overflow:hidden (Pitfall 4) | Product Cards Redesign | Swipe test on iOS Safari; re-test after split-panel layout |
| sendSuggestion CustomEvent fires with no listener (Pitfall 5) | Discover Screen Unification | Click each chip type on each route; verify message is sent |
| useSearchParams without Suspense causes CSR bailout (Pitfall 6) | New Routes Scaffolding | `next build` — verify new routes show "(Static)" in build output |
| Tailwind dark: utilities are inert (Pitfall 7) | Navigation Shell | Toggle theme with new tab bar visible; verify dark colors activate |
| h-screen layout hides content behind tab bar (Pitfall 8) | Navigation Shell | Scroll to end of long chat response with tab bar visible; verify no clipping |

---

## Sources

- Next.js official docs: [Text content does not match server-rendered HTML](https://nextjs.org/docs/messages/react-hydration-error)
- Next.js official docs: [Missing Suspense boundary with useSearchParams](https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout)
- Next.js official docs: [useSearchParams function reference](https://nextjs.org/docs/app/api-reference/functions/use-search-params)
- Vercel AI SDK issue: [Stream resumption doesn't work when users switch tabs](https://github.com/vercel/ai/issues/11865)
- iOS bottom tab bar safe areas: [Using Bottom Tab Bars on Safari iOS 15 — Samuel Kraft](https://samuelkraft.com/blog/safari-15-bottom-tab-bars-web)
- iOS keyboard overlap fix: [Fix mobile keyboard overlap with VisualViewport — DEV](https://dev.to/franciscomoretti/fix-mobile-keyboard-overlap-with-visualviewport-3a4a)
- CSS viewport units reference: [Understanding Mobile Viewport Units: svh, lvh, dvh — Medium](https://medium.com/@tharunbalaji110/understanding-mobile-viewport-units-a-complete-guide-to-svh-lvh-and-dvh-0c905d96e21a)
- Scroll chaining and overscroll: [Prevent Scroll Chaining With Overscroll Behavior — Shadeed](https://ishadeed.com/article/prevent-scroll-chaining-overscroll-behavior/)
- Tailwind dark mode selector strategy: [Mastering Custom Dark Mode with Tailwind CSS — Medium](https://medium.com/@asyncme/mastering-custom-dark-mode-with-tailwind-css-from-class-to-selector-strategy-1d0e7d8888f3)
- Framer Motion mobile optimization: [To optimize Framer Motion animations for mobile devices — studyraid](https://app.studyraid.com/en/read/7850/206068/optimizing-animations-for-mobile-devices)
- Project codebase: `frontend/app/chat/page.tsx`, `frontend/components/ChatContainer.tsx`, `frontend/components/ProductCarousel.tsx`, `frontend/components/UnifiedTopbar.tsx`, `frontend/app/layout.tsx`, `frontend/app/globals.css`, `frontend/tailwind.config.ts`
- Project memory: CLAUDE.md, MEMORY.md (known SSR pitfalls, deployment lessons)

---
*Pitfalls research for: Next.js 14 mobile-first frontend redesign (ReviewGuide.ai v2.0)*
*Researched: 2026-03-16*
