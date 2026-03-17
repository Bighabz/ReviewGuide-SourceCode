# Phase 13: Discover Screen - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Unified Discover screen at `/` replacing the current Browse/Chat split landing pages. Users can start research (search bar), explore categories (horizontal chip row), or tap a trending topic — all from one editorial screen. No backend changes required. Category detail pages (`/browse/[category]`) remain.

</domain>

<decisions>
## Implementation Decisions

### Hero section
- Drop the animated video logo — clean editorial hero only
- Headline: "What are you *researching* today?" — "researching" in serif italic (#1B4DFF via var(--primary))
- Subline: "Expert reviews, real data, zero fluff." — DM Sans Regular 14px, var(--text-secondary)
- Keep the same wording as existing browse page hero (already matches Figma spec)
- Search bar: left magnifying glass icon only, no decorative pen icon on right
- Search bar is a visual CTA, not an input field — tapping navigates to `/chat?new=1` with cursor focused in input. No typing happens on the Discover screen itself.
- Search bar height ~56px, 1px solid var(--border), 16px corner radius, subtle shadow

### Category chips
- Horizontal scrollable row of pill-shaped chips, no wrap
- Show top 8 categories from `categoryConfig.ts`: Popular (hardcoded first), Tech, Travel, Kitchen, Fitness, Home, Fashion, Outdoor
- Chip height 36px, padding 12px 16px, corner radius 20px (pill shape)
- Active chip: `bg-[var(--text)]` + white text (DM Sans SemiBold 13px) — adapts to dark mode via CSS variables
- Inactive chips: transparent background, `border-[var(--border)]`, `text-[var(--text)]`
- Scrollbar hidden on mobile (`-webkit-scrollbar: none`)
- Tapping a chip navigates to `/chat?q=<first query from categoryConfig>&new=1` — starts a focused research session
- "For You" chip: appears as the first chip ONLY if `recentSearches` exist in localStorage. If no history, "Popular" is first chip instead. "For You" shows recently researched items inline below the chip row when active.

### Trending research cards
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

### Route migration
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

</decisions>

<specifics>
## Specific Ideas

- The Discover screen should feel like a single editorial page, not a dashboard — visual hierarchy: hero (draw attention) → chips (quick filter) → trending (start browsing)
- "For You" personalization is lightweight (localStorage-based) — no backend, no accounts
- Trending topics are curated editorial picks, like a magazine's "What's Hot" section
- Category chips are a shortcut to research, not a filter mechanism — tapping sends to chat immediately

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `categoryConfig.ts`: 10+ categories with slug, name, tagline, image, icon, queries — chips pull from this
- `recentSearches.ts`: localStorage-based recent search tracking — "For You" chip reads from this
- `ChatInput.tsx`: Current hero search bar component — may be replaced with a simpler tap-to-navigate search bar
- `NavLayout.tsx`: Phase 12 navigation shell — Discover screen renders inside it
- `MobileTabBar.tsx`: Phase 12 tab bar — "Discover" tab needs href updated to `/`
- `cn()` from `frontend/lib/utils.ts`: Tailwind class merging utility

### Established Patterns
- CSS variables exclusively (`var(--*)`) — no Tailwind `dark:` utilities
- `'use client'` directive on interactive components
- `useRouter().push()` for programmatic navigation
- `font-serif` class for Instrument Serif editorial headings
- `product-card-hover` class for lift effect on interactive cards

### Integration Points
- `frontend/app/page.tsx`: Currently redirects to `/browse` — will become the Discover screen
- `frontend/app/browse/page.tsx`: Current browse page — its hero/categories/recent sections are being replaced
- `frontend/components/browse/BrowseLayout.tsx`: Desktop sidebar layout — used only by category pages going forward
- `frontend/components/UnifiedTopbar.tsx`: "Discover" link needs href change from `/browse` to `/`
- `frontend/components/MobileTabBar.tsx`: "Discover" tab href needs change from `/browse` to `/`
- `frontend/components/NavLayout.tsx`: Active tab detection needs to handle `/` as the Discover route

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-discover-screen*
*Context gathered: 2026-03-17*
