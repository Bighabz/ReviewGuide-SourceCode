# Phase 12: Navigation Shell - Research

**Researched:** 2026-03-16
**Domain:** Next.js 14 App Router layout composition, Framer Motion page transitions, iOS safe area, mobile bottom tab bar with FAB
**Confidence:** HIGH (stack already installed; verified patterns from official sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Mobile tab bar + FAB**
- 5 tabs: Discover, Saved, Ask (central FAB), Compare, Profile
- Central FAB is a raised 48px circular button (#1B4DFF, white "+" icon) that navigates to `/chat?new=1` — always starts a fresh research session
- Tab bar hides when on-screen keyboard opens — slides down, slides back up when keyboard dismissed (150ms slide animation)
- Lucide icons for all tabs: Home, Bookmark, Plus, LayoutGrid (or BarChart3), User — consistent with existing icon library
- Active tab: blue icon (#1B4DFF) + blue label. Inactive: #9B9B9B icon and label
- Tab bar height: 64px, white background, top border 1px solid #E8E6E1
- Label text: DM Sans Medium 10px
- Long-press on Profile tab opens a small popover with theme toggle + accent picker (interim solution until Profile page in Phase 16)

**Mobile header**
- Slim header on mobile: logo (left) + user avatar (right) — no search, no nav links, no theme toggle
- Footer is hidden on mobile — legal links will eventually move to Profile page
- Chat screen additionally gets a contextual back-arrow header (<- to Discover) with conversation title — sets up the shell for Phase 14's full ChatHeader with status line

**Desktop navigation**
- UnifiedTopbar nav links updated to match new tab labels: Discover, Saved, Ask, Compare, Profile
- Discover links to `/browse` until Phase 13 replaces it; Saved -> placeholder; Compare -> placeholder; Profile -> placeholder
- Placeholder routes not created in Phase 12 — links point to `/browse` or existing routes as fallback
- Footer remains on desktop as-is (3-column layout with legal links, affiliate disclosure, copyright)

**Page transitions**
- Tab switching: 150ms crossfade (opacity transition via Framer Motion AnimatePresence)
- Forward navigation (Discover -> Chat via search, opening results): 200ms slide-in from right
- Back navigation: 200ms slide-out to right
- Tab bar show/hide: 150ms slide down/up animation
- All transitions use Framer Motion (already installed)

**Layout architecture**
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | User sees bottom tab bar with 5 tabs (Discover, Saved, Ask, Compare, Profile) on mobile (<768px) | Bottom tab bar with Tailwind responsive hiding (md:hidden), fixed positioning, safe area CSS |
| NAV-02 | User sees desktop top navigation bar with logo and nav links on screens >=1024px | NavLayout conditionally renders UnifiedTopbar on lg:, tab bar hidden on lg:; existing UnifiedTopbar adapted |
| NAV-03 | User can tap central FAB button to start a new research chat from any screen | FAB button with router.push('/chat?new=1') in NavLayout, always rendered over tab bar |
| NAV-04 | User sees animated page transitions between routes | template.tsx approach with Framer Motion motion.div (entry-only) OR FrozenRouter for exit animations — see Architecture section |
| NAV-05 | Bottom tab bar handles iOS safe area insets correctly | viewport-fit=cover in viewport meta, env(safe-area-inset-bottom) in tab bar padding, pb-[calc(64px+env(safe-area-inset-bottom))] on content |
</phase_requirements>

---

## Summary

Phase 12 builds a navigation shell that wraps all app routes. The core deliverable is a `NavLayout` client component inserted into `layout.tsx` that conditionally renders the appropriate navigation chrome based on device width and current route. On mobile it shows a slim header plus fixed bottom tab bar with raised FAB; on desktop it shows the existing `UnifiedTopbar` with updated nav labels.

The project already has all required libraries: Framer Motion 12 (`framer-motion: ^12.26.2`), `lucide-react`, `next/navigation` hooks. No new packages need to be installed. The existing CSS variable system (`var(--*)` with `data-theme`) and `globals.css` foundations are in place.

The main technical complexity points are: (1) page transitions in Next.js 14 App Router have a known limitation with exit animations via AnimatePresence — the `template.tsx` entry-animation approach is the pragmatic production choice; (2) iOS safe area requires `viewport-fit=cover` to be added to the viewport meta in `layout.tsx`; (3) keyboard hide/show detection should use the `visualViewport` API resize event (cross-browser) over window resize.

**Primary recommendation:** Build `NavLayout` as a client component using `usePathname()` for route exclusion logic. Use `template.tsx` for page transitions (entry-only, no exit jank). Use `env(safe-area-inset-bottom)` with `viewport-fit=cover` for iOS safe areas. Detect keyboard open/close via `window.visualViewport` resize event.

---

## Standard Stack

### Core (All Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | ^14.2.35 | App Router, layout.tsx, template.tsx, usePathname | Project foundation |
| framer-motion | ^12.26.2 | motion.div, AnimatePresence for transitions | Already installed, used in UnifiedTopbar |
| lucide-react | ^0.294.0 | Home, Bookmark, Plus, LayoutGrid, User icons | Already installed, consistent icon library |
| next/navigation | (built-in) | usePathname, useRouter for route detection | Next.js built-in |
| tailwind-merge | ^3.4.0 | cn() for conditional class merging | Already installed via lib/utils.ts |

### No New Packages Required
The full required stack is already installed. Do NOT add:
- react-navigation (React Native only)
- @mui/material BottomNavigation (adds 50KB+ for one component)
- Any "use-long-press" npm package (implement with useRef/setTimeout natively — 10 lines)

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| template.tsx (entry-only transitions) | FrozenRouter + AnimatePresence | FrozenRouter enables exit animations but introduces "multiple renderers" warning and complex back/forward edge cases — not worth it for 150-200ms transitions |
| visualViewport resize | window resize event | window resize is unreliable on iOS Safari for keyboard events; visualViewport is the correct API |
| visualViewport resize | VirtualKeyboard API | VirtualKeyboard API is Chromium-only as of 2025; not supported on iOS Safari |

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Add viewport-fit=cover; insert NavLayout
│   ├── template.tsx            # NEW: Framer Motion entry animation wrapper
│   └── [routes as-is]
├── components/
│   ├── NavLayout.tsx           # NEW: Core layout shell component
│   ├── MobileTabBar.tsx        # NEW: Fixed bottom tab bar + FAB
│   ├── MobileHeader.tsx        # NEW: Slim mobile-only header
│   └── UnifiedTopbar.tsx       # MODIFIED: updated nav labels (Discover/Saved/Ask/Compare/Profile)
```

### Pattern 1: NavLayout — Conditional Navigation Shell

**What:** A `'use client'` component that wraps `{children}` and renders the correct navigation chrome based on viewport and pathname. Replaces the current Footer placement in `layout.tsx`.

**When to use:** Every non-excluded route. Excluded: `/admin/*`, `/privacy`, `/terms`, `/affiliate-disclosure`, `/login`.

```typescript
// frontend/components/NavLayout.tsx
'use client'

import { usePathname } from 'next/navigation'
import UnifiedTopbar from './UnifiedTopbar'
import MobileHeader from './MobileHeader'
import MobileTabBar from './MobileTabBar'
import Footer from './Footer'
import { cn } from '@/lib/utils'

const EXCLUDED_PREFIXES = ['/admin', '/privacy', '/terms', '/affiliate-disclosure', '/login']

interface NavLayoutProps {
  children: React.ReactNode
}

export default function NavLayout({ children }: NavLayoutProps) {
  const pathname = usePathname()
  const isExcluded = EXCLUDED_PREFIXES.some(prefix => pathname?.startsWith(prefix))

  if (isExcluded) {
    // Excluded routes: render children with no layout chrome
    // Each excluded route manages its own topbar (or none)
    return <>{children}</>
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Desktop: existing unified topbar (hidden on mobile) */}
      <div className="hidden md:block">
        <UnifiedTopbar />
      </div>

      {/* Mobile: slim header (logo + avatar only) */}
      <div className="block md:hidden">
        <MobileHeader />
      </div>

      {/* Content area — padded bottom on mobile for tab bar */}
      <main className={cn(
        'flex-1',
        // Mobile: add padding for 64px tab bar + safe area
        'pb-[calc(64px+env(safe-area-inset-bottom))] md:pb-0'
      )}>
        {children}
      </main>

      {/* Desktop footer (hidden on mobile) */}
      <div className="hidden md:block">
        <Footer />
      </div>

      {/* Mobile bottom tab bar + FAB (hidden on desktop) */}
      <div className="block md:hidden">
        <MobileTabBar />
      </div>
    </div>
  )
}
```

### Pattern 2: MobileTabBar with Raised FAB

**What:** Fixed bottom bar with 5 tabs. Center FAB raised 8px above bar using negative translateY. Keyboard-aware: hides when keyboard opens.

```typescript
// frontend/components/MobileTabBar.tsx
'use client'

import { useState, useEffect, useCallback } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Home, Bookmark, Plus, LayoutGrid, User } from 'lucide-react'
import { cn } from '@/lib/utils'

const TABS = [
  { id: 'discover', label: 'Discover', icon: Home, href: '/browse' },
  { id: 'saved',    label: 'Saved',    icon: Bookmark, href: '/browse' }, // fallback Phase 12
  { id: 'ask',      label: 'Ask',      icon: Plus,     href: null },      // FAB — special
  { id: 'compare',  label: 'Compare',  icon: LayoutGrid, href: '/browse' }, // fallback Phase 12
  { id: 'profile',  label: 'Profile',  icon: User,     href: null },      // long-press popover
] as const

export default function MobileTabBar() {
  const pathname = usePathname()
  const router = useRouter()
  const [keyboardOpen, setKeyboardOpen] = useState(false)
  const [showProfilePopover, setShowProfilePopover] = useState(false)

  // Keyboard detection via visualViewport API
  useEffect(() => {
    const vv = window.visualViewport
    if (!vv) return

    const handleResize = () => {
      // When keyboard opens, visual viewport height shrinks significantly
      const keyboardThreshold = window.innerHeight * 0.75
      setKeyboardOpen(vv.height < keyboardThreshold)
    }

    vv.addEventListener('resize', handleResize)
    return () => vv.removeEventListener('resize', handleResize)
  }, [])

  // Long-press for Profile tab (10-line native implementation)
  const longPressTimer = useCallback(() => {
    let timer: ReturnType<typeof setTimeout>
    return {
      start: () => { timer = setTimeout(() => setShowProfilePopover(true), 500) },
      cancel: () => clearTimeout(timer),
    }
  }, [])

  return (
    <AnimatePresence>
      {!keyboardOpen && (
        <motion.nav
          initial={{ y: 0 }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ duration: 0.15, ease: 'easeInOut' }}
          className="fixed bottom-0 left-0 right-0 z-[200]"
          style={{
            // Tab bar background fills up to and including safe area
            paddingBottom: 'env(safe-area-inset-bottom)',
            background: 'var(--surface-elevated)',
            borderTop: '1px solid #E8E6E1',
          }}
        >
          <div className="flex items-center justify-around h-16 px-2">
            {TABS.map((tab) => {
              if (tab.id === 'ask') {
                // Central FAB — raised above tab bar
                return (
                  <button
                    key="ask"
                    onClick={() => router.push('/chat?new=1')}
                    className="relative flex items-center justify-center w-12 h-12 rounded-full bg-[var(--primary)] text-white shadow-lg active:scale-95 transition-transform"
                    style={{
                      transform: 'translateY(-8px)',
                      boxShadow: '0 4px 16px rgba(27,77,255,0.35)',
                    }}
                    aria-label="Start new research"
                  >
                    <Plus size={22} strokeWidth={2.5} />
                  </button>
                )
              }
              // Standard tab
              const isActive = tab.id === 'discover'
                ? pathname?.startsWith('/browse')
                : pathname?.startsWith(tab.href ?? '')
              const Icon = tab.icon

              return (
                <button
                  key={tab.id}
                  onClick={() => tab.href && router.push(tab.href)}
                  className="flex flex-col items-center gap-0.5 min-w-[56px] py-1"
                  aria-label={tab.label}
                >
                  <Icon
                    size={22}
                    strokeWidth={isActive ? 2 : 1.5}
                    color={isActive ? '#1B4DFF' : '#9B9B9B'}
                  />
                  <span
                    className="font-medium leading-none"
                    style={{
                      fontSize: '10px',
                      color: isActive ? '#1B4DFF' : '#9B9B9B',
                      fontFamily: 'var(--font-dm-sans, system-ui)',
                    }}
                  >
                    {tab.label}
                  </span>
                </button>
              )
            })}
          </div>
        </motion.nav>
      )}
    </AnimatePresence>
  )
}
```

### Pattern 3: template.tsx for Page Transitions

**What:** Next.js `template.tsx` file re-mounts on every route change, triggering Framer Motion entry animations. This is the production-safe approach — no exit animations, but no routing bugs either.

**When to use:** Place `template.tsx` in `app/` for global transitions.

```typescript
// frontend/app/template.tsx
'use client'

import { motion } from 'framer-motion'

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}
```

For directional slide transitions (forward nav), a slightly richer variant:

```typescript
// For slide-in from right (forward navigation context):
<motion.div
  initial={{ opacity: 0, x: 16 }}
  animate={{ opacity: 1, x: 0 }}
  transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
>
  {children}
</motion.div>
```

**Note on exit animations:** AnimatePresence + FrozenRouter CAN produce exit animations in Next.js App Router but introduces rendering warnings and fragile dependency on internal Next.js context (`LayoutRouterContext` from `next/dist/client/components/layout-router-context.shared-runtime`). This internal import can break on any minor Next.js upgrade. Given the short (150-200ms) transition durations in this phase, the template.tsx entry-only approach is the correct production choice.

### Pattern 4: viewport-fit=cover for iOS Safe Area

**What:** The `env(safe-area-inset-bottom)` CSS variable only works when `viewport-fit=cover` is set in the viewport meta tag. Without it, the value is always 0.

**Required change to `layout.tsx`:**

```typescript
// frontend/app/layout.tsx — viewport export
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: 'cover',   // ADD THIS — enables env(safe-area-inset-bottom)
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0e1a' }
  ],
}
```

### Pattern 5: Layout.tsx Integration

**What:** NavLayout replaces the current inline `div.flex-col + Footer` structure in `layout.tsx`.

```typescript
// frontend/app/layout.tsx (after modification)
import NavLayout from '@/components/NavLayout'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `...theme init...` }} />
      </head>
      <body className={`${dmSans.variable} ${instrumentSerif.variable} font-sans`} suppressHydrationWarning>
        <NavLayout>{children}</NavLayout>
      </body>
    </html>
  )
}
```

`NavLayout` is a client component, but `layout.tsx` itself remains a server component — this is valid because Server Components can render Client Components as children.

### Anti-Patterns to Avoid

- **Using `dark:` Tailwind utilities in new components:** The project uses `data-theme` attribute strategy, not Tailwind's `dark:` prefix. `dark:` utilities are completely inert with this setup. Use `var(--*)` CSS variables exclusively.
- **Using `h-screen` for full-height containers:** iOS keyboard shrinks the visual viewport but not the layout viewport; `h-screen` can cause content to be hidden behind the keyboard. Use `h-dvh` for full-height containers.
- **Using `window resize` to detect keyboard:** Unreliable on iOS Safari. Use `window.visualViewport.addEventListener('resize', ...)` instead.
- **Importing LayoutRouterContext from Next.js internals:** The FrozenRouter pattern depends on `next/dist/client/components/layout-router-context.shared-runtime`. This is not a public API and can break silently on Next.js patch upgrades.
- **Applying NavLayout inside each route's page.tsx:** It belongs in root `layout.tsx` only. Each page managing its own shell leads to nav flickering on route change.
- **Math.random() in NavLayout or MobileTabBar:** Any server-rendered component using Math.random() causes hydration mismatch. NavLayout is a client component (`'use client'`), so this is not an issue — but be explicit with the directive.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Icon set | Custom SVG icons | `lucide-react` (already installed) | Already used throughout; Home, Bookmark, Plus, LayoutGrid, User are exact icons needed |
| Class merging | Manual string concatenation | `cn()` from `lib/utils.ts` (tailwind-merge) | Already installed; handles Tailwind conflict resolution |
| Route navigation | Manual history.pushState | `useRouter().push()` from `next/navigation` | SSR-safe, integrates with Next.js prefetching |
| Long-press detection | npm package | 10-line `useRef` + `setTimeout` inline | Only used once (Profile tab); adding a package for this is overkill |
| Motion animation | CSS keyframes for tab bar | `motion.div` from framer-motion | Already installed; consistent with existing animation approach in UnifiedTopbar |

**Key insight:** All tooling is already installed. The entire phase is composition work — wiring existing pieces into a new layout shell. No new dependencies needed.

---

## Common Pitfalls

### Pitfall 1: Missing viewport-fit=cover Breaks iOS Safe Area
**What goes wrong:** `env(safe-area-inset-bottom)` returns `0` on all iOS devices.
**Why it happens:** The browser only exposes non-zero safe area insets when `viewport-fit=cover` is set. The current `layout.tsx` does not set this.
**How to avoid:** Add `viewportFit: 'cover'` to the `Viewport` export in `layout.tsx` before any safe-area CSS is written.
**Warning signs:** Tab bar overlaps iPhone home indicator on physical device; safe area padding appears to have no effect.

### Pitfall 2: h-screen on Chat Page (Existing Bug to Fix)
**What goes wrong:** `frontend/app/chat/page.tsx` line 131 uses `h-screen` instead of `h-dvh`. When keyboard opens on iOS, the chat container doesn't resize correctly.
**Why it happens:** `h-screen` = `100vh` = layout viewport height (doesn't shrink on keyboard open). `h-dvh` = dynamic viewport height (shrinks with keyboard).
**How to avoid:** Replace `h-screen` with `h-dvh` in chat page and anywhere else `h-screen` is used for full-height contexts.
**Warning signs:** Chat input disappears behind keyboard on iOS; content not scrollable.

### Pitfall 3: NavLayout Causes Hydration Mismatch if Not Marked 'use client'
**What goes wrong:** `usePathname()` cannot be called in Server Components; calling it without `'use client'` causes a runtime crash.
**Why it happens:** `usePathname` is a Client Component hook.
**How to avoid:** `NavLayout`, `MobileTabBar`, `MobileHeader` all need `'use client'` directive. `layout.tsx` itself remains server-side and just imports `NavLayout`.
**Warning signs:** Error: "usePathname only works in Client Components."

### Pitfall 4: Tab Bar Not Hiding on Keyboard Open (iOS)
**What goes wrong:** The fixed bottom tab bar sits on top of the keyboard, pushing content up and creating a double-height obstruction.
**Why it happens:** `visualViewport.resize` is not listened to, so the `keyboardOpen` state stays `false`.
**How to avoid:** Implement `visualViewport` listener in `useEffect` within `MobileTabBar`. Guard with `if (!window.visualViewport) return` for SSR safety.
**Warning signs:** Tab bar visible above keyboard when any text input is focused on mobile.

### Pitfall 5: Existing UnifiedTopbar Rendered Twice on Mobile
**What goes wrong:** After NavLayout is introduced, mobile shows both the old UnifiedTopbar (from individual page files like `chat/page.tsx` and `BrowseLayout.tsx`) AND the new MobileHeader from NavLayout.
**Why it happens:** `chat/page.tsx` and `BrowseLayout.tsx` both render `<UnifiedTopbar />` directly. NavLayout also renders navigation.
**How to avoid:** Remove `<UnifiedTopbar />` from `chat/page.tsx` and `BrowseLayout.tsx` after NavLayout is wired in. Migration order matters: wire NavLayout first, then strip per-page topbars.
**Warning signs:** Double navigation bars on mobile after NavLayout is added.

### Pitfall 6: Admin/Login Pages Get Tab Bar
**What goes wrong:** Admin and login pages show the bottom tab bar, breaking their standalone layout.
**Why it happens:** The `EXCLUDED_PREFIXES` check in NavLayout is missing or incorrect.
**How to avoid:** Check `EXCLUDED_PREFIXES = ['/admin', '/privacy', '/terms', '/affiliate-disclosure', '/login']` with `pathname?.startsWith(prefix)`.
**Warning signs:** Bottom tab bar visible on `/admin/...` routes.

---

## Code Examples

Verified patterns from the project's existing code + official sources:

### Keyboard Detection via visualViewport API
```typescript
// Source: MDN VisualViewport API https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
useEffect(() => {
  if (typeof window === 'undefined' || !window.visualViewport) return
  const vv = window.visualViewport

  const handleResize = () => {
    // Visual viewport shrinks by >25% when keyboard opens on most devices
    const keyboardThreshold = window.innerHeight * 0.75
    setKeyboardOpen(vv.height < keyboardThreshold)
  }

  vv.addEventListener('resize', handleResize)
  return () => vv.removeEventListener('resize', handleResize)
}, [])
```

### Safe Area CSS (Tailwind + env())
```css
/* Tab bar itself — background extends into safe area */
.tab-bar {
  padding-bottom: env(safe-area-inset-bottom);
}

/* Content area — pushed up so it's not behind tab bar + safe area */
.content-area {
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}
```

As Tailwind utility (used in NavLayout):
```
pb-[calc(64px+env(safe-area-inset-bottom))]
```

### Framer Motion Entry Transition (template.tsx)
```typescript
// Source: Next.js docs — template.js re-mounts on navigation
// https://nextjs.org/docs/app/api-reference/file-conventions/template
'use client'
import { motion } from 'framer-motion'

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}
```

### Long-Press Hook (inline, no package)
```typescript
// Inline implementation — no package needed for single use
function useLongPress(callback: () => void, delay = 500) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const start = useCallback(() => {
    timerRef.current = setTimeout(callback, delay)
  }, [callback, delay])

  const cancel = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
  }, [])

  return {
    onMouseDown: start,
    onMouseUp: cancel,
    onMouseLeave: cancel,
    onTouchStart: start,
    onTouchEnd: cancel,
  }
}
```

### Active Tab Detection
```typescript
// Source: existing pattern from UnifiedTopbar.tsx
const pathname = usePathname()

function getActiveTab(pathname: string | null) {
  if (!pathname) return 'discover'
  if (pathname.startsWith('/chat')) return 'ask'
  if (pathname.startsWith('/browse') || pathname === '/') return 'discover'
  return 'discover' // default
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `h-screen` | `h-dvh` | iOS 15.4 / CSS spec 2022 | Prevents keyboard overlap on iOS; must replace `h-screen` in chat/page.tsx |
| `window resize` for keyboard | `visualViewport.resize` | ~2020 (Safari 13+) | Reliable cross-browser keyboard detection |
| Framer Motion exit animations in Next.js App Router | template.tsx entry-only | Next.js 13+ App Router | Exit animations broken by design; template.tsx is the stable alternative |
| `viewport-fit=initial` (default) | `viewport-fit=cover` | iOS 11+ | Required to get non-zero safe area insets on notched/Dynamic Island devices |

**Deprecated/outdated in this project:**
- `h-screen` in `chat/page.tsx` (line 131, 217): Should be `h-dvh`
- `min-h-screen` in `BrowseLayout.tsx`, `login/page.tsx`: Lower priority but should be `min-h-dvh` eventually
- Per-page `<UnifiedTopbar />` renders: Move to NavLayout, remove from `chat/page.tsx` and `BrowseLayout.tsx`

---

## Open Questions

1. **SSE stream tab-switch behavior (from STATE.md)**
   - What we know: STATE.md flags "SSE stream-on-tab-switch architecture decision must be made in Phase 12 before Chat screen is modified"
   - What's unclear: If user navigates away from `/chat` mid-stream via tab bar, does the stream abort? Does NavLayout need to handle stream state at all?
   - Recommendation: For Phase 12, the tab bar simply calls `router.push()` — it does NOT need to know about streaming. The ChatContainer's existing SSE abort logic (`EventSource.close()`) will fire when the component unmounts. This decision is "implemented by default" via React unmount behavior. No special handling needed in Phase 12.

2. **Chat page's own topbar removal timing**
   - What we know: `chat/page.tsx` renders `<UnifiedTopbar />` directly; `BrowseLayout.tsx` also renders `<UnifiedTopbar />`
   - What's unclear: Whether Phase 12 should remove these in the same phase or leave them for Phase 13/14
   - Recommendation: Remove them in Phase 12 as part of the NavLayout migration. Removing them in a later phase risks double-topbar being shipped to production.

3. **ChatHeader contextual back-arrow for mobile**
   - What we know: CONTEXT.md specifies a contextual back-arrow header on the chat screen for mobile ("← to Discover with conversation title")
   - What's unclear: Whether this belongs in `MobileHeader` (conditional render on chat route) or in `ChatContainer` itself
   - Recommendation: Implement it in `MobileHeader` using `usePathname()` to detect `/chat` route and render the back-arrow variant. Phase 14 will extend it with the full status line — isolating it in MobileHeader makes that extension clean.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.0.17 + @testing-library/react 14 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npm run test:run -- --reporter=verbose tests/navigation.test.tsx` |
| Full suite command | `cd frontend && npm run test:run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | MobileTabBar renders 5 tabs on mobile viewport | unit | `npm run test:run -- tests/mobileTabBar.test.tsx` | Wave 0 |
| NAV-01 | Tab bar is hidden on desktop (md: class applied) | unit | `npm run test:run -- tests/mobileTabBar.test.tsx` | Wave 0 |
| NAV-02 | UnifiedTopbar renders on desktop; not on mobile | unit | `npm run test:run -- tests/navLayout.test.tsx` | Wave 0 |
| NAV-03 | FAB click calls router.push('/chat?new=1') | unit | `npm run test:run -- tests/mobileTabBar.test.tsx` | Wave 0 |
| NAV-04 | template.tsx renders motion.div with opacity animation | unit | `npm run test:run -- tests/pageTransition.test.tsx` | Wave 0 |
| NAV-05 | Tab bar paddingBottom includes env(safe-area-inset-bottom) | unit (style check) | `npm run test:run -- tests/mobileTabBar.test.tsx` | Wave 0 |
| NAV-05 | viewport Viewport export includes viewportFit: 'cover' | unit | `npm run test:run -- tests/layout.test.tsx` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npm run test:run -- tests/mobileTabBar.test.tsx tests/navLayout.test.tsx`
- **Per wave merge:** `cd frontend && npm run test:run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/navLayout.test.tsx` — covers NAV-01 (responsive hiding), NAV-02 (desktop topbar), excluded routes
- [ ] `frontend/tests/mobileTabBar.test.tsx` — covers NAV-01 (5 tabs), NAV-03 (FAB click), NAV-05 (safe area style)
- [ ] `frontend/tests/pageTransition.test.tsx` — covers NAV-04 (template.tsx motion.div)
- [ ] `frontend/tests/layout.test.tsx` — covers NAV-05 (viewport viewportFit: 'cover')

Note: Existing `tests/setup.ts` already mocks `usePathname`, `useRouter`, and `localStorage` — NavLayout tests can use it directly.

---

## Sources

### Primary (HIGH confidence)
- Next.js official docs — layout.tsx, template.tsx, Viewport export, usePathname
  https://nextjs.org/docs/app/api-reference/file-conventions/layout
  https://nextjs.org/docs/app/api-reference/file-conventions/template
  https://nextjs.org/docs/app/api-reference/functions/use-pathname
- MDN — env(safe-area-inset-bottom), VisualViewport API
  https://developer.mozilla.org/en-US/docs/Web/CSS/env
  https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- Project source — framer-motion ^12.26.2, lucide-react, next/navigation confirmed in `frontend/package.json`
- Project source — `data-theme` pattern, CSS variable system confirmed in `globals.css`
- Project source — existing Framer Motion usage in `UnifiedTopbar.tsx` (AnimatePresence, motion.div)

### Secondary (MEDIUM confidence)
- Samuel Kraft — iOS bottom tab bars with safe area (env() pattern, viewport-fit=cover requirement)
  https://samuelkraft.com/blog/safari-15-bottom-tab-bars-web
- Next.js GitHub Discussion #59349 — template.tsx vs AnimatePresence limitations confirmed
  https://github.com/vercel/next.js/discussions/59349
- imcorfitz.com — FrozenRouter pattern documented (assessed as too fragile for production)
  https://www.imcorfitz.com/posts/adding-framer-motion-page-transitions-to-next-js-app-router
- dev.to — template.tsx approach for page transitions in Next.js 14
  https://dev.to/abdur_rakibrony_97cea0e9/page-transition-in-nextjs-14-app-router-using-framer-motion-2he7

### Tertiary (LOW confidence)
- None — all critical claims verified against official docs or project source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed installed in `package.json`, versions exact
- Architecture: HIGH — NavLayout pattern verified against Next.js App Router conventions; route exclusion via usePathname verified as standard approach
- Safe area / iOS: HIGH — env() and viewport-fit=cover verified via MDN + Samuel Kraft article
- Page transitions: MEDIUM — template.tsx approach works; exit animations confirmed broken in App Router (Next.js GitHub discussion); Framer Motion 12 React API confirmed stable (no breaking changes)
- Keyboard detection: MEDIUM — visualViewport API confirmed as correct approach; specific threshold (75% of innerHeight) is an estimate that may need tuning on certain devices
- Pitfalls: HIGH — most discovered directly from codebase inspection (existing h-screen usage, double topbar risk)

**Research date:** 2026-03-16
**Valid until:** 2026-06-16 (Next.js 14 stable, Framer Motion 12 stable; view transitions experimental flag not relevant for this phase)
