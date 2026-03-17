# Phase 13: Discover Screen - Research

**Researched:** 2026-03-17
**Domain:** Next.js 14 App Router / React 18 / Tailwind + CSS Variables / Client-side personalization
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Hero section**
- Drop the animated video logo — clean editorial hero only
- Headline: "What are you *researching* today?" — "researching" in serif italic (#1B4DFF via var(--primary))
- Subline: "Expert reviews, real data, zero fluff." — DM Sans Regular 14px, var(--text-secondary)
- Keep the same wording as existing browse page hero (already matches Figma spec)
- Search bar: left magnifying glass icon only, no decorative pen icon on right
- Search bar is a visual CTA, not an input field — tapping navigates to `/chat?new=1` with cursor focused in input. No typing happens on the Discover screen itself.
- Search bar height ~56px, 1px solid var(--border), 16px corner radius, subtle shadow

**Category chips**
- Horizontal scrollable row of pill-shaped chips, no wrap
- Show top 8 categories from `categoryConfig.ts`: Popular (hardcoded first), Tech, Travel, Kitchen, Fitness, Home, Fashion, Outdoor
- Chip height 36px, padding 12px 16px, corner radius 20px (pill shape)
- Active chip: `bg-[var(--text)]` + white text (DM Sans SemiBold 13px) — adapts to dark mode via CSS variables
- Inactive chips: transparent background, `border-[var(--border)]`, `text-[var(--text)]`
- Scrollbar hidden on mobile (`-webkit-scrollbar: none`)
- Tapping a chip navigates to `/chat?q=<first query from categoryConfig>&new=1` — starts a focused research session
- "For You" chip: appears as the first chip ONLY if `recentSearches` exist in localStorage. If no history, "Popular" is first chip instead. "For You" shows recently researched items inline below the chip row when active.

**Trending research cards**
- Hardcoded static array in a `trendingTopics.ts` file — editable by hand, replaceable with real data later
- 5-6 topics (e.g. "Best Headphones 2026", "Tokyo Travel Guide", "Top Laptops for Students")
- 3 cards visible without scrolling on mobile, vertical stack
- Each card: ~72px height, horizontal layout — left icon (40x40 circle with pastel bg + Lucide icon), center text, right chevron `>`
- Lucide icons with distinct pastel background colors per card (e.g. blue for Headphones, orange for Plane, green for Laptop)
- Title: DM Sans SemiBold 15px, var(--text)
- Subtitle: DM Sans Regular 13px, var(--text-secondary)
- Tapping a card navigates to `/chat?q=<topic query>&new=1`
- Section header: "TRENDING RESEARCH" in uppercase DM Sans Medium 11px, var(--text-muted), letter-spacing 1.5px — editorial label style
- Arrow `→` below cards hints at more topics
- Desktop: cards display in a 2-column or 3-column grid

**Route migration**
- `/` becomes the Discover screen directly (remove the `redirect('/browse')` from `page.tsx`)
- `/browse` root page is dropped — its content is replaced by the Discover screen at `/`
- `/browse/[category]` dynamic pages remain — CategorySidebar stays on desktop for category detail pages only
- BrowseLayout is used only by `/browse/[category]` pages (not the Discover screen)
- UnifiedTopbar "Discover" link updated to point to `/` (not `/browse`)
- MobileTabBar "Discover" tab updated to point to `/`

### Claude's Discretion
- Exact trending topic content (titles, subtitles, icons, colors)
- Number of trending topics (5 or 6)
- "For You" section layout when chip is active (inline cards below chip row)
- Desktop layout grid columns for trending cards
- Search bar shadow and focus ring treatment
- Exact spacing between hero, chips, and trending sections

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DISC-01 | User sees editorial hero headline with serif italic accent and search bar on `/` | Requires converting `app/page.tsx` from redirect to a full 'use client' component; hero pattern already exists in `browse/page.tsx` |
| DISC-02 | User can scroll horizontal category chips (Popular, Tech, Travel, Kitchen, Fitness, etc.) | `categoryConfig.ts` provides slug/name/queries; chip scroll pattern is new to this codebase — overflow-x-auto with scrollbar-hidden |
| DISC-03 | User sees trending research cards with icons, titles, subtitles — tapping navigates to chat | New `trendingTopics.ts` static data file; Lucide icons + pastel backgrounds pattern; `useRouter().push()` for navigation |
| DISC-04 | User sees personalized "For You" chip based on recent search history | `recentSearches.ts` + `getRecentSearches()` already handle localStorage safely — SSR guard required (`useEffect` + `useState`) |
| DISC-05 | Search bar tap navigates to chat screen with input focused | New `DiscoverSearchBar` component that is `<div role="button">` (not `<input>`) — click calls `router.push('/chat?new=1')` |
</phase_requirements>

---

## Summary

Phase 13 replaces the current split Browse/Chat entry point with a single editorial Discover screen at `/`. All the building blocks exist in the codebase: the hero copy and CSS variable system come from `browse/page.tsx`, category data comes from `categoryConfig.ts`, personalization state comes from `recentSearches.ts`, and the navigation shell (NavLayout, MobileTabBar, UnifiedTopbar) was completed in Phase 12.

The primary engineering work is: (1) transform `app/page.tsx` from a single-line redirect into a full client component, (2) build three UI sub-components (hero search bar, category chip row, trending card list), and (3) create one new data file (`trendingTopics.ts`). The route migration (removing `/browse` root, updating topbar/tabbar hrefs) is mechanical and low-risk.

The only non-trivial interaction is the "For You" chip: `localStorage` is unavailable during SSR, so the component must guard with `useEffect` + `useState` (the same pattern already used in `browse/page.tsx` line 15-17). This is well-understood and follows existing project patterns.

**Primary recommendation:** Build the Discover screen as a single `'use client'` component in `app/page.tsx`, extracting three focused sub-components: `DiscoverSearchBar`, `CategoryChipRow`, and `TrendingCards`. Create `lib/trendingTopics.ts` as the static data source. Update topbar and tabbar hrefs last to avoid breaking the active-tab detection.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js App Router | ^14.2.35 | `app/page.tsx` becomes the Discover screen; `app/browse/page.tsx` is dropped | Already in use; App Router file-based routing |
| React 18 | ^18.2.0 | `'use client'` component with hooks for localStorage state | Already in use |
| Tailwind CSS | ^3.3.6 | Layout, spacing, responsive breakpoints | Already in use |
| CSS Variables (`var(--)`) | n/a | All color/theme values | Project-wide requirement — NO `dark:` utilities |
| lucide-react | ^0.294.0 | Icons for trending cards (Headphones, Plane, Laptop, etc.) and search magnifier | Already in use throughout |
| framer-motion | ^12.26.2 | Optional subtle card hover animation (same `product-card-hover` pattern) | Already in use |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `next/navigation` `useRouter` | ^14.2.35 | Programmatic navigation on chip/card/searchbar tap | All tap-to-navigate interactions |
| `cn()` from `lib/utils.ts` | local | Conditional Tailwind class merging | Active/inactive chip state |
| `clsx` / `tailwind-merge` | ^2.1.1 / ^3.4.0 | Used inside `cn()` | Indirect — through `cn()` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Static `trendingTopics.ts` array | API-fetched trending data | Static is correct here — locked decision; no backend changes this phase |
| `useRouter().push()` for search bar tap | `<Link href="/chat?new=1">` | Link is fine too, but `useRouter` is the established pattern for programmatic navigation in this codebase |
| CSS `overflow-x: auto` chip scroll | `embla-carousel` or similar | Scroll libraries are overkill; native overflow-x scroll is sufficient and simpler |

**Installation:** No new packages required. All libraries already present.

---

## Architecture Patterns

### Recommended Project Structure

New files this phase creates:
```
frontend/
├── app/
│   └── page.tsx                    # REPLACE: redirect → DiscoverScreen component
├── lib/
│   └── trendingTopics.ts           # NEW: static trending topic data
├── components/
│   └── discover/
│       ├── DiscoverSearchBar.tsx   # NEW: tap-to-navigate visual search bar
│       ├── CategoryChipRow.tsx     # NEW: horizontal chip row with "For You" logic
│       └── TrendingCards.tsx       # NEW: trending topic card list/grid
```

Modified files:
```
frontend/
├── components/
│   ├── UnifiedTopbar.tsx           # MODIFY: "Discover" link href /browse → /
│   └── MobileTabBar.tsx            # MODIFY: "Discover" tab href /browse → /
├── app/
│   └── browse/
│       └── page.tsx                # REMOVE or leave as redirect to /
```

### Pattern 1: Page Component as Orchestrator

`app/page.tsx` becomes a thin orchestrator — `'use client'` directive, reads localStorage once via `useEffect`, passes data down to sub-components. No logic lives in `page.tsx` itself.

```typescript
// app/page.tsx
'use client'

import { useState, useEffect } from 'react'
import { getRecentSearches } from '@/lib/recentSearches'
import DiscoverSearchBar from '@/components/discover/DiscoverSearchBar'
import CategoryChipRow from '@/components/discover/CategoryChipRow'
import TrendingCards from '@/components/discover/TrendingCards'

export default function DiscoverPage() {
  const [hasHistory, setHasHistory] = useState(false)

  useEffect(() => {
    setHasHistory(getRecentSearches().length > 0)
  }, [])

  return (
    <div className="flex flex-col pb-20">
      <DiscoverSearchBar />
      <CategoryChipRow hasHistory={hasHistory} />
      <TrendingCards />
    </div>
  )
}
```

### Pattern 2: Visual CTA Search Bar (not an input)

The search bar is a `<div role="button">` or `<button>` styled to look like an input. It does NOT accept typing. Clicking it navigates to `/chat?new=1`.

```typescript
// components/discover/DiscoverSearchBar.tsx
'use client'

import { Search } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function DiscoverSearchBar() {
  const router = useRouter()

  return (
    <button
      onClick={() => router.push('/chat?new=1')}
      aria-label="Start a research session"
      className="w-full flex items-center gap-3 px-4 bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text-muted)] text-left rounded-2xl cursor-pointer hover:border-[var(--primary)]/40 transition-all"
      style={{ height: '56px', borderRadius: '16px', boxShadow: 'var(--shadow-sm)' }}
    >
      <Search size={18} className="text-[var(--text-muted)] shrink-0" />
      <span className="text-sm">Ask anything — best headphones, Tokyo trip, laptop deals...</span>
    </button>
  )
}
```

### Pattern 3: Horizontal Chip Row with Scrollbar Hidden

```typescript
// Key CSS pattern for hidden scrollbar on the chip row
// Apply via style or a custom CSS class
<div
  className="flex gap-2 overflow-x-auto py-1"
  style={{ scrollbarWidth: 'none' }}  // Firefox
>
  {/* On mobile, add: -webkit-scrollbar: none via globals.css utility class */}
```

The scrollbar-hidden utility can be added to `globals.css` as a reusable layer:
```css
/* In globals.css @layer utilities */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
```

### Pattern 4: "For You" Chip Guard (SSR Safety)

localStorage is not available during server-side rendering. The guard pattern matches what `browse/page.tsx` already uses:

```typescript
// CORRECT: guarded with useEffect
const [hasHistory, setHasHistory] = useState(false)
useEffect(() => {
  setHasHistory(getRecentSearches().length > 0)
}, [])

// WRONG: would cause hydration error
const hasHistory = getRecentSearches().length > 0  // crashes on server
```

Since `app/page.tsx` must be `'use client'` anyway (it needs `useRouter`), this is natural.

### Pattern 5: Trending Topic Data Shape

```typescript
// lib/trendingTopics.ts
export interface TrendingTopic {
  id: string
  title: string
  subtitle: string
  query: string        // the query sent to /chat?q=
  icon: string         // Lucide icon name (e.g. 'Headphones', 'Plane')
  iconBg: string       // pastel bg color (e.g. '#EFF6FF', '#FFF7ED')
  iconColor: string    // icon stroke color (e.g. '#3B82F6', '#F97316')
}

export const trendingTopics: TrendingTopic[] = [
  {
    id: 'headphones-2026',
    title: 'Best Headphones 2026',
    subtitle: 'Noise-cancelling picks at every price',
    query: 'Best noise-cancelling headphones',
    icon: 'Headphones',
    iconBg: '#EFF6FF',
    iconColor: '#3B82F6',
  },
  // ... 4-5 more
]
```

### Pattern 6: Category Chip Mapping

The CONTEXT.md specifies 8 chips: Popular (hardcoded first, no slug), then Tech, Travel, Kitchen, Fitness, Home, Fashion, Outdoor. These map to `categoryConfig.ts` slugs:

| Chip Label | categoryConfig slug | queries[0] used for navigation |
|------------|--------------------|---------------------------------|
| Popular | (hardcoded — navigates to `/chat?new=1`) | n/a |
| Tech | `electronics` | "Best noise-cancelling headphones" |
| Travel | `travel` | "Top all-inclusive resorts in the Caribbean" |
| Kitchen | `home-appliances` | "Best robot vacuums for pet hair" |
| Fitness | `outdoor-fitness` | "Best hiking boots for beginners" |
| Home | `smart-home` | "Best Alexa-compatible smart home gadgets" |
| Fashion | `fashion-style` | "Best white sneakers for everyday wear" |
| Outdoor | `outdoor-fitness` | "Best hiking boots for beginners" |

Note: `categoryConfig.ts` uses "Health & Wellness", "Kids & Toys", "Baby", "Big & Tall" for the remaining categories — these are not in the 8-chip set. The planner should build a chip config array rather than iterating `categories` directly, since the display names differ from `category.name`.

### Anti-Patterns to Avoid

- **Using `<textarea>` or `<input>` in DiscoverSearchBar:** The search bar must NOT accept typing. Use `<button>` styled as an input.
- **Calling `getRecentSearches()` at module level:** Crashes on SSR. Always inside `useEffect`.
- **Using Tailwind `dark:` utilities:** Inert with this project's `data-theme` strategy. Use `var(--)` CSS variables only.
- **Adding a topbar or header inside `app/page.tsx`:** NavLayout (from layout.tsx) already provides the header — adding another creates double navigation bars.
- **Using `Math.random()` for card ordering or icon colors:** Causes hydration errors. Use deterministic values from `trendingTopics.ts` data.
- **Leaving `redirect('/browse')` in page.tsx:** Must be removed completely — it runs on the server and will short-circuit the entire component.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| localStorage safe reads | Custom try/catch wrapper | `getRecentSearches()` from `lib/recentSearches.ts` | Already handles SSR, parse errors, type validation |
| Icon rendering | Custom SVG icons | `lucide-react` (already installed, v0.294.0) | Headphones, Plane, Laptop2, Dumbbell etc. are all available |
| CSS class merging | String concatenation | `cn()` from `lib/utils.ts` | Handles conditional classes and Tailwind deduplication |
| Programmatic navigation | `window.location.href =` | `useRouter().push()` from `next/navigation` | Works with Next.js App Router history and transitions |
| Category data | New hardcoded array | Import from `lib/categoryConfig.ts` | Already has slug, name, queries — chip row reads from it |

---

## Common Pitfalls

### Pitfall 1: SSR Crash from localStorage in "For You" Chip
**What goes wrong:** Calling `getRecentSearches()` outside of `useEffect` crashes on the server with "localStorage is not defined."
**Why it happens:** Next.js App Router can server-render client components on first load. `localStorage` does not exist in the Node.js runtime.
**How to avoid:** Initialize state as `false` (no history assumed), then read localStorage inside `useEffect` on mount. The existing `browse/page.tsx` has this exact pattern at lines 15-17.
**Warning signs:** Hydration errors in dev console, "ReferenceError: localStorage is not defined" in server logs.

### Pitfall 2: Active-Tab Detection Breaks for `/`
**What goes wrong:** After route migration, both MobileTabBar and UnifiedTopbar already handle `pathname === '/'` as the Discover tab. But the logo link in UnifiedTopbar (line 124) still points to `/browse`. If a user clicks the logo, they land on the now-removed `/browse` page.
**Why it happens:** The logo href and the "Discover" nav link href are separate strings — updating one and not the other breaks discovery navigation.
**How to avoid:** Update both `href="/browse"` occurrences that relate to Discover in UnifiedTopbar: the logo `<Link>` and the Discover nav link.
**Warning signs:** Logo click goes to an empty/broken page.

### Pitfall 3: `app/browse/page.tsx` Still Exists After Migration
**What goes wrong:** If `/browse` root page is left as-is, users typing `/browse` directly see the old hero + category cards, which contradicts the Discover screen being at `/`. This also means there are two places rendering similar hero content.
**Why it happens:** Route migration requires explicitly removing or redirecting the old page.
**How to avoid:** Either delete `app/browse/page.tsx` entirely, or replace its content with `redirect('/')` to keep URLs clean.
**Warning signs:** Navigating directly to `/browse` shows old content.

### Pitfall 4: Category Chip Label Mismatch
**What goes wrong:** `categoryConfig.ts` uses different names than the chip labels. "Electronics" in config vs "Tech" on the chip, "Home Appliances" vs "Kitchen", "Outdoor & Fitness" vs both "Fitness" and "Outdoor."
**Why it happens:** The chip labels are editorial shorthand; the config names are descriptive.
**How to avoid:** Build a standalone chip config array in the `CategoryChipRow` component or `trendingTopics.ts`-adjacent file that maps chip label → category slug → query. Do NOT iterate `categories` array directly for chip rendering.
**Warning signs:** Chip labels showing "Electronics" or "Home Appliances" instead of "Tech" or "Kitchen."

### Pitfall 5: Framer Motion `product-card-hover` on Server-Only Import
**What goes wrong:** If `TrendingCards.tsx` uses the `product-card-hover` CSS class but the component is not marked `'use client'`, Framer Motion animations won't trigger.
**Why it happens:** Framer Motion's interactive hooks require a browser DOM.
**How to avoid:** All interactive components that handle click events must include `'use client'` directive at the top.

### Pitfall 6: BrowseLayout Sidebar Appearing on Discover Screen
**What goes wrong:** `app/browse/layout.tsx` wraps all `/browse/**` routes in `BrowseLayout`, which includes the `CategorySidebar`. The Discover screen at `/` does NOT use `BrowseLayout` — it renders directly inside `NavLayout`.
**Why it happens:** Could happen if someone mistakenly nests the Discover screen under `/browse/` routing.
**How to avoid:** The Discover screen lives at `app/page.tsx` (the root route `/`), completely outside the `app/browse/` directory and its layout. The `BrowseLayout` wrapper never touches it.

---

## Code Examples

### Existing Hero Pattern (from browse/page.tsx — reuse directly)

```typescript
// Source: frontend/app/browse/page.tsx lines 41-47
<h1 className="font-serif text-2xl sm:text-3xl md:text-4xl text-center text-[var(--text)] leading-tight tracking-tight">
  What are you{' '}
  <span className="italic text-[var(--primary)]">researching</span>{' '}
  today?
</h1>
<p className="text-sm sm:text-base text-[var(--text-secondary)] text-center mt-3 max-w-md">
  Expert reviews, real data, zero fluff.
</p>
```

### Existing Navigation Pattern

```typescript
// Source: frontend/app/browse/page.tsx lines 19-25
const router = useRouter()

const handleHeroSend = useCallback(() => {
  if (heroInput.trim()) {
    router.push(`/chat?q=${encodeURIComponent(heroInput.trim())}&new=1`)
  } else {
    router.push('/chat?new=1')
  }
}, [heroInput, router])
```

### Existing localStorage Guard Pattern

```typescript
// Source: frontend/app/browse/page.tsx lines 13-17
const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([])

useEffect(() => {
  setRecentSearches(getRecentSearches())
}, [])
```

### Existing Active Tab Detection (MobileTabBar)

```typescript
// Source: frontend/components/MobileTabBar.tsx lines 116-127
const getIsActive = (tabId: string, href: string | null) => {
  if (tabId === 'discover') {
    return pathname?.startsWith('/browse') || pathname === '/'
  }
  // ...
}
```

After migration, the `startsWith('/browse')` branch becomes irrelevant for Discover but stays harmless (no page lives there for root `/browse`). The `pathname === '/'` branch is the active one.

### UnifiedTopbar Active Tab Detection

```typescript
// Source: frontend/components/UnifiedTopbar.tsx lines 43-47
const getActiveTab = () => {
  if (pathname?.startsWith('/chat')) return 'ask'
  if (pathname?.startsWith('/browse') || pathname === '/') return 'discover'
  return 'discover'
}
```

Same analysis — `pathname === '/'` is the key branch after migration.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `redirect('/browse')` at `/` | Full editorial Discover screen | Phase 13 | Users land on value-first screen, no redirect |
| `BrowseLayout` wraps all browse content | `BrowseLayout` only for `/browse/[category]` | Phase 13 | Clean separation; no sidebar on Discover |
| `ChatInput` (textarea) as hero search | `DiscoverSearchBar` (button) as visual CTA | Phase 13 | Simpler interaction; typing starts in Chat screen |

---

## Open Questions

1. **"Popular" chip behavior**
   - What we know: "Popular" is hardcoded first; when no history exists, "Popular" is default active chip
   - What's unclear: Does tapping "Popular" navigate anywhere, or does it show all trending topics inline?
   - Recommendation: Treat "Popular" as a no-op tap (no navigation) or navigate to `/chat?new=1`. The safest is to navigate to `/chat?new=1` since all other chips navigate to chat.

2. **`/browse` root page fate**
   - What we know: Its content moves to `/`. It should no longer exist as a distinct page.
   - What's unclear: Should `app/browse/page.tsx` be deleted or replaced with `redirect('/')`?
   - Recommendation: Replace with `redirect('/')` to cleanly handle any users with bookmarked `/browse` URLs.

3. **"For You" inline card content**
   - What we know: When "For You" chip is active, recently researched items show inline below the chip row
   - What's unclear: Exactly what each "For You" item looks like (just query text? or a small card with product names?)
   - Recommendation: Reuse the existing recent-searches card style from `browse/page.tsx` lines 72-88, displayed in a condensed inline row.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest ^4.0.17 + @testing-library/react ^14.1.2 |
| Config file | `frontend/vitest.config.ts` |
| Quick run command | `cd frontend && npx vitest run tests/discoverScreen.test.tsx` |
| Full suite command | `cd frontend && npx vitest run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DISC-01 | `/` renders editorial hero headline with serif italic "researching" and search bar | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-01 | Subline "Expert reviews, real data, zero fluff." visible on `/` | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-02 | Category chip row renders at least 8 chips | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-02 | Tapping a category chip calls router.push with correct chat URL | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-03 | At least 3 trending cards render (icon, title, subtitle) | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-03 | Tapping a trending card calls router.push with encoded query | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-04 | "For You" chip is NOT shown when localStorage has no recent searches | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-04 | "For You" chip IS shown when localStorage has recent searches | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-05 | Clicking search bar calls router.push('/chat?new=1') | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |
| DISC-05 | Search bar renders as a button (not an input/textarea) | unit | `npx vitest run tests/discoverScreen.test.tsx` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run tests/discoverScreen.test.tsx`
- **Per wave merge:** `cd frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/discoverScreen.test.tsx` — covers DISC-01 through DISC-05 (10 behavioral contracts)
- [ ] No new fixtures or shared setup needed — existing `tests/setup.ts` (localStorage mock + router mock + jsdom) covers all Discover screen requirements

*(Existing `tests/setup.ts` already mocks: `next/navigation`, `localStorage`, and CSS variables — no additions needed)*

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `frontend/app/page.tsx` — current redirect implementation
- Direct code inspection of `frontend/app/browse/page.tsx` — hero pattern, localStorage guard, category navigation
- Direct code inspection of `frontend/lib/categoryConfig.ts` — category data shape and available slugs
- Direct code inspection of `frontend/lib/recentSearches.ts` — `getRecentSearches()` API and SSR safety pattern
- Direct code inspection of `frontend/components/UnifiedTopbar.tsx` — current Discover href and active tab detection
- Direct code inspection of `frontend/components/MobileTabBar.tsx` — current Discover tab href and active detection
- Direct code inspection of `frontend/components/NavLayout.tsx` — confirmed Discover screen renders inside NavLayout without additional wrappers
- Direct code inspection of `frontend/components/ChatInput.tsx` — existing textarea-based input (NOT suitable for Discover)
- Direct code inspection of `frontend/vitest.config.ts` and `frontend/package.json` — Vitest framework confirmed
- Direct code inspection of `frontend/tests/setup.ts` — existing mock infrastructure (localStorage, router, CSS vars)
- Direct code inspection of `frontend/.planning/phases/13-discover-screen/13-CONTEXT.md` — locked decisions
- Direct code inspection of `frontend/app/globals.css` — CSS variable definitions

### Secondary (MEDIUM confidence)
- Phase 12 test files (`navLayout.test.tsx`, `mobileTabBar.test.tsx`, `pageTransition.test.tsx`) — established test patterns for Phase 13 to follow
- `STATE.md` decisions block — confirmed Phase 12 navigation shell complete and approved by human verification

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already present, no new dependencies
- Architecture patterns: HIGH — directly derived from existing code in the same codebase
- Pitfalls: HIGH — drawn from observable code patterns (SSR guard, href values, layout nesting)
- Test requirements: HIGH — vitest framework confirmed, existing test patterns established

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable — no external dependencies change)
