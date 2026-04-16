# ReviewGuide.ai — Full-Site QA Audit & Strategic Recommendations

## For: Claude Opus 4.7 (or latest frontier model)
## Date: 2026-04-16
## Branch: `v2-with-swipe` (deployed to production as `main`)

---

## Context for the Auditor

You are a senior staff engineer and UX auditor performing a comprehensive QA pass on **ReviewGuide.ai** — an AI-powered shopping and travel assistant. The site returns editorial blog-style responses with product cards, affiliate links, travel itineraries, and review citations. It monetizes through affiliate commissions (Amazon, eBay, Skimlinks, Booking.com, Expedia, Viator).

**The current production build is based on v2.0 (the "Editorial Luxury" frontend redesign)** with cherry-picked improvements:
- AI-generated product/travel images (38 WebP files)
- Backend bug fixes (product_compose fallback loop, multi-provider gating, label-domain parity, accessory suppression, budget enforcement, travel timeout recovery)
- Scroll fix (flex height chain)
- Product card fallback images (keyword-matched)
- **NEW: Swipeable product review carousel** (touch swipe + snap scroll + dots)

**We explicitly chose v2.0 over v3.0 ("Bold Editorial")** because the stakeholder (Mike) preferred the cleaner, warmer v2.0 aesthetic over v3.0's bold accent colors, spring-physics card animations, and aggressive typography changes. The v3.0 work is preserved on the `v3-backup` branch but is NOT deployed.

**Your job is to audit what's live, find every issue, and recommend what to build next.**

---

## Your MCP Toolbox

You have access to these Chrome browser automation tools via the `claude-in-chrome` MCP server. Use them aggressively — don't just describe what you'd check, actually check it.

### Tab & Navigation
| Tool | Purpose |
|------|---------|
| `tabs_context_mcp` | **Call first.** Get all open tab IDs in the MCP group |
| `tabs_create_mcp` | Create a new tab in the MCP group |
| `navigate` | Navigate a tab to a URL, or go forward/back |
| `resize_window` | Resize browser window (for responsive testing) |

### Visual Inspection
| Tool | Purpose |
|------|---------|
| `computer` (action: screenshot) | Take full-viewport screenshot of a tab |
| `computer` (action: zoom) | Zoom into a specific region `[x0, y0, x1, y1]` for pixel-level inspection |
| `computer` (action: scroll) | Scroll up/down/left/right at specific coordinates |
| `computer` (action: hover) | Hover over elements to check hover states |

### Interaction
| Tool | Purpose |
|------|---------|
| `computer` (action: left_click) | Click on elements |
| `computer` (action: type) | Type text into focused inputs |
| `computer` (action: key) | Press keyboard keys (Enter, Tab, Escape, etc.) |
| `computer` (action: left_click_drag) | Drag elements (test swipe gestures on desktop) |
| `find` | Find elements by natural language description ("search bar", "submit button") |
| `form_input` | Set form values using accessibility ref IDs |
| `read_page` | Get accessibility tree — all elements with ref IDs, or filter to interactive only |

### Data & Debugging
| Tool | Purpose |
|------|---------|
| `javascript_tool` | Execute JS in page context — measure DOM dimensions, computed styles, check state |
| `read_console_messages` | Read browser console (errors, warnings, app logs). Always use `pattern` filter |
| `read_network_requests` | Monitor HTTP requests (API calls, image loads, SSE streams). Use `urlPattern` filter |
| `get_page_text` | Extract all text content from the page |

### Recording
| Tool | Purpose |
|------|---------|
| `gif_creator` (start/stop/export) | Record browser interactions as animated GIF for bug reports |

---

## Test Plan — Execute All Sections

### Phase 0: Setup (2 minutes)

1. Call `tabs_context_mcp` to get current tab state
2. Create 2 tabs: one for desktop (1440×900), one for mobile (390×844 — iPhone 14 Pro)
3. Use `resize_window` to set viewport sizes
4. Navigate both to `https://www.reviewguide.ai`
5. Check `read_console_messages` with pattern `error|Error|ERR` on both — log any startup errors

---

### Phase 1: Homepage / Discover Screen (10 minutes)

**On both viewports:**

1. **Screenshot** the full homepage on desktop and mobile
2. **Visual inspection:**
   - Is the search bar visible and centered?
   - Are category chips rendered with readable text?
   - Are trending cards visible with thumbnails?
   - Is the product carousel rendering all 5 slides? (Use `javascript_tool` to check `document.querySelectorAll('[class*="slide"]').length` or inspect the SLIDES array)
   - Do mosaic hero images load? (Check with `javascript_tool`: query all `img[src*="mosaic"]` and verify `naturalWidth > 0`)
3. **Carousel interaction:**
   - Click the right arrow — does it advance?
   - Click dots — does it jump to the correct slide?
   - On mobile: simulate swipe with `left_click_drag` from right to left — does it advance?
   - Does auto-rotation work? (Wait 5 seconds, screenshot, check if slide changed)
   - Verify all 5 slides render distinct content (not duplicates) — screenshot each
4. **Carousel content audit:**
   - Zoom into each card — check badge text, score, subtitle, CTA link
   - Verify "Research →" is a proper `<a>` tag (use `read_page` and check for `href`)
   - Verify no prices on roundup/comparison cards (headphones, laptops, shoes should NOT have prices)
   - Verify Tokyo card says "GUIDE" not "TRENDING", score is "4.8 Editor Rating"
5. **Image 404 check:**
   - Use `read_network_requests` with `urlPattern: "images"` — look for any 404 status codes
   - Use `javascript_tool` to check all images on page: `[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)`
6. **Category chips:**
   - Click a category chip — does it navigate to `/chat?q=...`?
   - Click a trending card — same check
7. **Navigation:**
   - Desktop: verify UnifiedTopbar shows (ReviewGuide logo, Discover, Saved, Ask, Compare, Profile, search bar, New Chat)
   - Mobile: verify MobileHeader shows, MobileTabBar at bottom with 5 tabs
   - Click "Ask" / central tab — navigates to `/chat?new=1`?

---

### Phase 2: Chat — Product Query (15 minutes)

**Test query: "best wireless earbuds under $100"**

1. Navigate to `/chat` on both viewports
2. Type the query and submit
3. **During streaming:**
   - Screenshot while streaming — is there a loading/thinking indicator?
   - Can you scroll up while streaming? (Use `computer` action: scroll up)
   - Does the auto-scroll follow new content?
   - Check `read_network_requests` with `urlPattern: "stream"` — verify SSE connection established
4. **After response completes:**
   - Screenshot the full response on both viewports
   - **Product review carousel (NEW FEATURE — critical test):**
     - Are product cards grouped in a swipeable carousel?
     - Is there a "1 of N products" counter?
     - Are dot indicators visible?
     - On desktop: do arrow buttons appear? Click next/prev — does it work?
     - On mobile: swipe left with `left_click_drag` — does the next card snap into view?
     - Zoom into each product card: does it have an image (real or fallback)?
   - **Top Pick block:**
     - Is there a "Our Top Pick" featured card?
     - Does it have an image (real or fallback)?
     - Is the CTA clickable and links to an affiliate URL?
   - **Blog narrative:**
     - Is there editorial text with review citations (RTINGS, Tom's Guide, CNET)?
     - Are citation links clickable? (`read_page` filter: interactive, check for `<a>` tags with external hrefs)
   - **Source citations section:**
     - Are colored dots visible?
     - Are source links clickable?
   - **Follow-up suggestions:**
     - Are suggestion chips visible below the response?
     - Click one — does it send as a follow-up message?
5. **Scroll behavior:**
   - Scroll to the very top — is the first message (user's question) fully visible above the header?
   - On mobile: is there adequate padding-top so content isn't hidden behind the fixed MobileHeader?
   - Scroll to the bottom — is the input visible and not cut off?
6. **Affiliate links:**
   - Click a "Check price on Amazon" or similar CTA
   - Verify the URL contains the affiliate tag (`revguide-20` for Amazon, appropriate tags for eBay)
   - Verify the link opens in a new tab
   - Check for label-domain parity: Amazon-labeled links go to amazon.com, eBay to ebay.com
7. **Console errors:**
   - `read_console_messages` with pattern `error|Error|ERR|fail|undefined` — log everything

---

### Phase 3: Chat — Travel Query (10 minutes)

**Test query: "Top all-inclusive resorts in the Caribbean"**

1. Send the query on mobile viewport
2. **During streaming:**
   - Screenshot — what status text appears?
   - Does it show tool-specific updates ("Searching for hotels...", "Building itinerary...")?
3. **After response completes:**
   - Screenshot the full response
   - **Hotel widget card:**
     - Does it have a hero image (travel-themed, not empty placeholder)?
     - Does CTA say "Search on Expedia" (not "Search Properties")?
     - Is "Powered by Expedia" badge small and subtle?
     - Does "Caribbean" text wrap correctly (not "Caribb ean")?
   - **Flight widget card:**
     - Same checks as hotel widget
     - On mobile: are hotel and flight cards stacked vertically (not side-by-side)?
   - **Resort/attractions section:**
     - Are resorts rendered as cards (not a flat bullet list with pin icons)?
     - Do resort cards have images?
     - Is there a card-based layout (not just text)?
   - **Spacing and typography:**
     - Are section headers sans-serif (not decorative serif)?
     - Is there consistent spacing between sections?
     - Is the "Want better results?" conclusion styled with a tinted background?
4. **Dark mode:**
   - Toggle dark mode (if available in settings)
   - Screenshot — are all travel components visible? No white text on white background?

---

### Phase 4: Chat — Edge Cases (5 minutes)

1. **Empty state:** Navigate to `/chat?new=1` — verify welcome screen shows with suggestions
2. **Rapid messages:** Send a message, then immediately try sending another while streaming — what happens? (Should show queued notice or "please wait", not silently drop)
3. **Long response scrollback:** After a long response, scroll to top, then click "Jump to latest" button — does it work?
4. **New chat:** Click "New Chat" button — does it clear the conversation and show welcome screen?
5. **Browser back/forward:** After navigating to chat, press browser back — where does it go? Forward — does it return?

---

### Phase 5: Browse Pages (5 minutes)

1. Navigate to a browse category: `https://www.reviewguide.ai/browse/headphones`
2. **Screenshot** on both viewports
3. **Category hero:**
   - Does it have a background image (AI-generated WebP)?
   - Is text readable over the image (gradient overlay)?
4. **Editor's Picks:**
   - Are Editor's Picks cards visible?
   - Do they have images?
   - Do affiliate links work?
5. **Navigation between categories:**
   - Click a different category in the sidebar — does it load?
6. **404 page:**
   - Navigate to `https://www.reviewguide.ai/nonexistent-page`
   - Does a styled 404 page appear (not the raw Next.js default)?

---

### Phase 6: Cross-Cutting Concerns (5 minutes)

1. **Dark mode toggle:**
   - Find and toggle dark mode
   - Screenshot homepage, chat, and browse in dark mode
   - Check for any invisible text, broken contrast, or white flashes
2. **Performance:**
   - Use `javascript_tool` to measure: `performance.getEntriesByType('navigation')[0].loadEventEnd`
   - Check LCP: `new PerformanceObserver(l => console.log('LCP:', l.getEntries().at(-1))).observe({type: 'largest-contentful-paint', buffered: true})`
3. **Responsive breakpoints:**
   - Resize to 768px width (tablet) — does layout adjust correctly?
   - Resize to 1024px — does desktop layout kick in?
4. **Accessibility:**
   - Use `read_page` with filter: "all" — check for images missing alt text
   - Check color contrast on key text elements using `javascript_tool` + computed styles
5. **Console health:**
   - Final `read_console_messages` with pattern `error|warn` — compile all issues

---

## Deliverable Format

After completing all phases, produce a structured report:

```markdown
# ReviewGuide.ai — Full Audit Report
**Date:** [date]
**Branch:** v2-with-swipe
**Auditor:** Claude Opus 4.7

## Executive Summary
[3-5 sentence overview: what works well, what's broken, overall quality assessment]

## Critical Issues (P0 — fix before any new feature work)
| # | Issue | Page | Viewport | Evidence |
|---|-------|------|----------|----------|
| 1 | [description] | [page] | [mobile/desktop/both] | [screenshot ID or measurement] |

## Major Issues (P1 — fix this sprint)
[same table format]

## Minor Issues (P2 — fix when convenient)
[same table format]

## Visual Polish (P3 — nice to have)
[same table format]

## What Works Well
[bullet list of things that are solid and should NOT be changed]

## Strategic Recommendations
### Immediate (next 2 weeks)
[what to build/fix next, in priority order]

### Short-term (next month)
[features and improvements]

### Medium-term (next quarter)
[bigger bets and architectural changes]

## v2.0 vs v3.0 Assessment
[Your professional opinion on the v2.0 aesthetic vs the v3.0 "Bold Editorial" direction.
What specifically works better about v2.0? What was v3.0 getting right that v2.0 lacks?
Recommendations for a potential v2.5 that takes the best of both.]

## Swipe Carousel Assessment
[Detailed feedback on the new product review carousel: UX, performance, edge cases,
mobile feel, desktop behavior, what to improve]

## Appendix: Test Evidence
[List of all screenshots taken with IDs, console errors found, network issues detected]
```

---

## Important Notes

- **Do NOT skip any section.** Execute every test, take every screenshot, measure every dimension.
- **Use `javascript_tool` liberally** — measure actual computed values, don't guess from screenshots.
- **Record GIFs** of the swipe carousel interaction on both mobile and desktop using `gif_creator`.
- **Be brutally honest.** This audit determines what gets built next. Sugarcoating wastes everyone's time.
- **Compare against best-in-class:** Airbnb, Google Shopping, Wirecutter, The Verge product pages. Where does ReviewGuide fall short?
- **The stakeholder (Mike) chose v2.0 over v3.0.** Respect that decision but give your honest professional opinion on the tradeoffs.
