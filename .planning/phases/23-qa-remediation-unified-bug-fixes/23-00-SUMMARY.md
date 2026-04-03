---
phase: 23-qa-remediation-unified-bug-fixes
plan: "00"
subsystem: testing
tags: [baseline, qa, snapshot, audit]

# Dependency graph
requires: []
provides:
  - "Pre-fix baseline snapshot: commit SHA, env config, model config, affiliate tags, API URL, 8 canonical prompts"
  - "BASELINE.md at .planning/phases/23-qa-remediation-unified-bug-fixes/BASELINE.md"
affects:
  - "23-01 through 23-N (all Phase 23 fix plans measure against this baseline)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "QA run template: prompt, session_id, request_id, tools invoked, time-to-first-token, time-to-done"

key-files:
  created:
    - .planning/phases/23-qa-remediation-unified-bug-fixes/BASELINE.md
  modified: []

key-decisions:
  - "Baseline captures .env affiliate tag (mikejahshan-20) AND code hardcoded fallback (revguide-20) separately — discrepancy noted for QAR-07 fix"
  - "RATE_LIMIT_ENABLED=false in .env overrides docker-compose default of true — intentional for local dev"
  - "8 canonical prompts map directly to QAR bug IDs rather than generic smoke tests"

patterns-established:
  - "QA Run Template: each test run against canonical prompts must record session_id, request_id, tools invoked, TTFT, and time-to-done"

requirements-completed:
  - QAR-00

# Metrics
duration: 8min
completed: 2026-04-03
---

# Phase 23 Plan 00: QA Remediation Baseline Summary

**Pre-fix baseline snapshot created with commit SHA `46c3b99`, environment config, model config, affiliate tags (noting `mikejahshan-20` vs `revguide-20` discrepancy), and 8 canonical test prompts mapped to QAR bug IDs**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-03T05:49:23Z
- **Completed:** 2026-04-03T05:57:10Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Captured frozen pre-fix state: commit SHA, all non-secret env vars from `docker-compose.yml` + `backend/.env`
- Documented model configuration: all agents on `gpt-4o-mini`, search provider `openai`, `USE_CURATED_LINKS=true`
- Identified affiliate tag discrepancy: `.env` still has `mikejahshan-20` while code fallback uses `revguide-20` (QAR-07 scope)
- Created 8 canonical test prompts with expected tool chains and per-prompt QAR coverage mapping
- Defined QA run template for recording per-test metrics (session_id, TTFT, tools invoked)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BASELINE.md with pre-fix snapshot** - `d96390e` (chore)

**Plan metadata:** *(this SUMMARY commit)*

## Files Created/Modified

- `.planning/phases/23-qa-remediation-unified-bug-fixes/BASELINE.md` - Pre-fix baseline with commit SHA, env snapshot, model config, affiliate tags, 8 canonical test prompts + QAR map

## Decisions Made

- Captured `.env` affiliate tag (`mikejahshan-20`) AND code hardcoded fallback (`revguide-20`) separately — the discrepancy itself is a bug to fix in QAR-07
- RATE_LIMIT_ENABLED=false is the live local dev value; docker-compose default is true — both recorded
- 8 canonical prompts were scoped to cover QAR-01 through QAR-07 directly, not as generic smoke tests

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `backend/.env` still references `mikejahshan-20` despite memory file noting migration to `revguide-20` on 2026-03-25. This was expected — it is a pre-existing discrepancy that the baseline captures, not a new issue.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- BASELINE.md is frozen and committed at `d96390e`
- All Phase 23 fix plans (23-01 onward) have a concrete "before" state to measure against
- Canonical prompts and QA run template are ready for use in regression harness (Phase 23-05 / QAR-08)
- Affiliate tag discrepancy (`mikejahshan-20` in `.env` vs `revguide-20` in code) should be resolved during QAR-07 fix

---

*Phase: 23-qa-remediation-unified-bug-fixes*
*Completed: 2026-04-03*
