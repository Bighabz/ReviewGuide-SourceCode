---
phase: 11-viator-cj-expansion
plan: 04
subsystem: business-process
tags: [cj, viator, affiliate, credentials, railway]

requires:
  - phase: 11-02
    provides: "ViatorActivityProvider requiring VIATOR_API_KEY"
  - phase: 11-03
    provides: "Complete Viator pipeline requiring credentials on Railway"
provides:
  - "Documentation of required human actions for CJ and Viator setup"
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: []

key-decisions:
  - "Plan 11-04 is a business process plan requiring human action -- no code changes"
  - "CJ advertiser_ids=joined means approved advertisers appear automatically with zero code change"

patterns-established: []

requirements-completed: []

duration: 1min
completed: 2026-03-26
---

# Phase 11 Plan 04: CJ Advertiser Applications + Viator Credentials Summary

**Business process plan: CJ advertiser applications and Viator API credential setup require human action**

## Performance

- **Duration:** 1 min (documentation only)
- **Started:** 2026-03-26T00:12:00Z
- **Completed:** 2026-03-26T00:13:00Z
- **Tasks:** 0 (both tasks are checkpoint:human-action)
- **Files modified:** 0

## Accomplishments
- Documented all required human actions for CJ and Viator setup
- No code changes needed -- this plan is purely business process

## Task Commits

No commits -- this plan requires human action, not code changes.

## Required Human Actions

### Task 1: CJ Advertiser Applications (PROV-03)

Log in to CJ publisher portal (https://signup.cj.com) and submit applications to at least 3 of:

1. **Best Buy** - Advertisers -> Search "Best Buy" -> Apply
2. **Dell** - Advertisers -> Search "Dell" -> Apply
3. **Target** - Advertisers -> Search "Target" -> Apply
4. **Wayfair** - Advertisers -> Search "Wayfair" -> Apply
5. **Nike** - Advertisers -> Search "Nike" -> Apply

**Why no code change is needed:** The existing CJ provider uses `CJ_ADVERTISER_IDS="joined"` which means the CJ API automatically returns products from ALL approved advertisers. When any application is approved, products appear immediately.

**Verification:** Check email for application confirmation from CJ.

### Task 2: Viator API Credentials on Railway

1. Check if Viator affiliate account exists (check VIATOR_AFFILIATE_ID on Railway)
2. If not, sign up at https://partnerresources.viator.com/
3. Get API key (UUID format) and Affiliate ID (PID) from Account -> API Settings
4. Add to Railway environment variables:
   - `VIATOR_API_KEY` = (UUID API key)
   - `VIATOR_AFFILIATE_ID` = (PID number)
   - `VIATOR_API_ENABLED` = `true`
5. Redeploy backend
6. Check logs for `"Registered affiliate provider: viator"` to confirm

**Warning:** Per project memory lesson, always verify new feature flags exist on Railway after adding them. If you see `"Skipping affiliate provider 'viator': missing required env vars"`, the credentials were not set correctly.

## Files Created/Modified
None - no code changes.

## Decisions Made
- CJ advertiser applications submitted through publisher portal (business process, not code)
- Viator credentials provisioned via Railway env vars (infrastructure, not code)

## Deviations from Plan

None - plan documented as requiring human action, which is the correct approach.

## Issues Encountered
None.

## User Setup Required

**External services require manual configuration:**
- CJ publisher portal: Submit advertiser applications to 3+ target brands
- Viator Partner Resources: Obtain API key and affiliate ID
- Railway dashboard: Set VIATOR_API_KEY, VIATOR_AFFILIATE_ID, VIATOR_API_ENABLED=true

## Next Phase Readiness
- All code for Viator is complete and tested (Plans 01-03)
- Viator provider will auto-load once VIATOR_API_KEY is set on Railway
- CJ advertiser products will auto-appear once applications are approved

---
*Phase: 11-viator-cj-expansion*
*Completed: 2026-03-26*
