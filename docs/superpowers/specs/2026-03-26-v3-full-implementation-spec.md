# ReviewGuide.ai v3 — Full Implementation Spec

**Date:** 2026-03-26
**Status:** Approved by user
**Source:** User audit + Chrome MCP live site review + competitive analysis (Amazon, Best Buy, RTINGS)

---

## Bug Report (from live site audit)

### Critical Bugs
- **Streaming not working end-to-end:** "Thinking..." for 3-10s, then entire response dumps at once. Zero token-by-token streaming visible to user.
- **Wrong prices:** Sony WH-1000XM5 listed at $44.99, Bose 700 at $44.99, Sennheiser at $35.99. These are $300+ headphones. Likely pulling eBay used/parts prices.
- **Raw markdown leaking:** Product descriptions show literal "# Bose Noise Cancelling Headphones 700" and "# TOZO NC9 Editorial Summary" with hash characters rendered as text.
- **Incomplete product cards:** Last 2 products (Sennheiser, Jabra) have no image, no summary, no rating, no pros. Just a buy link. Looks broken.
- **History panel broken:** Shows "0 conversations" and "Loading..." even after chatting.
- **CJ API deprecated:** Returning 404s. Already disabled.

### UX Bugs
- **Two-line message bubble:** "Best wireless earbuds under / $100" wraps unnecessarily. Bubble max-width too narrow.
- **Top Pick card has no buy link:** No price, no rating, no buy button. Must scroll 3+ times to reach "Where to Buy."
- **Product appears twice:** Top Pick summary card + identical detailed card immediately below for same product.
- **Truncated product names:** "Amazon - Bose Noise Cancellin..." cut off in buy cards.
- **Inconsistent buy cards:** Some show price, some show "Check price →", some eBay cards have seller ratings, some don't.
- **No cons in product cards:** Only pros listed. Zero criticism anywhere.
- **Source colored dots meaningless:** Random colors with no legend.
- **Generic follow-up questions:** Not tailored to specific query.
- **Homepage has no sidebar:** Great sidebar only on chat page, not homepage.
- **Category pills redundant:** Homepage shows pills AND trending cards, but real categories in hidden sidebar.
- **Hover states invisible:** Sidebar items, trending cards, buy links have barely perceptible hover effects.
- **Accent color picker only changes link color:** No immersive theme change.
- **Footer bland and wastes space.**
- **Response too long:** 2000-word magazine article in a chat bubble. Tone mismatch.
- **Only Amazon links:** No multi-retailer despite claiming "price comparison."
- **Footer cut off by sidebar on smaller viewports:** Responsive layout bug.
- **Search bar + chat input overlap:** Two places to type, unclear which to use.

---

## Section 1: STREAMING RESPONSES — REAL-TIME TOKEN DISPLAY (HIGHEST PRIORITY)

The #1 user complaint: responses appear all at once after a long "Thinking..." wait. This MUST be real-time streaming.

**Technical requirements:**
- Use Server-Sent Events (SSE) from the API backend to push tokens as they're generated
- On the frontend, subscribe to the SSE stream and append each token/chunk to the DOM in real-time
- Text should begin appearing within 200-500ms of the request being sent
- Use `EventSource` or `fetch()` with `ReadableStream` on the client
- Render markdown progressively — as markdown fragments arrive, parse and render them incrementally (use a streaming-compatible markdown renderer or buffer until a complete block is available)
- Auto-scroll the chat container to follow the latest content as it streams in
- Show a subtle blinking cursor or typing indicator at the end of the streaming text (like a terminal cursor)
- Product cards can render progressively: show a skeleton/shimmer placeholder first, then populate with data as it arrives
- The "Thinking..." state should show for NO MORE than 1 second before the first tokens appear — replace it with a pulsing dot animation or shimmer bar
- If the backend currently returns the full response as one payload, refactor it to use streaming (e.g., Claude API with `stream: true`, or your backend proxying the stream via SSE)
- Add a "Stop generating" button that appears during streaming, allowing users to cancel mid-response

**Why this matters:** Streaming makes a 10-second response FEEL like 1 second because the user starts reading immediately. This is the single biggest UX win possible.

**Backend context:** The backend DOES stream via SSE (graph.astream_events). Phase A-C eliminated 3 LLM calls and removed the 20ms artificial delay. But product_compose still makes 6+ LLM calls (opener, conclusion, review_consensus x3-5, blog_article) totaling ~24s. The fix: remove opener/conclusion calls (redundant), cap review_consensus to 3 products, and stream blog_article tokens directly to SSE as they generate from Haiku.

---

## Section 2: USER MESSAGE BUBBLE — FIX THE TWO-LINE WRAPPING BUG

When clicking a suggested query or trending topic, the user's message bubble wraps to two lines unnecessarily.

**Fix:**
- Increase the `max-width` of user message bubbles to at least `80%` of the chat container width (or `max-width: 560px` minimum)
- For short single-sentence queries, the bubble should fit on ONE line whenever the viewport allows
- Test with all suggested queries and trending topics to ensure none wrap unnecessarily
- The bubble should only wrap when the text genuinely exceeds the available width

---

## Section 3: PRODUCT CARD REDESIGN — BUY LINK ON TOP PICK, ELIMINATE DUPLICATION

**Problem:** The "OUR TOP PICK" card has no price, no rating, and no buy link. Below it, the same product appears AGAIN as a detailed card. Users must scroll through a wall of text + pros/cons + THEN find the "Where to Buy" section 3+ scrolls down.

**Fix — Unified Product Card:**
- MERGE the "Our Top Pick" summary card and the detailed review card into ONE unified card per product
- Every product card MUST include ALL of the following in a single view:
  - Product image (large — at least 140x140px) via Nano Banana MCP or real product photo
  - Product name (clickable link to retailer)
  - Star rating + numeric score (e.g., ★ 4.7/5)
  - Price with retailer name (e.g., "$44.99 on Amazon") — this should be a prominent button, not buried
  - Best for / Use case tag (1-line, e.g., "Best Overall" or "Best Budget")
  - 2-3 line summary (NOT a wall of text)
  - Expandable section for detailed pros/cons (collapsed by default, click to expand)
  - "Compare" and "Save" icon buttons on the card
- The buy link should be a COLORED BUTTON, not a plain text link (e.g., orange "Buy on Amazon — $44.99" button)
- If multiple retailers have the product, show a "lowest price" badge and a dropdown for other stores
- NO duplicate cards for the same product

**Fix — Markdown Rendering Bug:**
- Product card descriptions are showing raw markdown like "# Sony WH-1000XM5: The Gold Standard..." with the literal `#` hash character
- Strip or properly parse ALL markdown before rendering in product card text
- Check all product description fields for unrendered markdown artifacts (headers, bold markers, etc.)

**Fix — Truncated Product Names:**
- In "Where to Buy" cards, product names get truncated: "Amazon - Bose Noise Cancellin..."
- Ensure full product names are visible, or use proper ellipsis with a tooltip showing the full name
- Consider shorter format: just "Amazon" with the product name shown in the parent card

**Fix — Inconsistent Buy Cards:**
- Standardize all buy cards: every card shows retailer logo/name, price (or "Check price" if unavailable), and an external link icon
- Add visual hierarchy: highlight the lowest price option with a "Best Price" badge or green accent
- Remove inconsistent seller ratings that appear on some eBay listings but not others — either show them for ALL retailers or none

---

## Section 4: PRODUCT IMAGES VIA NANO BANANA MCP — EVERYWHERE

Every product mentioned MUST have a real, high-quality product image. Use Nano Banana MCP to:
- Fetch product images for ALL products in chat responses — no exceptions
- Display in unified product cards at 140x140px minimum
- Display in homepage catalog grid cards (see section 6)
- Display in trending topic cards on homepage (e.g., "Best Headphones 2026" should show headphones)
- If no image is found, show a styled category placeholder (headphone icon for audio, laptop icon for computers, etc.) — NEVER an empty/blank space
- Cache images aggressively for performance
- Support image carousel on product cards (some already have pagination dots — make this consistent)

**Image sourcing strategy (fallback chain):**
1. Real product photos from affiliate APIs (eBay, Serper Shopping, Amazon CDN via ASIN)
2. Serper Image Search by product name
3. Nano Banana MCP generated product imagery
4. Branded category placeholder icon (last resort, NEVER blank space)

---

## Section 5: THEME & COLOR OVERHAUL — RICH, IMMERSIVE, INTERACTIVE

The current site is too flat and lifeless. The accent color picker barely changes anything.

**Dark Mode (make this the default):**
- Background: rich dark (#0C0E14) with subtle blue-ish undertone — NOT flat black or gray
- Card surfaces: elevated dark (#151822) with thin border (#1C2233) and subtle box-shadow
- Accent: electric blue (#3B82F6) for links/CTAs + warm amber (#F59E0B) for ratings/prices
- Text: #E8EAED primary, #8892A4 secondary
- Add depth with layered backgrounds — sidebar slightly different shade from main content
- Subtle gradient on the hero/header area (dark gradient from top-left to bottom-right)
- Product cards: dark card surface with gentle glow effect on hover (box-shadow: 0 0 20px rgba(59,130,246,0.15))
- Buy buttons: vivid gradient button (blue-to-purple or orange-to-gold gradient)
- Rating stars: bright amber/gold (#F59E0B)
- Price text: green (#22C55E) for deal prices, white for regular
- Source links (RTINGS, Tom's Guide): show as colored chips/pills, not plain underlined text

**Light Mode:**
- NOT pure white — use warm cream (#F7F5F0) for background
- Cards: white (#FFFFFF) with warm shadow (tinted shadow like rgba(180,160,130,0.1))
- Accent colors remain vibrant
- More texture — subtle dot pattern or very faint gradient on the background

**Hover States & Micro-Interactions (critical for feeling alive):**
- Trending cards: hover lifts card (translateY(-2px)), deepens shadow, arrow icon slides right
- Sidebar items: full-width background highlight with accent tint, slight scale (1.01), icon pulses
- Product cards in chat: subtle glow border, slight lift
- Buy buttons: gradient shifts or button pulses on hover
- Source citations: tooltip preview with source name and favicon
- Navigation links: active bottom border accent, hover color transition
- ALL transitions: smooth 200-300ms ease-out
- Skeleton/shimmer loading for all async content
- Subtle page transition animation between views

**Accent Color Picker:**
- Extend to affect ENTIRE theme mood: button gradients, card glow color, sidebar highlights, hero gradient tint
- Consider themed names ("Ocean", "Sunset", "Neon", "Forest", "Berry")

---

## Section 6: HOMEPAGE REDESIGN — VISUAL PRODUCT CATALOG WITH SIDEBAR

**Remove category pill bubbles** from main content area — belong in sidebar.

**Add Left Sidebar to Homepage:**
- Same sidebar from chat page (Quick Searches + Categories)
- Each item has icon and item count badge (e.g., "Electronics (234)")
- Clicking category scrolls to or filters that section
- Collapsible on desktop, slide-out drawer on mobile

**Redesign Main Content Area:**
- Hero section: bolder heading, subtle animated gradient background or transitioning product silhouettes
- Below hero: scrollable product catalog by category:
  - Section headers: "Trending in Electronics", "Popular in Kitchen", etc.
  - Horizontally scrollable rows (4-5 visible, Netflix-style)
  - Each card: product IMAGE, name, star rating, price, one-line hook
  - Clickable — opens chat researching that product
  - "View All →" at end of each row
- Trending Research cards should have images too
- "Recently Viewed" row if user has history
- "Deals & Price Drops" row for products with price decreases

**Sticky Bottom Search Bar:**
- Pin "Ask anything" to bottom of viewport
- Float above content with backdrop blur and shadow
- Stays fixed as user scrolls catalog
- Focus expands input slightly, dims background
- Match chat page input behavior

---

## Section 7: ADDITIONAL MICRO-UX FIXES

**Chat Input Bar:**
- Border glow when focused (accent color)
- Microphone icon placeholder
- Attachment/image icon placeholder
- Send button: smooth color transition on hover, press animation

**Response Structure:**
- Start every response with 1-2 sentence bold summary, THEN detail
- Trim editorial intro to 1 short paragraph max before first product card
- "Want to dig deeper?" follow-ups as clickable chip buttons, not inline text

**Navigation:**
- "Saved" page: placeholder UI with empty state illustration
- "Compare" page: same treatment
- "Profile" link: proper placeholder or remove
- Chat history: sidebar panel showing past conversations

**Footer:**
- Either make useful (category links, "Top Searches", social links) or minimize to single compact line

**Mobile Bottom Nav:**
- Proper active state indicators
- "Ask" button visually prominent (larger, floating, accent-colored)

---

## Section 8: PERFORMANCE & POLISH

- Loading skeletons (shimmer) for ALL async content
- Lazy-load images on scroll
- Preload first few images per catalog row
- Smooth scroll behavior site-wide
- Respect `prefers-reduced-motion`
- Subtle click feedback (brief scale-down)
- Test on mobile (375px), tablet (768px), desktop (1280px+)

---

## Price Fix Strategy

The wrong prices ($44.99 for $300+ headphones) are coming from eBay used/parts listings. Fix:
1. Filter eBay results by condition: only "New" items, exclude "Used", "Parts", "Refurbished"
2. If curated Amazon link exists, prefer that price over eBay
3. Show price source: "From $299 on Amazon" not just "$299"
4. If price seems unrealistic (>80% below typical retail), flag or hide it

## Compose Pipeline Optimization

product_compose currently makes 6+ LLM calls totaling ~24s. Fix:
1. Remove product_opener LLM call (redundant with blog_article)
2. Remove product_conclusion LLM call (redundant)
3. Cap review_consensus to top 3 products only
4. Stream blog_article tokens directly to SSE as they generate from Haiku
5. Target: compose in <8s total, first tokens visible in <2s
