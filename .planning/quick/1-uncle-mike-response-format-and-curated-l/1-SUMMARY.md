---
phase: quick
plan: 1
subsystem: backend
tags: [product-compose, product-affiliate, response-format, affiliate-links, feature-flag]
dependency_graph:
  requires: []
  provides: [USE_CURATED_LINKS flag, Uncle Mike response format, curated-only affiliate mode]
  affects: [backend/mcp_server/tools/product_affiliate.py, backend/mcp_server/tools/product_compose.py, backend/app/core/config.py]
tech_stack:
  added: []
  patterns: [feature-flag via pydantic-settings, curated-only early return, response format enforcement via system prompt]
key_files:
  created: []
  modified:
    - backend/app/core/config.py
    - backend/.env
    - backend/mcp_server/tools/product_affiliate.py
    - backend/mcp_server/tools/product_compose.py
decisions:
  - USE_CURATED_LINKS defaults to True — curated amzn.to links (tag mikejahshan-20) are used as sole product source until PA-API access is granted
  - blog_article word limit raised from 350 to 400 to accommodate mandatory follow-up questions section
  - Concierge product listing cap changed from 8 to 5 to match product card cap
metrics:
  duration: ~2 minutes
  completed: 2026-03-25
  tasks_completed: 2
  files_changed: 4
---

# Quick Task 1: Uncle Mike Response Format and Curated Links Summary

**One-liner:** Enforced Blog Review -> Product Cards (max 5) -> Follow-up Questions format and added USE_CURATED_LINKS=true flag so curated amzn.to links bypass live API searches as the sole product source.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add USE_CURATED_LINKS flag and curated-only early return | 9420fb2 | config.py, product_affiliate.py |
| 2 | Enforce Uncle Mike response format in product_compose | 72ae453 | product_compose.py |

## What Was Built

### Task 1: USE_CURATED_LINKS Feature Flag

**backend/app/core/config.py** — Added `USE_CURATED_LINKS: bool = Field(default=True)` after `USE_MOCK_AFFILIATE`. When `True`, product_affiliate skips all live API calls and returns only matched curated amzn.to links.

**backend/.env** — Added `USE_CURATED_LINKS=true` (file is gitignored, updated locally).

**backend/mcp_server/tools/product_affiliate.py** — Added curated-only early return block at line ~115. When `curated_amazon_links and settings.USE_CURATED_LINKS`, the function:
- Maps each product name to a curated link dict (url, title, price, image_url, asin)
- Returns `{"affiliate_products": {"amazon": results}}` with results capped at 5
- Logs: `USE_CURATED_LINKS=true: returning N curated Amazon links (skipping live APIs)`
- Also capped the existing live-API curated supplement path at `min(len(curated_amazon_links), 5)`

The existing live API + curated supplement behavior is fully preserved when `USE_CURATED_LINKS=false`.

### Task 2: Uncle Mike Response Format

**backend/mcp_server/tools/product_compose.py** — Four changes:

1. **blog_article system prompt** — Replaced with structured two-section format:
   - SECTION 1: Blog Review (3-5 paragraphs with reviewer citations)
   - SECTION 2: Follow-up Questions (MANDATORY — 3 specific questions after the review)
   - Word limit raised to 400, follow-up questions explicitly marked as REQUIRED

2. **concierge system prompt** — Updated to require 2-3 specific follow-up questions at end (product-specific, not generic)

3. **Product review card cap** — Added `if review_card_count >= 5: break` at top of the `for idx, product in enumerate(products_with_offers, 1):` loop

4. **Concierge product list cap** — Changed `product_idx >= 8` to `product_idx >= 5`

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: backend/app/core/config.py (USE_CURATED_LINKS field at line 262)
- FOUND: backend/.env (USE_CURATED_LINKS=true at line 31, gitignored)
- FOUND: backend/mcp_server/tools/product_affiliate.py (curated-only block at line 115)
- FOUND: backend/mcp_server/tools/product_compose.py (blog_article prompt, concierge prompt, card cap, list cap)
- FOUND: commit 9420fb2 (Task 1)
- FOUND: commit 72ae453 (Task 2)
