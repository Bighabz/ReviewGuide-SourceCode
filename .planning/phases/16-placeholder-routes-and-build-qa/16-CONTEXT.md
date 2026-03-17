# Phase 16: Placeholder Routes and Build QA - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Final v2.0 milestone gate: create polished placeholder pages for `/saved` and `/compare`, ensure `next build` passes cleanly, and validate all new components work correctly in dark mode and on mobile. This phase confirms the entire milestone is production-deployable.

</domain>

<decisions>
## Implementation Decisions

### Placeholder page design
- Both `/saved` and `/compare` get polished editorial placeholder pages
- Each page: centered content with a Lucide icon (Bookmark for Saved, BarChart3 for Compare), serif italic heading ("Saved Items" / "Compare Products"), subtext ("This feature is coming soon. We're building something great."), and a CTA button back to Discover ("Back to Discover" → `/`)
- Pages use CSS variables, match the editorial luxury aesthetic
- Pages render inside NavLayout (get MobileHeader + tab bar on mobile, UnifiedTopbar on desktop)
- MobileTabBar Saved and Compare tabs updated to point to `/saved` and `/compare` (currently `/browse` fallback)
- UnifiedTopbar Saved and Compare links updated similarly
- Static pages (no client-side state needed) — should appear as "(Static)" in `next build` output

### Build QA
- `next build` must complete with zero errors
- All new routes (`/`, `/chat`, `/results/[id]`, `/saved`, `/compare`) must appear in build output
- `/saved` and `/compare` should be "(Static)" routes
- Full test suite must pass (`npm run test:run`)
- Dark mode validation: all new Phase 12-16 components render correctly in dark mode
- No TypeScript errors, no ESLint errors

### Claude's Discretion
- Exact placeholder page copy and visual polish
- Whether to add a decorative illustration or keep it icon-only
- Suspense wrapper placement if needed for any dynamic routes
- iOS device testing approach (simulator vs real device vs skip if unavailable)
- Whether to add a `/profile` placeholder (not in requirements but referenced in tab bar)

</decisions>

<specifics>
## Specific Ideas

- Placeholder pages should feel intentional, not broken — users should know the feature is planned
- The editorial aesthetic should carry through even on "Coming soon" pages
- This is the milestone's quality gate — if build passes and all tests are green, v2.0 is shippable

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NavLayout.tsx`: All pages render inside it — placeholders get header + tab bar automatically
- `MobileTabBar.tsx`: Saved/Compare tabs currently link to `/browse` — update to `/saved` and `/compare`
- `UnifiedTopbar.tsx`: Same links need updating
- `FunPlaceholder.tsx` in `frontend/components/ui/`: Existing placeholder component — may be reusable
- CSS variables in `globals.css`: Full editorial theme ready

### Established Patterns
- CSS variables exclusively (`var(--*)`)
- `font-serif` class for Instrument Serif headings
- Static Next.js pages: just export default function, no `'use client'` needed if no interactivity

### Integration Points
- `frontend/app/saved/page.tsx`: New route page
- `frontend/app/compare/page.tsx`: New route page
- `frontend/components/MobileTabBar.tsx`: Update Saved/Compare tab hrefs
- `frontend/components/UnifiedTopbar.tsx`: Update Saved/Compare link hrefs

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 16-placeholder-routes-and-build-qa*
*Context gathered: 2026-03-17*
