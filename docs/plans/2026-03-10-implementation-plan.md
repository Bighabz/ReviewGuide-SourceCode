# Compliance, UX Fixes & Editorial Restyling — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add legal/compliance pages, global footer with 3-tier affiliate disclosure, fix UX bugs, and editorially restyle product result blocks.

**Architecture:** Frontend-only changes (Approach A). No backend modifications except potentially strengthening name-memory prompts. All new pages follow existing Next.js 14 App Router patterns. Footer is a shared component added to root layout. Product blocks are restyled in-place.

**Tech Stack:** Next.js 14, React 18, TypeScript, Tailwind CSS, CSS variables (editorial theme), lucide-react icons

---

## Task 1: Create Global Footer Component

**Files:**
- Create: `frontend/components/Footer.tsx`

**Step 1: Create the Footer component**

```tsx
import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="w-full border-t border-[var(--border)] bg-[var(--surface)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12">
        {/* Three-column grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-12">
          {/* Brand */}
          <div>
            <h3 className="font-serif text-lg font-semibold text-[var(--text)] mb-3">
              ReviewGuide.ai
            </h3>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              AI-powered product research, reviews, and price comparison — all in one conversation.
            </p>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
              Legal
            </h4>
            <ul className="space-y-2">
              <li>
                <Link href="/privacy" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/affiliate-disclosure" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors">
                  Affiliate Disclosure
                </Link>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
              Connect
            </h4>
            <ul className="space-y-2">
              <li>
                <a href="mailto:mike@reviewguide.ai" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)] transition-colors">
                  mike@reviewguide.ai
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Prominent Affiliate Disclosure */}
        <div className="mt-8 pt-6 border-t border-[var(--border)]">
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-3xl">
            ReviewGuide.ai participates in affiliate marketing programs, including the Amazon Associates program. We may earn commissions when you purchase products through links on our site, at no additional cost to you. Our recommendations are generated independently and are not influenced by affiliate partnerships.
          </p>
        </div>

        {/* Copyright */}
        <div className="mt-6 pt-4 border-t border-[var(--border)]">
          <p className="text-xs text-[var(--text-muted)]">
            &copy; {new Date().getFullYear()} ReviewGuide.ai. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
```

**Step 2: Commit**
```bash
git add frontend/components/Footer.tsx
git commit -m "feat: create global Footer component with legal links and affiliate disclosure"
```

---

## Task 2: Add Footer to Root Layout

**Files:**
- Modify: `frontend/app/layout.tsx`

**Step 1: Import Footer and add it below children**

In `frontend/app/layout.tsx`, the current body is:
```tsx
<body className={`${dmSans.variable} ${instrumentSerif.variable} font-sans`} suppressHydrationWarning>{children}</body>
```

Change to:
```tsx
<body className={`${dmSans.variable} ${instrumentSerif.variable} font-sans`} suppressHydrationWarning>
  <div className="flex flex-col min-h-screen">
    <div className="flex-1">{children}</div>
    <Footer />
  </div>
</body>
```

Add import at top:
```tsx
import Footer from '@/components/Footer'
```

**Important note:** The chat page has a sticky input bar at the bottom. The footer sits BELOW the chat container in the DOM flow — users scroll past the chat to see it. It does NOT interfere with the sticky chat input because the sticky input is positioned within its own container. Verify this visually after implementation.

**Step 2: Remove inline footer from ChatContainer**

In `frontend/components/ChatContainer.tsx` lines 845-850, remove the old minimal footer:
```tsx
{/* Minimal footer */}
<div id="footer" className="mt-3 sm:mt-4 text-center">
  <div className="text-[10px] sm:text-xs mb-2 text-[var(--text-muted)] opacity-80">
    ReviewGuide.ai may earn from qualifying purchases. AI results should be verified.
  </div>
</div>
```

**Step 3: Verify the footer renders on `/browse`, `/chat`, `/privacy`, `/affiliate-disclosure`**

Run: `cd frontend && npm run dev`
Check each route in the browser. Footer should appear at the bottom of every page.

**Step 4: Commit**
```bash
git add frontend/app/layout.tsx frontend/components/ChatContainer.tsx
git commit -m "feat: add Footer to root layout and remove inline chat footer"
```

---

## Task 3: Create Terms of Service Page

**Files:**
- Create: `frontend/app/terms/page.tsx`

**Step 1: Create the page**

Follow the exact same layout pattern as `frontend/app/privacy/page.tsx` (max-w-3xl, back-to-browse link, editorial headings, prose sections).

Sections to include:
1. **Acceptance of Terms** — by using the site, you agree
2. **Service Description** — AI-powered product research and recommendation platform
3. **User Responsibilities** — no misuse, no scraping, no automated access
4. **AI-Generated Content** — content is informational, not professional advice; verify independently
5. **Affiliate Links** — site contains affiliate links; purchases through links may generate commissions
6. **Intellectual Property** — content owned by ReviewGuide.ai
7. **Disclaimers** — provided "as is", no warranty on accuracy
8. **Limitation of Liability** — not liable for purchasing decisions based on AI content
9. **Changes to Terms** — may update periodically
10. **Contact** — mike@reviewguide.ai

Use effective date: March 10, 2026.

**Step 2: Verify the page renders at `/terms`**

Run dev server and navigate to `http://localhost:3000/terms`.

**Step 3: Commit**
```bash
git add frontend/app/terms/page.tsx
git commit -m "feat: create Terms of Service page"
```

---

## Task 4: Update Affiliate Disclosure Page

**Files:**
- Modify: `frontend/app/affiliate-disclosure/page.tsx`

**Step 1: Update content to match stakeholder-provided language**

Replace the `<div className="space-y-6">` section (lines 22-57) with:

```tsx
<div className="space-y-6">
  <p className="text-[var(--text-secondary)] leading-relaxed">
    ReviewGuide.ai participates in various affiliate marketing programs.
    This means we may earn a commission when users purchase products through
    links on our website, at no additional cost to you.
  </p>

  <p className="text-[var(--text-secondary)] leading-relaxed font-medium text-[var(--text)]">
    As an Amazon Associate, we earn from qualifying purchases.
  </p>

  <p className="text-[var(--text-secondary)] leading-relaxed">
    Our product summaries and recommendations are generated independently
    to help users make informed decisions. Affiliate partnerships do not
    influence our analysis, opinions, or product evaluations.
  </p>

  <div className="border-t border-[var(--border)] pt-6 mt-8">
    <p className="text-sm text-[var(--text-muted)]">
      Questions?{' '}
      <a
        href="mailto:mike@reviewguide.ai"
        className="text-[var(--primary)] hover:underline"
      >
        mike@reviewguide.ai
      </a>
    </p>
  </div>
</div>
```

**Step 2: Commit**
```bash
git add frontend/app/affiliate-disclosure/page.tsx
git commit -m "fix: update affiliate disclosure to match required FTC language"
```

---

## Task 5: Update Privacy Policy Date

**Files:**
- Modify: `frontend/app/privacy/page.tsx`

**Step 1: Update effective date on line 22**

Change `February 27, 2026` to `March 10, 2026`.

**Step 2: Commit**
```bash
git add frontend/app/privacy/page.tsx
git commit -m "chore: update privacy policy effective date"
```

---

## Task 6: Add Tier 3 Inline Disclosure to Product Components

**Files:**
- Modify: `frontend/components/ProductCards.tsx`
- Modify: `frontend/components/ProductCarousel.tsx`
- Modify: `frontend/components/AffiliateLinks.tsx`
- Modify: `frontend/components/blocks/BlockRegistry.tsx` (for price_comparison)

**Step 1: Add disclosure to ProductCards**

In `frontend/components/ProductCards.tsx`, add after the closing `})}` of the map (before the final `</div>`):

```tsx
{/* Tier 3 Affiliate Disclosure */}
<p className="text-xs text-[var(--text-muted)] mt-3 px-1">
  Disclosure: We may earn commissions from qualifying purchases.
</p>
```

**Step 2: Add disclosure to ProductCarousel**

In `frontend/components/ProductCarousel.tsx`, add after the pagination dots section (before the final `</div>` of the outer wrapper, around line 253):

```tsx
{/* Tier 3 Affiliate Disclosure */}
<p className="text-xs text-[var(--text-muted)] mt-3 px-1">
  Disclosure: We may earn commissions from qualifying purchases.
</p>
```

**Step 3: Add disclosure to AffiliateLinks**

In `frontend/components/AffiliateLinks.tsx`, add after the grid `</div>` (before the closing `</div>` of the outer wrapper, around line 84):

```tsx
{/* Tier 3 Affiliate Disclosure */}
<p className="text-xs text-[var(--text-muted)] mt-3">
  Disclosure: We may earn commissions from qualifying purchases.
</p>
```

**Step 4: Add disclosure to PriceComparison in BlockRegistry**

In `frontend/components/blocks/BlockRegistry.tsx`, wrap the price_comparison renderer (line 100-101) to include disclosure:

```tsx
price_comparison: (b) => (
    <div>
        <PriceComparison items={(b.data as any[]) ?? []} title={b.title} />
        <p className="text-xs text-[var(--text-muted)] mt-3 px-1">
            Disclosure: We may earn commissions from qualifying purchases.
        </p>
    </div>
),
```

**Step 5: Commit**
```bash
git add frontend/components/ProductCards.tsx frontend/components/ProductCarousel.tsx frontend/components/AffiliateLinks.tsx frontend/components/blocks/BlockRegistry.tsx
git commit -m "feat: add Tier 3 inline affiliate disclosure near product links"
```

---

## Task 7: Remove "Results may be incomplete" Message

**Files:**
- Modify: `frontend/components/Message.tsx`

**Step 1: Remove the ExplainabilityPanel render block**

In `frontend/components/Message.tsx`, remove lines 300-308:

```tsx
{/* RFC §2.5: explainability panel — shown only when result quality is degraded
     or at least one provider returned no data.  Collapsed by default. */}
{message.response_metadata &&
  (message.response_metadata.degraded ||
    (message.response_metadata.missing_sources ?? []).length > 0) && (
    <ExplainabilityPanel
      metadata={message.response_metadata}
    />
)}
```

Also remove the import on line 11:
```tsx
import { ExplainabilityPanel } from './ExplainabilityPanel'
```

**Note:** Do NOT delete `ExplainabilityPanel.tsx` itself — just remove its usage. It may be re-enabled later.

**Step 2: Commit**
```bash
git add frontend/components/Message.tsx
git commit -m "ui: remove 'Results may be incomplete' explainability panel from messages"
```

---

## Task 8: Fix Mobile Horizontal Scrolling

**Files:**
- Modify: `frontend/components/Message.tsx` (line 119)
- Modify: `frontend/components/ChatContainer.tsx` (if needed)
- Modify: `frontend/app/globals.css` (if needed)

**Step 1: Investigate and fix the overflow source**

The most likely culprits for mobile horizontal overflow:

**A) Message container** — Line 119 of `Message.tsx`:
```tsx
<div id="message-container" className="mr-auto flex gap-2 sm:gap-4 items-start flex-row overflow-visible" style={{ maxWidth: '780px' }}>
```
The `overflow-visible` class allows child content to escape bounds. Change to `overflow-hidden` or add `max-w-full`:
```tsx
<div id="message-container" className="mr-auto flex gap-2 sm:gap-4 items-start flex-row overflow-hidden max-w-full" style={{ maxWidth: '780px' }}>
```

**B) Comparison HTML block** — The `comparison_html` renderer in BlockRegistry injects raw HTML with inline CSS that may have fixed widths. In BlockRegistry line 81, the container already has `overflow-hidden` and `rounded-xl`. Add `max-w-full`:
```tsx
className="comparison-html-container rounded-xl overflow-hidden overflow-x-auto shadow-card border border-[var(--border)] max-w-full"
```

**C) ProductCarousel** — The flex container (line 148) may overflow on very small screens. Ensure it has `overflow-hidden` (already present) and cards respect `min-w-0`.

**D) Global safety net** — Add to `frontend/app/globals.css` if not already present:
```css
#message-container,
.comparison-html-container,
.prose {
  overflow-wrap: break-word;
  word-break: break-word;
}
```

**Step 2: Test on mobile viewport**

Open browser dev tools → toggle device toolbar → select iPhone SE or similar small device. Navigate to `/chat` and send a query. Verify no horizontal scrollbar appears.

**Step 3: Commit**
```bash
git add frontend/components/Message.tsx frontend/components/blocks/BlockRegistry.tsx frontend/app/globals.css
git commit -m "fix: prevent mobile horizontal scrolling in chat messages and product blocks"
```

---

## Task 9: Verify Submit Arrow Button

**Files:**
- Investigate: `frontend/components/ChatInput.tsx`
- Investigate: `frontend/components/ChatContainer.tsx`

**Step 1: Trace the issue**

The code at `ChatInput.tsx:80` has `onClick={onSend}` and `ChatContainer.tsx:840` passes `onSend={handleSendMessage}`. The `handleSendMessage` function at line 635 checks `if (!messageToSend.trim() || isStreaming) return`.

Check for these possible causes:
1. **`isStreaming` stuck as `true`** — If a previous stream errored without resetting `isStreaming`, the button stays disabled. Check `useStreamReducer` for proper error-state cleanup.
2. **CSS overlay blocking clicks** — Check if any absolutely positioned element sits over the button (z-index issue).
3. **`disabled` prop** — The button is `disabled={disabled || !hasValue}`. If `ChatContainer` passes `disabled={isStreaming}` and streaming gets stuck, button stays disabled.

**Step 2: If `isStreaming` gets stuck, fix the stream error handler**

Look for the `useStreamReducer` hook and its `RESET`/error handling. Ensure that on error or timeout, `isStreaming` is set back to `false`.

**Step 3: Test**

Open `/chat`, type a query, click the arrow button. It should submit. Also test: send a query, wait for response, type another query, click arrow — should submit again.

**Step 4: Commit only if a code change was needed**
```bash
git add frontend/components/ChatInput.tsx frontend/components/ChatContainer.tsx
git commit -m "fix: ensure submit arrow button triggers chat send correctly"
```

---

## Task 10: Editorial Restyle — ProductCards

**Files:**
- Modify: `frontend/components/ProductCards.tsx`

**Step 1: Restyle the component**

Replace the current card layout with a more editorial blog-style. Key changes:
- Use `font-serif` for product name headings (e.g., "1. iRobot Roomba j9+")
- Show editorial badges (Best Overall, Budget Pick) as styled subtitles
- Convert pros/cons from bullet grid to flowing text paragraphs
- Change "View Deal" CTA to "Check price on [Merchant] →"
- More whitespace, warmer card background
- Keep the same interface — only change the JSX/styling

The full replacement for the return JSX inside the map:

```tsx
<div
  key={product.id || product.rank || index}
  className="group bg-[var(--surface-elevated)] border border-[var(--border)] rounded-xl overflow-hidden hover:shadow-md transition-all duration-300"
>
  <div className="p-5 sm:p-6">
    {/* Editorial heading */}
    <div className="flex items-start justify-between gap-4 mb-2">
      <div className="flex-1 min-w-0">
        <h3 className="font-serif text-xl font-semibold text-[var(--text)] leading-snug tracking-tight">
          <span className="text-[var(--primary)]">{displayRank}.</span>{' '}
          <a href={displayLink} target="_blank" rel="noopener noreferrer" className="hover:underline decoration-1 underline-offset-4">
            {displayTitle}
          </a>
        </h3>
        {/* Badges as editorial labels */}
        <div className="flex items-center gap-2 mt-1.5">
          {product.badges?.map((badge, bIdx) => (
            <span key={bIdx} className="text-xs font-semibold text-[var(--accent)] italic">
              {badge}
            </span>
          ))}
          {displayMerchant && (
            <span className="text-[10px] uppercase font-medium tracking-wider text-[var(--text-muted)]">
              via {displayMerchant}
            </span>
          )}
        </div>
      </div>
      {displayPrice !== undefined && (
        <div className="text-right shrink-0">
          <p className="text-xl font-bold text-[var(--text)] font-serif">
            ${displayPrice.toFixed(2)}
          </p>
        </div>
      )}
    </div>

    {/* Snippet / description */}
    {product.snippet && (
      <p className="text-sm text-[var(--text-secondary)] leading-relaxed mt-3 mb-4">
        {product.snippet}
      </p>
    )}

    {/* Pros & cons as flowing text */}
    {(displayPros.length > 0 || displayCons.length > 0) && (
      <div className="mt-3 mb-4 space-y-2 text-sm leading-relaxed">
        {displayPros.length > 0 && (
          <p className="text-[var(--text)]">
            <span className="font-semibold text-green-600">What we like:</span>{' '}
            {displayPros.join('. ')}.
          </p>
        )}
        {displayCons.length > 0 && (
          <p className="text-[var(--text)]">
            <span className="font-semibold text-red-500">Watch out for:</span>{' '}
            {displayCons.join('. ')}.
          </p>
        )}
      </div>
    )}

    {/* CTA */}
    <div className="flex justify-start pt-3 border-t border-[var(--border)]">
      <a
        href={displayLink}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 text-sm font-medium text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors"
      >
        Check price{displayMerchant ? ` on ${displayMerchant}` : ''} &rarr;
      </a>
    </div>
  </div>
</div>
```

**Step 2: Verify visually**

Send a product query in chat (e.g., "best robot vacuums"). Confirm the cards render with editorial styling.

**Step 3: Commit**
```bash
git add frontend/components/ProductCards.tsx
git commit -m "ui: restyle ProductCards with editorial blog-like layout"
```

---

## Task 11: Editorial Restyle — ProductCarousel

**Files:**
- Modify: `frontend/components/ProductCarousel.tsx`

**Step 1: Restyle the carousel cards**

Key changes to the card content area (inside the `<a>` tag, lines 170-232):
- Larger, more comfortable padding
- Serif font for product title
- "View on [Merchant] →" instead of "View Deal"
- Price section more prominent

Replace the content `<div className="p-4 space-y-2">` section (lines 176-230) with:

```tsx
<div className="p-4 sm:p-5 space-y-2.5">
  {/* Merchant + Best Price badge */}
  <div className="flex items-center gap-2">
    <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
      {item.merchant}
    </span>
    {item.best_price && (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/15 dark:text-emerald-400">
        Best Price
      </span>
    )}
  </div>

  {/* Title — serif */}
  <h4 className="font-serif text-base font-semibold text-[var(--text)] line-clamp-2 leading-snug group-hover:text-[var(--primary)] transition-colors">
    {item.title}
  </h4>

  {/* Rating */}
  {item.rating && (
    <div className="flex items-center gap-1.5">
      <StarRatingInline value={item.rating} size={13} />
      <span className="text-xs text-[var(--text-muted)]">
        {item.rating}
        {item.review_count && ` (${item.review_count.toLocaleString()})`}
      </span>
    </div>
  )}

  {/* Price + CTA */}
  <div className="flex items-center justify-between pt-2.5 border-t border-[var(--border)]">
    <div>
      <span className="text-lg font-bold font-serif text-[var(--text)]">
        {item.currency === 'USD' ? '$' : item.currency}{' '}
        {item.price?.toFixed(2) ?? 'N/A'}
      </span>
      {item.best_price && item.savings != null && item.savings > 0 && (
        <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
          Save ${item.savings.toFixed(2)}{item.compared_retailer ? ` vs ${item.compared_retailer}` : ''}
        </p>
      )}
    </div>
    <span className="inline-flex items-center gap-1 text-xs font-medium text-[var(--primary)] group-hover:text-[var(--primary-hover)]">
      View on {item.merchant} &rarr;
    </span>
  </div>
</div>
```

**Step 2: Commit**
```bash
git add frontend/components/ProductCarousel.tsx
git commit -m "ui: restyle ProductCarousel with editorial serif headings and layout"
```

---

## Task 12: Editorial Restyle — AffiliateLinks

**Files:**
- Modify: `frontend/components/AffiliateLinks.tsx`

**Step 1: Restyle the component**

Change the product header to use `font-serif` (already does). Make the retailer link cards more editorial:

Replace the grid content (lines 38-83) with:

```tsx
{/* Where to Buy — editorial heading */}
<h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
  Where to buy
</h4>

<div className="space-y-2">
  {affiliateLinks.map((link, idx) => (
    <a
      key={idx}
      href={link.affiliate_link}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--primary)]/30 transition-all group"
    >
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] shrink-0">
          {link.merchant}
        </span>
        {link.rating && (
          <div className="flex items-center gap-1">
            <Star size={12} fill="currentColor" className="text-amber-500" />
            <span className="text-xs text-[var(--text-muted)]">{link.rating}</span>
          </div>
        )}
        {link.review_count && link.review_count > 0 && (
          <span className="text-xs text-[var(--text-muted)]">
            ({link.review_count.toLocaleString()} reviews)
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-base font-bold font-serif text-[var(--text)]">
          {link.currency} {link.price.toFixed(2)}
        </span>
        <span className="text-xs font-medium text-[var(--primary)] group-hover:text-[var(--primary-hover)] flex items-center gap-1">
          View <ExternalLink size={12} />
        </span>
      </div>
    </a>
  ))}
</div>
```

**Step 2: Commit**
```bash
git add frontend/components/AffiliateLinks.tsx
git commit -m "ui: restyle AffiliateLinks with editorial 'Where to buy' layout"
```

---

## Task 13: Investigate and Fix Chat Name Memory

**Files:**
- Investigate: `backend/mcp_server/tools/general_compose.py` (lines 85, 90-95, 151)
- Investigate: `backend/app/api/v1/chat.py` (lines 226-298)

**Step 1: Verify conversation history is being passed to compose tools**

Add temporary debug logging in `general_compose.py` to confirm history length and content:
```python
logger.info(f"[general_compose] History length: {len(conversation_history)}, first msg: {conversation_history[0] if conversation_history else 'EMPTY'}")
```

**Step 2: Test the name memory flow**

1. Start a new chat session
2. Send: "My name is Mike"
3. Wait for response
4. Send: "What's my name?"
5. Check backend logs for the history being passed

**Step 3: If history is passed correctly but LLM drops the name**

Strengthen the system prompt in `general_compose.py` line 85. Change:
```python
"You remember everything the user has told you — their name, preferences, pets, family members, budget, etc."
```
To:
```python
"You remember everything the user has told you. If the user introduced themselves or shared their name earlier in the conversation, always address them by name. Remember their preferences, budget, family members, pets, etc. Use these personal details naturally in your responses."
```

**Step 4: Commit if changes were made**
```bash
git add backend/mcp_server/tools/general_compose.py
git commit -m "fix: strengthen name memory instructions in general compose prompt"
```

---

## Task 14: Final Verification and Cleanup

**Step 1: Run frontend build to catch TypeScript/compilation errors**
```bash
cd frontend && npm run build
```

Fix any errors that appear.

**Step 2: Visual verification checklist**

Open dev server (`npm run dev`) and check:
- [ ] Footer appears on `/browse`, `/chat`, `/privacy`, `/terms`, `/affiliate-disclosure`
- [ ] Footer links navigate correctly
- [ ] `/terms` page renders with all sections
- [ ] `/affiliate-disclosure` has updated Amazon Associates language
- [ ] Inline disclosure text appears below ProductCards, ProductCarousel, AffiliateLinks, PriceComparison blocks
- [ ] "Results may be incomplete" no longer appears in chat messages
- [ ] No horizontal scrolling on mobile (test with browser dev tools device emulation)
- [ ] Submit arrow button works on desktop
- [ ] Product cards have editorial styling (serif headings, flowing pros/cons, "Check price" CTA)
- [ ] Carousel cards have serif headings
- [ ] AffiliateLinks shows "Where to buy" layout

**Step 3: Final commit**
```bash
git add -A
git commit -m "chore: cleanup and fix any build issues from compliance and editorial changes"
```

---

## Task Summary

| Task | Description | Priority | Est. Complexity |
|------|-------------|----------|----------------|
| 1 | Create Footer component | P0 | Low |
| 2 | Add Footer to layout + remove inline footer | P0 | Low |
| 3 | Create Terms of Service page | P0 | Low |
| 4 | Update Affiliate Disclosure language | P0 | Low |
| 5 | Update Privacy Policy date | P0 | Trivial |
| 6 | Add Tier 3 inline disclosures | P0 | Low |
| 7 | Remove "Results may be incomplete" | P1 | Trivial |
| 8 | Fix mobile horizontal scrolling | P1 | Medium |
| 9 | Verify/fix submit arrow button | P1 | Medium |
| 10 | Editorial restyle ProductCards | P1 | Medium |
| 11 | Editorial restyle ProductCarousel | P1 | Low |
| 12 | Editorial restyle AffiliateLinks | P1 | Low |
| 13 | Investigate chat name memory | P2 | Medium |
| 14 | Final verification and cleanup | P0 | Low |

## Dependency Order

Tasks 1-7 are independent and can be parallelized.
Task 8 (mobile scroll) should be done after Tasks 10-12 (editorial restyling) since restyling may fix or introduce overflow issues.
Task 9 (submit button) is independent.
Task 13 (name memory) is independent (backend).
Task 14 must be last.
