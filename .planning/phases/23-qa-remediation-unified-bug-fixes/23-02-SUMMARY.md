---
phase: 23-qa-remediation-unified-bug-fixes
plan: "02"
subsystem: frontend
tags: [bug-fix, mobile, css, overflow, z-index, 404]
dependency_graph:
  requires: []
  provides: [overflow-x-clip-body, custom-404-page, mobile-chat-bubble-fix, chat-input-z-index-fix]
  affects: [frontend/app/globals.css, frontend/app/chat/page.tsx, frontend/components/ChatContainer.tsx, frontend/components/Message.tsx, frontend/app/not-found.tsx]
tech_stack:
  added: []
  patterns: [overflow-clip instead of overflow-hidden on ancestor containers, sticky z-index above fixed MobileTabBar, editorial 404 page with CSS vars]
key_files:
  created:
    - frontend/app/not-found.tsx
    - frontend/tests/notFound.test.tsx
  modified:
    - frontend/app/globals.css
    - frontend/app/chat/page.tsx
    - frontend/components/ChatContainer.tsx
    - frontend/components/Message.tsx
    - frontend/tests/chatScreen.test.tsx
    - frontend/tests/layout.test.tsx
decisions:
  - "Use overflow-clip instead of overflow-hidden everywhere — clip prevents scroll containment issues while hidden creates BFC that crushes flex children"
  - "Chat input z-index raised to z-[300] (above MobileTabBar z-[200]) so chat bar is always visible on mobile"
  - "Removed minWidth: fit-content from user bubble — was causing 167px collapse in constrained parents on mobile"
  - "Dark mode CSS vars for stop button (--surface-elevated, --surface-hover, --text-secondary, --border) confirmed present in [data-theme=dark] — no changes needed"
metrics:
  duration: 581s
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_modified: 7
---

# Phase 23 Plan 02: Mobile Bug Fixes and Custom 404 Page Summary

Five P0/P1 frontend bugs fixed across 4 files: `overflow-clip` on body + 4 chat ancestor containers, user bubble `minWidth: fit-content` removed, chat input raised to `z-[300]` above mobile nav, dark mode CSS vars confirmed, and editorial 404 page created.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write failing tests (TDD RED) | f889588 | tests/chatScreen.test.tsx, tests/layout.test.tsx, tests/notFound.test.tsx |
| 2 | Apply 5 fixes — overflow-x, bubble, z-index, dark mode, 404 | cef2f33 | globals.css, chat/page.tsx, ChatContainer.tsx, Message.tsx, not-found.tsx |

## What Was Built

### Fix 1 — Chat bubble mobile width (QAR-08)
Removed `style={{ minWidth: 'fit-content' }}` from the user chat bubble in `Message.tsx` line 152. This property forced the bubble to minimum content width when its parent was narrow on mobile, causing the ~167px collapse. Also changed `overflow-hidden` to `overflow-clip` on `#message-container` (line 119) — this is the parent that was creating a block formatting context that crushed flex children.

### Fix 2 — Chat input nav overlap (QAR-08)
The `MobileTabBar` component uses `fixed bottom-0 z-[200]`. The chat input wrapper was at `z-40`, sitting below the tab bar visually. Raised chat input wrapper to `z-[300]` so it renders above the MobileTabBar on all mobile viewports.

### Fix 3 — overflow-x: clip (QAR-09)
Changed `overflow-x: hidden` to `overflow-x: clip` in the `body` rule in `globals.css`. Also applied `overflow-clip` to all 3 `overflow-hidden` containers in `chat/page.tsx` (h-dvh wrapper, flex-1 inner, main) and the `#chat-container` div in `ChatContainer.tsx`. The `clip` value preserves iOS zoom-pan and avoids the scroll containment issues that `hidden` introduces.

### Fix 4 — Stop button dark mode (QAR-11)
Verified all CSS variables used by the stop button (`--surface-elevated`, `--border`, `--text-secondary`, `--text`, `--surface-hover`) are defined in the `[data-theme="dark"]` block in `globals.css`. No changes needed — the vars were already present with correct dark values.

### Fix 5 — Custom 404 page (QAR-10)
Created `frontend/app/not-found.tsx` using the editorial luxury theme: `font-serif` heading, CSS variable colors (`var(--text)`, `var(--primary)`), and a styled "Back to home" link to `/`.

## Test Results

- `tests/layout.test.tsx` — 4/4 pass (including new QAR-09 overflow-x: clip test)
- `tests/notFound.test.tsx` — 5/5 pass (new file, all QAR-10 tests)
- `tests/chatScreen.test.tsx` — 21/22 pass (QAR-11 stop button test passes; 1 pre-existing "Thinking..." failure unrelated to this plan)
- Full suite: 272 pass, 21 fail (21 failures all pre-existing, same as baseline)
- Build: passes cleanly, `/_not-found` route included

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed QAR-11 test regex to capture button opening tag**
- **Found during:** Task 1 (TDD GREEN verification)
- **Issue:** Initial stop button test used regex `Stop generating...` which matched only the closing tag content — className attribute was BEFORE the text node, so `var(--` was not in the captured string
- **Fix:** Changed regex to `<button...Stop generating...` to capture from opening tag
- **Files modified:** frontend/tests/chatScreen.test.tsx
- **Commit:** cef2f33 (included in same commit)

**2. [Rule 1 - Bug] Confirmed stash pop preserved all file changes**
- **Found during:** Task 2 verification
- **Issue:** git stash pop was used to verify pre-existing test failure baseline; system reminders showed old file contents causing confusion about whether changes were applied
- **Fix:** Verified actual file contents with grep — all changes were in place
- **Files modified:** none (verification only)

## Decisions Made

- Use `overflow-clip` everywhere instead of `overflow-hidden` — `clip` is strictly better: it prevents painting outside the box without creating a BFC or new scroll container. iOS zoom-pan relies on being able to scroll the root; `overflow-x: hidden` on body blocks this.
- Chat input z-index set to `z-[300]` (above `z-[200]` MobileTabBar) rather than adding padding/margin — z-index fix is cleaner and doesn't affect layout flow.
- `minWidth: fit-content` removed entirely from user bubble — no replacement needed; `max-w-[85%]` on the bubble div and `max-w-full` on the parent provide the correct constraints.
- Dark mode vars for stop button confirmed present — QAR-11 was a verification requirement, not a missing-vars fix.

## Self-Check: PASSED
