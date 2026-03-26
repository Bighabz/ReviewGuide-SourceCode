---
phase: 07-skimlinks-middleware-editors-picks
plan: 02
subsystem: backend
tags: [skimlinks, middleware, product-affiliate, affiliate]
dependency_graph:
  requires: [07-01-PLAN.md, 06-02-PLAN.md, 06-03-PLAN.md]
  provides: [_apply_skimlinks_wrapping function]
  affects: [product_affiliate.py, test_skimlinks.py]
tech_stack:
  added: []
  patterns: [extracted middleware function, module-level lazy import, is_supported_domain per-URL check]
key_files:
  created: []
  modified:
    - backend/mcp_server/tools/product_affiliate.py
    - backend/tests/test_skimlinks.py
    - backend/tests/test_skimlinks_middleware.py
decisions:
  - "Module-level lazy import of skimlinks_wrapper with ImportError fallback -- enables patching in tests"
  - "is_supported_domain check per URL for fine-grained wrapping control (not provider-level skip)"
  - "Updated Phase 6 integration tests to patch mcp_server.tools.product_affiliate.skimlinks_wrapper instead of app.services.affiliate.skimlinks.skimlinks_wrapper"
metrics:
  duration: 4min
  completed: "2026-03-26T00:10:00Z"
---

# Phase 7 Plan 02: Backend Skimlinks Post-Processing Middleware Summary

Extracted _apply_skimlinks_wrapping as a standalone async function in product_affiliate.py -- enables middleware-style post-processing of all provider results without touching any individual provider.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add _apply_skimlinks_wrapping function and wire into product_affiliate | 9bbecc8 | product_affiliate.py, test_skimlinks.py, test_skimlinks_middleware.py |

## Implementation Notes

**Phase 6 already had inline Skimlinks wrapping** at lines 283-302 of product_affiliate.py. This plan extracted that logic into a standalone `_apply_skimlinks_wrapping()` async function that:

1. Imports `skimlinks_wrapper` at module level (with ImportError fallback)
2. Uses `is_supported_domain()` to check each URL individually
3. Sets `offer["skimlinks_wrapped"] = True` on wrapped offers
4. Catches all exceptions non-fatally -- original URLs preserved on failure
5. Is called in BOTH return paths: main provider pipeline and curated-links-only early return

**Test fix required:** Phase 6 integration tests in test_skimlinks.py were patching `app.services.affiliate.skimlinks.skimlinks_wrapper` which no longer affects the function. Updated all 4 integration tests to patch `mcp_server.tools.product_affiliate.skimlinks_wrapper` and `mcp_server.tools.product_affiliate.settings`.

## Verification

- 4/4 AFFL-04 middleware tests pass
- 15/15 Phase 6 Skimlinks tests pass (no regression)
- 2/2 existing product_affiliate tests pass
- `grep -ri "skimlinks" backend/app/services/affiliate/providers/` returns 0 code matches

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Phase 6 integration test mock paths**
- **Found during:** Task 1 verification
- **Issue:** Phase 6 test_skimlinks.py integration tests patched `app.services.affiliate.skimlinks.skimlinks_wrapper` but the refactored function now uses module-level import at `mcp_server.tools.product_affiliate.skimlinks_wrapper`
- **Fix:** Updated all 4 TestProductAffiliateIntegration tests to patch the correct module-level names
- **Files modified:** backend/tests/test_skimlinks.py
- **Commit:** 9bbecc8

**2. [Rule 1 - Bug] Fixed false positive in test_no_provider_modifications**
- **Found during:** Task 1 verification
- **Issue:** serper_shopping_provider.py contains "Skimlinks" in a comment referencing Phase 6, which triggered a false positive
- **Fix:** Changed test to check only non-comment code lines for Skimlinks references
- **Files modified:** backend/tests/test_skimlinks_middleware.py
- **Commit:** 9bbecc8
