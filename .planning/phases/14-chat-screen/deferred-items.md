# Deferred Items — Phase 14 Chat Screen

## Pre-existing Test Failures (Out of Scope)

Discovered during Plan 03 full test suite run. These failures existed before Plan 03 changes.

### 1. tests/chatApi.test.ts — retries on network error with exponential backoff
- **Status:** Pre-existing failure
- **Cause:** Unrelated to Phase 14 changes (chatApi retry logic)

### 2. tests/explainabilityPanel.test.tsx (3 tests)
- shows "Low confidence" badge when confidence_score is 0.5 (< 0.6)
- shows "Low confidence" badge when confidence_score is 0.3
- shows the confidence score as a percentage when expanded
- **Status:** Pre-existing failures
- **Cause:** Unrelated to Phase 14 changes (ExplainabilityPanel component)

## Pre-existing TypeScript Errors (Out of Scope)

### components/discover/TrendingCards.tsx
- LucideIcon type incompatibility errors (pre-existing)
