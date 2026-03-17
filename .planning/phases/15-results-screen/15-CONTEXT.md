# Phase 15: Results Screen - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Dedicated `/results/:sessionId` route showing a full results view for a completed research session. Product card grid with rank badges and score bars, sources panel, quick actions, desktop split panel with minimal sidebar, mobile full-width layout. Data sourced from localStorage. No backend changes.

</domain>

<decisions>
## Implementation Decisions

### Data source + URL scheme
- Data sourced from localStorage — read the chat session's messages + ui_blocks using the session ID
- URL format: `/results/:sessionId` using the existing session UUID (e.g., `/results/a1b2c3d4-e5f6-...`)
- The expand icon (↗) in MobileHeader navigates to `/results/{currentSessionId}` — wire this in Phase 15 (was placeholder in Phase 14)
- If session not found in localStorage (fresh browser, expired data): redirect to `/` with a brief toast message "Session not found — start a new research"
- URL is "shareable" on the same browser only (localStorage limitation) — no backend persistence needed

### Product card grid
- One `ResultsProductCard` component with responsive container
- Mobile: horizontal scroll container (flex-row, overflow-x-auto, snap-x), cards 170px wide, peek effect showing ~2.2 cards
- Desktop: CSS grid (grid-cols-3), cards ~200px wide, max-width 1200px content area
- Card design: 16px corner radius, 0.67px solid var(--border), white background, 12px internal padding
- Top section: 100px height, pastel background tints via new CSS variables (--card-accent-1 through --card-accent-4 with dark mode variants). Rank badge (24px black circle, white number). Centered product image (~64px, object-fit contain).
- Middle section: category badge (pill, colored bg — Top Pick = warm gold, Best Value = blue, Premium = purple), product name (SemiBold 14px, 2-line clamp), short description (Regular 11px, 2-line clamp), score bar (4px height, var(--primary) fill, score number right-aligned)
- Bottom section: price (Bold 18px) left, "Buy on Amazon" CTA button right (var(--primary) bg, white text, 8px radius, 36px height). If no affiliate link: muted "Check Amazon →" text link
- Score derivation: average review ratings if available, else position-based fallback (1st=95, 2nd=88, 3rd=82, 4th=76, 5th=70)
- Images: same curated Amazon lookup + category placeholder fallback as Phase 14 InlineProductCard

### Desktop layout + sidebar
- Minimal left sidebar on desktop (320px): logo, current session title (active state), "Back to Chat" link. No conversation search, no history list.
- Sidebar hidden on mobile — back arrow in MobileHeader returns to chat
- Sidebar is part of the Results page component (not NavLayout) — implemented via CSS grid on desktop
- Sources section: inline below the header summary, above product grid. Collapsible on mobile (default expanded). Reuses SourceCitations component from Phase 14 with editorial "SOURCES ANALYZED" header styling.
- Results page renders inside NavLayout (gets MobileHeader + tab bar on mobile, UnifiedTopbar on desktop)

### Quick actions
- Three actions: Compare side by side, Export to list, Share results
- Share: functional — copies current URL to clipboard via `navigator.clipboard.writeText()` with "Link copied!" toast
- Compare and Export: visual placeholders — show "Coming soon" toast on click
- No "Set price alert" button — requires accounts (out of v2.0 scope)
- "QUICK ACTIONS" editorial header (uppercase DM Sans Medium 11px, var(--text-muted), letter-spacing 1.5px)
- Each action: icon + label, 44px height, DM Sans Regular 14px

### Results header
- Title: serif italic, 24px mobile / 28px desktop — derived from first user message (same as chat header title)
- Action buttons row below title: Share, Save (bookmark), Refresh — icon + label, spaced 24px
- Summary paragraph: 2-3 sentence synthesis mentioning number of sources in bold

### Claude's Discretion
- Exact pastel tint CSS variable values for dark mode
- Score bar animation/transition treatment
- Toast notification implementation (native vs component)
- How to extract product + source data from session messages/ui_blocks
- Results header summary text generation (from first AI response content)
- Horizontal scroll snap behavior details on mobile
- Whether to add follow-up chips at the bottom of Results (spec mentions them, but they may be deferred)

</decisions>

<specifics>
## Specific Ideas

- The Results page should feel like a polished editorial report — the "final output" of a research session
- Product cards are the hero element — large, visual, with clear rank badges and CTA buttons
- Score bars give a visual sense of relative quality at a glance
- Pastel card backgrounds differentiate products and add visual interest (not just white cards)
- The minimal sidebar on desktop gives the Results page a "dashboard" feel without the complexity of a full conversation history

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `InlineProductCard.tsx` (Phase 14): Compact 64px cards with curated image lookup — image/link logic reusable for ResultsProductCard
- `SourceCitations.tsx` (Phase 14): Colored dots + clickable source links — reuse for Results sources section
- `curatedLinks.ts`: 120+ products with Amazon images, prices, affiliate links
- `MobileHeader.tsx`: Has expand icon (↗) placeholder — wire to `/results/:sessionId`
- `ChatStatusContext`: Available for session title sharing
- `ConversationSidebar.tsx`: Existing sidebar component — may inform minimal sidebar design
- `framer-motion`: For scroll animations, card transitions

### Established Patterns
- CSS variables exclusively (`var(--*)`)
- `'use client'` on interactive components
- `usePathname()` / `useRouter()` from `next/navigation`
- `font-serif` class for Instrument Serif editorial headings
- `product-card-hover` class for lift effect

### Integration Points
- `frontend/app/results/[id]/page.tsx`: New dynamic route page
- `frontend/components/MobileHeader.tsx`: Wire expand icon to navigate to `/results/:sessionId`
- `frontend/app/globals.css`: Add new `--card-accent-*` CSS variables
- `frontend/components/NavLayout.tsx`: Active tab detection may need update for `/results` routes
- localStorage: Read session data via existing session storage keys from `CHAT_CONFIG`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-results-screen*
*Context gathered: 2026-03-17*
