---
phase: 14-chat-screen
plan: 02
subsystem: ui
tags: [react, typescript, context, mcp, python, lucide-react]

# Dependency graph
requires:
  - phase: 14-chat-screen
    provides: Plan 01 RED tests for CHAT-02, CHAT-03, CHAT-04 (inlineProductCard, sourceCitations tests)

provides:
  - backend/mcp_server/tools/product_compose.py emits review_sources UI block with source URLs
  - frontend/components/InlineProductCard.tsx: 64px compact product card with rank badges, curated images, affiliate links
  - frontend/components/SourceCitations.tsx: flat colored-dot citation list with +X more toggle
  - frontend/lib/chatStatusContext.tsx: ChatStatusProvider and useChatStatus for cross-tree status sharing

affects:
  - 14-03 (Plan 03 wires these components into Message.tsx, BlockRegistry, MobileHeader, NavLayout)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - CSS variables exclusively (var(--*)) in new React components — no dark: Tailwind utilities
    - Inline style for dynamic colors combined with static Tailwind class for DOM-queryability in tests
    - useCallback memoization on context setters to prevent unnecessary re-renders
    - Emoji prepended in separate aria-hidden span to allow exact-text matching in tests

key-files:
  created:
    - backend/mcp_server/tools/product_compose.py (modified — review_sources block restored)
    - frontend/components/InlineProductCard.tsx
    - frontend/components/SourceCitations.tsx
    - frontend/lib/chatStatusContext.tsx
  modified:
    - backend/mcp_server/tools/product_compose.py

key-decisions:
  - "review_sources consensus intentionally empty string — blog assistant_text handles editorial prose to avoid Pitfall 3 redundancy"
  - "Colored dots use both inline style (for correct color) and Tailwind bg- class (for test DOM queryability)"
  - "Emoji prefix rendered in separate aria-hidden span so getByText('Premium') matches label-only node"

patterns-established:
  - "Dual color approach: inline style sets actual color, Tailwind bg- class enables test queryability"
  - "Rank badge emojis in aria-hidden span so test text matchers find label text exactly"

requirements-completed: [CHAT-02, CHAT-03, CHAT-04]

# Metrics
duration: 7min
completed: 2026-03-17
---

# Phase 14 Plan 02: Foundational Components Summary

**Restored product_compose review_sources backend block and created InlineProductCard, SourceCitations, and ChatStatusContext frontend primitives — all 29 CHAT-02/CHAT-04 tests GREEN**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-03-17T09:20:00Z
- **Completed:** 2026-03-17T09:27:19Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Restored review_sources UI block in product_compose.py (deleted in bd4b5c3 refactor) — source URLs now reach frontend via SSE stream
- Created InlineProductCard with 64px product rows, curated Amazon image lookup, rank badges (Top Pick/Best Value/Premium), and affiliate links
- Created SourceCitations with flattened/deduped source list, colored dots by position, site name + title, and +X more expander
- Created ChatStatusContext providing isStreaming/statusText/sessionTitle across the component tree without prop drilling
- All 29 previously RED tests for CHAT-02 and CHAT-04 now pass GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Restore review_sources UI block in product_compose.py** - `c6efdcc` (fix)
2. **Task 2: Create InlineProductCard, SourceCitations, and ChatStatusContext** - `14d45fe` (feat)

## Files Created/Modified
- `backend/mcp_server/tools/product_compose.py` - Added 31-line review_sources block after product_review card assembly
- `frontend/components/InlineProductCard.tsx` - Compact 64px product card with rank badges, curated image lookup, price, affiliate link
- `frontend/components/SourceCitations.tsx` - Flat citation list with colored dots, +X more toggle, deduplication by URL
- `frontend/lib/chatStatusContext.tsx` - ChatStatusProvider + useChatStatus React context for cross-tree streaming status

## Decisions Made
- `consensus` field set to empty string intentionally — blog-style assistant_text already contains editorial prose; SourceCitations only renders source links to avoid redundancy (Pitfall 3 from RESEARCH.md)
- Colored dots use both `style={{ backgroundColor: '#EF4444' }}` AND `className="bg-red-500"` — inline style for visual accuracy, Tailwind class for test DOM queryability
- Emoji in rank badge wrapped in separate `aria-hidden` span so `getByText('Premium')` finds the label text node exactly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed rank badge emoji breaking getByText test**
- **Found during:** Task 2 (InlineProductCard creation)
- **Issue:** Emoji and label text in same span caused `getByText('Premium')` to fail — DOM text was "✨ Premium" not "Premium"
- **Fix:** Moved emoji into its own `aria-hidden` span so label text node is independently queryable
- **Files modified:** frontend/components/InlineProductCard.tsx
- **Verification:** `screen.getByText('Premium')` passes in test suite
- **Committed in:** 14d45fe (Task 2 commit)

**2. [Rule 1 - Bug] Fixed colored dot test — inline-only style not queryable**
- **Found during:** Task 2 (SourceCitations creation)
- **Issue:** Tests check both `[class*="bg-[#EF4444]"]` and `[class*="rounded-full"][class*="bg-"]` — inline-style-only dots failed both selectors
- **Fix:** Added `bg-red-500 / bg-blue-500 / bg-green-500 / bg-orange-500` Tailwind classes alongside inline styles
- **Files modified:** frontend/components/SourceCitations.tsx
- **Verification:** All 3 dot color tests and the general dot existence test pass
- **Committed in:** 14d45fe (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs in initial implementation caught by test run)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing TypeScript errors in `tests/chatScreen.test.tsx` and `tests/suggestions.test.tsx` (timestamp type mismatch and Mock type mismatch) — these are out-of-scope pre-existing issues, not introduced by Plan 02. Verified new files have zero TypeScript errors.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All four foundational pieces ready for Plan 03 integration
- InlineProductCard, SourceCitations wired into Message.tsx BlockRegistry in Plan 03
- ChatStatusContext provider added to NavLayout in Plan 03
- MobileHeader consumes ChatStatusContext (useChatStatus) in Plan 03
- review_sources backend block now live — SourceCitations will render when chat returns product review data

---
*Phase: 14-chat-screen*
*Completed: 2026-03-17*

## Self-Check: PASSED
- All 4 source files confirmed present on disk
- Both task commits (c6efdcc, 14d45fe) confirmed in git log
