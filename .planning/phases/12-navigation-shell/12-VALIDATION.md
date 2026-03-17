---
phase: 12
slug: navigation-shell
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.0.17 + @testing-library/react 14 |
| **Config file** | `frontend/vitest.config.ts` |
| **Quick run command** | `cd frontend && npm run test:run -- --reporter=verbose tests/mobileTabBar.test.tsx tests/navLayout.test.tsx` |
| **Full suite command** | `cd frontend && npm run test:run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run test:run -- --reporter=verbose tests/mobileTabBar.test.tsx tests/navLayout.test.tsx`
- **After every plan wave:** Run `cd frontend && npm run test:run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 0 | NAV-01 | unit | `npm run test:run -- tests/mobileTabBar.test.tsx` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 0 | NAV-02 | unit | `npm run test:run -- tests/navLayout.test.tsx` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 0 | NAV-03 | unit | `npm run test:run -- tests/mobileTabBar.test.tsx` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 0 | NAV-04 | unit | `npm run test:run -- tests/pageTransition.test.tsx` | ❌ W0 | ⬜ pending |
| 12-01-05 | 01 | 0 | NAV-05 | unit | `npm run test:run -- tests/mobileTabBar.test.tsx tests/layout.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/tests/navLayout.test.tsx` — stubs for NAV-01 (responsive hiding), NAV-02 (desktop topbar), excluded routes
- [ ] `frontend/tests/mobileTabBar.test.tsx` — stubs for NAV-01 (5 tabs), NAV-03 (FAB click), NAV-05 (safe area style)
- [ ] `frontend/tests/pageTransition.test.tsx` — stubs for NAV-04 (template.tsx motion.div)
- [ ] `frontend/tests/layout.test.tsx` — stubs for NAV-05 (viewport viewportFit: 'cover')

*Existing `tests/setup.ts` already mocks `usePathname`, `useRouter`, and `localStorage` — NavLayout tests can use it directly.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tab bar hides when keyboard opens | NAV-05 | Requires real iOS device with software keyboard | Open chat on iPhone, tap input, verify tab bar slides down |
| iOS safe area inset rendering | NAV-05 | env(safe-area-inset-bottom) returns 0 in non-Safari | Test on iPhone with home indicator, verify no overlap |
| Animated page transitions visual smoothness | NAV-04 | Visual quality assessment | Navigate between tabs, verify no white flash or stutter |
| Long-press Profile for theme popover | Context | Gesture detection needs real touch input | Long-press Profile tab on mobile, verify popover appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
