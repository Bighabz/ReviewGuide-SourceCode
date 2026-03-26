---
phase: 06-skimlinks-link-wrapper
plan: 02
subsystem: api
tags: [skimlinks, affiliate, httpx, redis-cache, oauth2, pydantic-settings]

requires:
  - phase: 06-skimlinks-link-wrapper
    provides: RED test scaffold (Plan 01)
provides:
  - SkimlinksLinkWrapper service class with wrap_url(), domain cache, OAuth2 auth
  - 6 SKIMLINKS_* config fields in Settings
  - Module-level singleton skimlinks_wrapper for import by other modules
  - EXCLUDED_DOMAINS constant (21 Amazon + eBay domains)
affects: [06-skimlinks-link-wrapper, 07-skimlinks-middleware]

tech-stack:
  added: []
  patterns: [Standalone service class (not BaseAffiliateProvider subclass) for URL wrapping vs product search, three-tier cache (in-memory -> Redis -> API)]

key-files:
  created:
    - backend/app/services/affiliate/skimlinks.py
  modified:
    - backend/app/core/config.py

key-decisions:
  - "SkimlinksLinkWrapper is standalone service, NOT BaseAffiliateProvider subclass -- Skimlinks wraps URLs, not searches for products"
  - "21 excluded domains: 13 Amazon variants (including amzn.to) + 8 eBay variants"
  - "Three-tier caching: in-memory set -> Redis JSON -> Merchant API (reduces API calls to near zero)"
  - "DOMAIN_CACHE_TTL = 86400 (24h) as module constant used directly in redis_set_with_retry call"

patterns-established:
  - "URL wrapping service pattern: enabled flag, extract domain, check exclusion, check merchant set, construct redirect"
  - "Module-level singleton for lazy import in product_affiliate function body"

requirements-completed: [AFFL-01, AFFL-02, AFFL-03]

duration: 5min
completed: 2026-03-25
---

# Phase 6 Plan 02: SkimlinksLinkWrapper Service Implementation

**SkimlinksLinkWrapper service with go.skimresources.com URL wrapping, 21-domain exclusion set, three-tier domain cache (memory/Redis/API), and OAuth2 auth**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-25T23:59:30Z
- **Completed:** 2026-03-26T00:04:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added 6 SKIMLINKS_* config fields to Settings (ENABLED, PUBLISHER_ID, DOMAIN_ID, CLIENT_ID, CLIENT_SECRET, DOMAIN_CACHE_TTL)
- Created SkimlinksLinkWrapper with wrap_url(), _get_merchant_domains(), _fetch_domains_from_api(), _get_access_token()
- All 11 RED tests from Plan 01 now pass GREEN
- Module-level singleton `skimlinks_wrapper` ready for import by product_affiliate.py

## Task Commits

1. **Task 1: Add Skimlinks settings to config.py** - config changes included in `0b007d9`
2. **Task 2: Create SkimlinksLinkWrapper service** - `0b007d9` (feat)

## Files Created/Modified
- `backend/app/core/config.py` - 6 new SKIMLINKS_* fields after CJ settings block
- `backend/app/services/affiliate/skimlinks.py` - SkimlinksLinkWrapper service class (171 lines)

## Decisions Made
- Used go.skimresources.com (not go.redirectingat.com) as the canonical link wrapper base per official API docs
- Graceful degradation: auth failure returns empty domain set, Redis failure logs warning but does not crash
- Feature flag reads from settings at __init__ time (self.enabled) for test mockability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - SKIMLINKS_API_ENABLED defaults to False. When Skimlinks publisher approval is received, set the following env vars on Railway:
- `SKIMLINKS_API_ENABLED=true`
- `SKIMLINKS_PUBLISHER_ID` (numeric, from Publisher Hub)
- `SKIMLINKS_DOMAIN_ID` (numeric, from Publisher Hub)
- `SKIMLINKS_CLIENT_ID` (from Publisher Hub API settings)
- `SKIMLINKS_CLIENT_SECRET` (from Publisher Hub API settings)

## Next Phase Readiness
- Service ready for wiring into product_affiliate.py in Plan 03
- All 11 tests pass; module exports verified

---
*Phase: 06-skimlinks-link-wrapper*
*Completed: 2026-03-25*
