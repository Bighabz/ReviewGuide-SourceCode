---
phase: 14
slug: chat-screen
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 2.x + @testing-library/react 14 + jsdom |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- tests/chatScreen.test.tsx tests/inlineProductCard.test.tsx tests/sourceCitations.test.tsx` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:run -- tests/chatScreen.test.tsx tests/inlineProductCard.test.tsx tests/sourceCitations.test.tsx`
- **After every plan wave:** Run `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 0 | CHAT-01 | unit | `npm run test:run -- tests/chatScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 0 | CHAT-02 | unit | `npm run test:run -- tests/inlineProductCard.test.tsx` | ❌ W0 | ⬜ pending |
| 14-01-03 | 01 | 0 | CHAT-03 | unit | `npm run test:run -- tests/chatScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 14-01-04 | 01 | 0 | CHAT-04 | unit | `npm run test:run -- tests/sourceCitations.test.tsx` | ❌ W0 | ⬜ pending |
| 14-01-05 | 01 | 0 | CHAT-05 | unit | `npm run test:run -- tests/chatScreen.test.tsx` | ❌ W0 | ⬜ pending |
| 14-01-06 | 01 | 0 | CHAT-06 | unit | `npm run test:run -- tests/chatScreen.test.tsx` | Exists (partial) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/chatScreen.test.tsx` — covers CHAT-01 (render order), CHAT-03 (status display), CHAT-05 (bubble alignment + label), CHAT-06 (chip restyle)
- [ ] `frontend/tests/inlineProductCard.test.tsx` — covers CHAT-02 (64px height, rank badges, image fallback, affiliate link)
- [ ] `frontend/tests/sourceCitations.test.tsx` — covers CHAT-04 (clickable links, target="_blank", colored dots, "+X more")

*Existing `tests/setup.ts` provides mocks for router, localStorage, CSS variables.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Asymmetric bubble corner rendering | CHAT-05 | CSS border-radius visual check | View chat on mobile, verify iMessage-style bubble tails |
| Live streaming status updates in header | CHAT-03 | Requires real SSE streaming from backend | Send a product query, watch header status line update in real-time |
| Source citation links open correct URLs | CHAT-04 | Requires real backend data with review_sources fix | Click a source citation, verify it opens the actual review article |
| Compact card images from curated data | CHAT-02 | Requires matching product names to curated links | Send a query for a curated product, verify real Amazon image appears |
| Suggestion chip restyle visual quality | CHAT-06 | Visual assessment of pill styling | View suggestion chips, verify they match editorial spec |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
