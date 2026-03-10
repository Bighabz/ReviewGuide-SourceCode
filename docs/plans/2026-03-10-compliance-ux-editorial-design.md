# ReviewGuide.ai — Compliance, UX Fixes & Editorial Restyling

**Date:** 2026-03-10
**Status:** Approved
**Approach:** A (Frontend-only editorial restyling for blog-style results)

---

## Context

Affiliate program approvals (Amazon API, Walmart, Best Buy, Home Depot) are blocked by missing legal/compliance pages and incomplete disclosure placement. Several UX bugs need fixing, and product results need editorial restyling to feel more like blog articles.

## Scope

### Workstream 1: Legal & Compliance (P0 — Blocking Affiliate Approvals)

#### 1A. Terms of Service Page
- **Action:** Create new `/terms` page
- **File:** `frontend/app/terms/page.tsx`
- **Content:** Standard ToS covering: acceptance of terms, service description (AI-powered product research), user responsibilities, intellectual property, disclaimers (AI-generated content), limitation of liability, governing law, changes to terms, contact info
- **Style:** Match existing `/privacy` page layout (max-w-3xl, editorial headings, back-to-browse link)

#### 1B. Update Affiliate Disclosure Page
- **Action:** Update existing `/affiliate-disclosure` page to match exact stakeholder-provided language
- **File:** `frontend/app/affiliate-disclosure/page.tsx`
- **Changes:**
  - Add explicit Amazon Associates line: "As an Amazon Associate, we earn from qualifying purchases."
  - Add: "Affiliate partnerships do not influence our analysis, opinions, or product evaluations."
  - Keep contact info

#### 1C. Update Privacy Policy
- **Action:** Minor updates to existing `/privacy` page
- **File:** `frontend/app/privacy/page.tsx`
- **Changes:** Update effective date, ensure content is current

#### 1D. Global Footer Component
- **Action:** Create `Footer.tsx`, render in root `layout.tsx`
- **File:** `frontend/components/Footer.tsx`
- **Structure:**
  ```
  ┌─────────────────────────────────────────────────┐
  │  ReviewGuide.ai          Legal        Connect   │
  │  AI-powered product      Privacy      Email     │
  │  research & reviews      Terms        (future)  │
  │                          Affiliate              │
  │                          Disclosure             │
  │─────────────────────────────────────────────────│
  │  Affiliate Disclosure (prominent text)          │
  │  "ReviewGuide.ai participates in affiliate      │
  │  marketing programs including Amazon Associates.│
  │  We may earn commissions at no cost to you."    │
  │─────────────────────────────────────────────────│
  │  © 2026 ReviewGuide.ai. All rights reserved.    │
  └─────────────────────────────────────────────────┘
  ```
- **Styling:** Editorial theme (Instrument Serif headings, warm palette, responsive)
- **Placement:** Root `layout.tsx` so it appears on every page
- **Interaction with existing layouts:** BrowseLayout and chat page have their own structure; footer renders below `{children}` in root layout. On chat page, footer is below the chat container (user scrolls to it, does not interfere with sticky input bar).

#### 1E. Inline Affiliate Disclosure (Tier 3)
- **Action:** Add short disclosure near affiliate link components
- **Text:** "Disclosure: We may earn commissions from qualifying purchases."
- **Components to update:**
  - `ProductCards.tsx` — below the cards grid
  - `ProductCarousel.tsx` — below the carousel
  - `AffiliateLinks.tsx` — below the links grid
  - `PriceComparison` block (in BlockRegistry) — below comparison table
- **Style:** `text-xs text-[var(--text-muted)]`, clearly readable, not hidden

---

### Workstream 2: UX Bug Fixes (P1)

#### 2A. Submit Arrow Button
- **Current state:** `ChatInput.tsx` line 80 has `onClick={onSend}`, disabled when `isStreaming` or empty input
- **Investigation:** Check if `handleSendMessage` in ChatContainer has guards that prevent execution. Check if `isStreaming` state gets stuck. Test on mobile (tap events vs click events).
- **File:** `frontend/components/ChatInput.tsx`, `frontend/components/ChatContainer.tsx`

#### 2B. Remove "Results may be incomplete"
- **Action:** Remove the trigger text from `ExplainabilityPanel.tsx`
- **File:** `frontend/components/ExplainabilityPanel.tsx` line 63
- **Approach:** Remove the clickable "Results may be incomplete" link and the expandable panel entirely

#### 2C. Mobile Horizontal Scrolling
- **Current state:** `globals.css` has `overflow-x: hidden` on body, viewport meta is correct
- **Investigation:** Check specific components for width overflow — likely candidates:
  - `UnifiedTopbar.tsx` (mobile nav pills, search bar)
  - `ChatContainer.tsx` (message bubbles with wide content)
  - Product block renderers (carousels, comparison tables)
  - `ComparisonTable` raw HTML (inline CSS may not be responsive)
- **Fix:** Add `overflow-x: hidden` or `max-w-full` to offending containers, ensure all block renderers respect viewport width

---

### Workstream 3: Chat Name Memory

#### 3A. Verify Conversation History Flow
- **Current state:** `general_compose.py` line 85 tells LLM "you remember everything the user has told you — their name, preferences" and passes last 10 messages
- **Issue:** LLM may not reliably extract names from history, or history may not include the message where the name was mentioned
- **Investigation:**
  1. Verify `conversation_history` in GraphState includes all messages (not truncated too early)
  2. Check if compose tools consistently receive history
  3. Test: say "My name is John" → follow up → does the LLM use the name?
- **Fix options:**
  - If history is passed correctly: may just be LLM inconsistency, reinforce system prompt
  - If history is truncated: increase window or add explicit name extraction to a `user_context` field in GraphState

---

### Workstream 4: Editorial Restyling of Product Results (Approach A)

#### 4A. ProductCards.tsx — Editorial Makeover
- **Current:** Grid of cards with rank badges, merchant tags, price, pros/cons bullets, "View Deal" CTA
- **New style:**
  - Numbered sections with `font-serif` headings (e.g., "1. iRobot Roomba j9+")
  - Editorial label as subtitle ("Best Overall" / "Budget Pick")
  - Pros/cons as flowing sentence fragments, not bullet grids
  - Prominent "Check price on Amazon →" CTA with affiliate link
  - Warmer card background, more whitespace
- **File:** `frontend/components/ProductCards.tsx`

#### 4B. ProductCarousel.tsx — Editorial Cards
- **Current:** Horizontal scroll of compact cards with image, title, price
- **New style:**
  - Larger card with more image space
  - Merchant badge + editorial label
  - Price prominent with "View on [Merchant]" link
  - Comfortable spacing
- **File:** `frontend/components/ProductCarousel.tsx`

#### 4C. AffiliateLinks.tsx — Cleaner Layout
- **Current:** Bordered card with grid of retailer links
- **New style:**
  - "Where to buy" section heading
  - Retailer rows with price, rating, and CTA
  - Less boxy, more editorial
- **File:** `frontend/components/AffiliateLinks.tsx`

#### 4D. Article-Like Message Container
- **Current:** Messages rendered as chat bubbles
- **New style for assistant product messages:**
  - Wrap product-related messages in an article container
  - `font-serif` headings, comfortable `leading-relaxed` line spacing
  - Editorial separator lines between sections
- **File:** `frontend/components/Message.tsx` (container styling only, do NOT modify ui_blocks logic)

---

### Workstream 5: Product/Price Matching Fix

#### 5A. Investigate Price Comparison Accuracy
- **Current:** `product_compose.py` uses Jaccard similarity (threshold 0.35) to match same products across retailers
- **Issue:** Products may not match correctly if names differ significantly between retailers
- **Investigation:** Review fuzzy matching logic, check if threshold is too low/high, test with real product names
- **File:** `backend/mcp_server/tools/product_compose.py` lines 61-69, 105-139

---

### Deferred (Not in this iteration)

| Item | Status | Reason |
|------|--------|--------|
| CJ API integration | Code exists, `CJ_API_ENABLED=False` | Needs API keys + testing |
| Full blog-style backend (Approach C) | Deferred | Try Approach A first |
| Streaming/typewriter effect | Already works via SSE | P3, acceptable as-is |
| Review links rework | Deferred | P2, needs separate design |

---

## Files Affected

### New Files
- `frontend/app/terms/page.tsx`
- `frontend/components/Footer.tsx`

### Modified Files
- `frontend/app/layout.tsx` (add Footer)
- `frontend/app/affiliate-disclosure/page.tsx` (update language)
- `frontend/app/privacy/page.tsx` (update date)
- `frontend/components/ProductCards.tsx` (editorial restyle + Tier 3 disclosure)
- `frontend/components/ProductCarousel.tsx` (editorial restyle + Tier 3 disclosure)
- `frontend/components/AffiliateLinks.tsx` (editorial restyle + Tier 3 disclosure)
- `frontend/components/Message.tsx` (article container styling only)
- `frontend/components/ExplainabilityPanel.tsx` (remove "Results may be incomplete")
- `frontend/components/ChatInput.tsx` (fix submit button if needed)
- `frontend/components/ChatContainer.tsx` (remove inline footer disclosure — moved to global Footer)
- `frontend/components/blocks/BlockRegistry.tsx` (add Tier 3 disclosure to price_comparison)
- `frontend/app/globals.css` (mobile overflow fixes if needed)
- `backend/mcp_server/tools/general_compose.py` (strengthen name memory prompt if needed)

---

## Success Criteria

1. All three legal pages accessible and linked from footer
2. Affiliate disclosure visible in three tiers (footer link, full page, inline near products)
3. No horizontal scrolling on mobile
4. Submit button works on desktop and mobile
5. "Results may be incomplete" message removed
6. Product results have editorial blog-like styling
7. Chat remembers user's name within a session
