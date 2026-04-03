---
phase: 23-qa-remediation-unified-bug-fixes
plan: 05
subsystem: frontend
tags: [wcag, accessibility, mobile, ios-scroll, chat-history, streaming, navigation]
dependency_graph:
  requires: [23-02]
  provides: [QAR-13, QAR-14, QAR-15, QAR-16, QAR-18, QAR-19]
  affects: [frontend/components/MessageList.tsx, frontend/components/ChatContainer.tsx, frontend/app/chat/page.tsx, frontend/app/globals.css, frontend/app/browse/page.tsx]
tech_stack:
  added: []
  patterns: [sentinel-scroll, queued-message-state, localStorage-session-tracking, url-session-param]
key_files:
  created: []
  modified:
    - frontend/app/globals.css
    - frontend/app/browse/page.tsx
    - frontend/components/ChatContainer.tsx
    - frontend/components/MessageList.tsx
    - frontend/app/chat/page.tsx
    - frontend/tests/chatScreen.test.tsx
decisions:
  - "Sentinel bottomRef div + scrollIntoView replaces 400ms setInterval+rAF — works reliably on iOS Safari where imperative scrollTop can fight native momentum scroll"
  - "Queue user message in state instead of full auto-send loop — simple useState + useEffect to watch isStreaming transition, 50ms setTimeout to allow state flush"
  - "trackSessionId() helper centralises chat_all_session_ids writes — called at all 3 session creation paths (URL query param, new session no query, handleNewConversation)"
  - "Session ID added to URL (?session=<id>) via router.replace so browser history entries carry the session context for forward/back navigation"
  - "--text-muted raised: light mode #A8A29E->%237373 (2.8:1->4.6:1), dark mode --text-muted #5A6478->%238892A4 (2.3:1->4.5:1), dark --text-secondary #8892A4->%239AA3B5 (4.5->5.3:1)"
metrics:
  duration: 435s
  completed: "2026-04-03"
  tasks: 2
  files: 6
---

# Phase 23 Plan 05: P2 Frontend Bug Fixes Summary

**One-liner:** WCAG-AA contrast fixes, sentinel-based iOS scroll, session history tracking with URL-reflected session IDs, queued message state, and documented /browse redirect.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | WCAG contrast, landscape nav, queued message, /browse comment | 3e5f0a3 |
| 2 | Sentinel scroll, session tracking, session in URL, tests | 2b1c653 |

## What Was Built

### QAR-13: WCAG AA contrast fixes (globals.css)

Three CSS variable values raised to meet WCAG AA (4.5:1) minimum:

| Variable | Before | After | Ratio change |
|----------|--------|-------|-------------|
| `--text-muted` (light) | `#A8A29E` | `#737373` | 2.8:1 → 4.6:1 |
| `--text-secondary` (dark) | `#8892A4` | `#9AA3B5` | 4.5:1 → 5.3:1 |
| `--text-muted` (dark) | `#5A6478` | `#8892A4` | 2.3:1 → 4.5:1 |

`--text-secondary` in light mode (`#57534E`) was already at ~7.4:1 and was not changed.

### QAR-14: Sentinel-based auto-scroll (MessageList.tsx)

Replaced `setInterval(..., 400)` + `scrollTop = scrollHeight` with:
- `const bottomRef = useRef<HTMLDivElement>(null)` 
- `useEffect` that calls `bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })` when `messages` or `isStreaming` changes (respecting `userScrolledUpRef` and `isTouchingRef` guards)
- `<div ref={bottomRef} aria-hidden="true" />` sentinel at bottom of message list
- Added `WebkitOverflowScrolling: 'touch'` and `overscrollBehaviorY: 'contain'` inline styles to scroll container

### QAR-15: Landscape orientation bottom nav (globals.css)

Added CSS override for `@media (orientation: landscape) and (max-height: 500px)` that forces `[data-keyboard-open="false"]` transform to `translateY(0) !important`, ensuring the bottom nav stays visible regardless of viewport height in landscape.

### QAR-16: Chat history session tracking (chat/page.tsx)

Added `trackSessionId(sessionId)` helper that pushes session IDs to `chat_all_session_ids` localStorage array. Called at all 3 session creation paths:
1. New session with URL query param (`?q=...&new=1`)
2. New session without query (`?new=1`)
3. `handleNewConversation()` callback

Also added `?session=<id>` to URL via `router.replace` so browser history entries reflect the active session. On normal page load, reads `?session` param and restores the correct session.

`ConversationSidebar` already reads `chat_all_session_ids` correctly — the bug was that the key was never populated, now it is.

### QAR-18: Queued message during streaming (ChatContainer.tsx)

Replaced silent `return` with:
- `const [queuedMessage, setQueuedMessage] = useState<string | null>(null)`
- When `isStreaming` is true in `handleSendMessage`: `setQueuedMessage(messageToSend); setInput(''); return`
- Same for `handleSuggestionClick`: stores suggestion in queue instead of silently ignoring
- `useEffect` watching `isStreaming`: when it transitions to `false` and `queuedMessage` is set, sends it automatically
- Visual notice below Stop button: "Message queued — will send after response completes"

### QAR-19: /browse documented redirect (browse/page.tsx)

Added JSDoc comment explaining the intentional redirect — homepage serves as primary browse/discover experience, redirect handles legacy links.

## Verification

- Build: passes (`npm run build` — all 16 routes built cleanly)
- Tests: 274 passing, 21 failing — same 21 failures as pre-plan baseline (pre-existing across MobileTabBar, homePage, topPickBlock, inlineProductCard tests)
- 2 new QAR-14 sentinel tests added and passing

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| `frontend/components/MessageList.tsx` | FOUND — bottomRef x4, scrollIntoView, no setInterval |
| `frontend/app/chat/page.tsx` | FOUND — chat_all_session_ids x3, trackSessionId helper |
| `frontend/app/globals.css` | FOUND — WCAG contrast adjustments, landscape media query |
| `frontend/components/ChatContainer.tsx` | FOUND — queuedMessage state x7 |
| `frontend/app/browse/page.tsx` | FOUND — intentional redirect comment |
| `.planning/phases/23-qa-remediation-unified-bug-fixes/23-05-SUMMARY.md` | FOUND |
| Commit `3e5f0a3` (Task 1) | FOUND |
| Commit `2b1c653` (Task 2) | FOUND |
| Build | PASSED — 16 routes built cleanly |
| Tests | 274 passing, 21 pre-existing failures (no regressions) |
