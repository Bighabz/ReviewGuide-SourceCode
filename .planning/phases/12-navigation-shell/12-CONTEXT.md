# Phase 12: Navigation Shell - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

App-like navigation shell for all screens — mobile gets a fixed bottom tab bar with central FAB and a slim top header, desktop keeps the existing top nav (updated labels), and every new component uses the correct `h-dvh` / CSS variable / dark mode baseline. Animated page transitions between routes. iOS safe area handling. This phase establishes the layout context for all subsequent v2.0 phases (13-16).

</domain>

<decisions>
## Implementation Decisions

### Mobile tab bar + FAB
- 5 tabs: Discover, Saved, Ask (central FAB), Compare, Profile
- Central FAB is a raised 48px circular button (#1B4DFF, white "+" icon) that navigates to `/chat?new=1` — always starts a fresh research session
- Tab bar hides when on-screen keyboard opens — slides down, slides back up when keyboard dismissed (150ms slide animation)
- Lucide icons for all tabs: Home, Bookmark, Plus, LayoutGrid (or BarChart3), User — consistent with existing icon library
- Active tab: blue icon (#1B4DFF) + blue label. Inactive: #9B9B9B icon and label
- Tab bar height: 64px, white background, top border 1px solid #E8E6E1
- Label text: DM Sans Medium 10px
- Long-press on Profile tab opens a small popover with theme toggle + accent picker (interim solution until Profile page in Phase 16)

### Mobile header
- Slim header on mobile: logo (left) + user avatar (right) — no search, no nav links, no theme toggle
- Footer is hidden on mobile — legal links will eventually move to Profile page
- Chat screen additionally gets a contextual back-arrow header (← to Discover) with conversation title — sets up the shell for Phase 14's full ChatHeader with status line

### Desktop navigation
- UnifiedTopbar nav links updated to match new tab labels: Discover, Saved, Ask, Compare, Profile
- Discover links to `/browse` until Phase 13 replaces it; Saved → placeholder; Compare → placeholder; Profile → placeholder
- Placeholder routes not created in Phase 12 — links point to `/browse` or existing routes as fallback
- Footer remains on desktop as-is (3-column layout with legal links, affiliate disclosure, copyright)

### Page transitions
- Tab switching: 150ms crossfade (opacity transition via Framer Motion AnimatePresence)
- Forward navigation (Discover → Chat via search, opening results): 200ms slide-in from right
- Back navigation: 200ms slide-out to right
- Tab bar show/hide: 150ms slide down/up animation
- All transitions use Framer Motion (already installed)

### Layout architecture
- New `NavLayout` component wraps `{children}` inside root layout.tsx body
- Root layout.tsx keeps: fonts, html/body setup, meta tags
- NavLayout handles: mobile slim header, bottom tab bar, desktop UnifiedTopbar, footer visibility, safe area insets
- Admin pages (/admin/*) and legal pages (/privacy, /terms, /affiliate-disclosure) excluded from NavLayout — keep current layout (full topbar + footer, no tab bar)
- Content area gets `pb-[calc(64px+env(safe-area-inset-bottom))]` on mobile to prevent content hiding behind fixed tab bar

### Claude's Discretion
- Exact Framer Motion easing curves for transitions
- Tab bar shadow intensity and blur values
- FAB elevation/shadow treatment
- How to detect keyboard open/close (visualViewport API vs resize event)
- Route-detection logic for excluding admin/legal pages from NavLayout

</decisions>

<specifics>
## Specific Ideas

- Tab bar matches the Figma "ReviewGuide.ai — New UX Concept" bottom bar spec (5 tabs, raised center FAB)
- Mobile experience should feel like a native app — no browser-like header/footer clutter
- The slim mobile header (logo + avatar) provides brand presence without eating real estate
- Forward/back slide transitions give spatial orientation; tab crossfades avoid implying hierarchy between tabs

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `UnifiedTopbar.tsx`: Current top navigation — will be adapted for desktop (new labels) and replaced on mobile by slim header + tab bar
- `Footer.tsx`: 3-column footer — hidden on mobile, kept on desktop
- `framer-motion`: Already installed, used in UnifiedTopbar for animations (AnimatePresence, motion.div)
- `lucide-react`: Icon library already used throughout — Home, Bookmark, Plus, LayoutGrid, User icons available
- `cn()` from `frontend/lib/utils.ts`: Tailwind class merging utility
- CSS variables in `globals.css`: Full editorial luxury theme with light/dark modes, `data-theme` attribute strategy

### Established Patterns
- `data-theme` attribute for dark mode (not Tailwind `dark:` utilities) — all new components must use `var(--*)` exclusively
- `h-dvh` for full-height containers (not `h-screen`) — prevents iOS keyboard overlap
- `'use client'` directive on all interactive components
- Props interfaces defined inline above component functions
- `usePathname()` / `useRouter()` from `next/navigation` for route detection

### Integration Points
- `layout.tsx`: Root layout — NavLayout will be inserted as a child wrapping `{children}`
- `Footer` import in layout.tsx will move inside NavLayout (conditionally rendered)
- `ChatContainer.tsx`: Currently has its own internal header — Phase 12 adds a contextual back-arrow header on mobile, Phase 14 extends it
- Route structure: `/browse`, `/chat`, `/admin/*`, `/privacy`, `/terms`, `/affiliate-disclosure`, `/login`
- `window.dispatchEvent(new CustomEvent('sendSuggestion', ...))` pattern must not be broken by layout changes

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-navigation-shell*
*Context gathered: 2026-03-16*
