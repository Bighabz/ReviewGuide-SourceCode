# Phase 14: Chat Screen - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructured chat UI: AI responses follow a predictable structure (summary → compact inline product cards → source citations → follow-up chips), message bubbles have correct alignment and styling, and a live status indicator updates during streaming. Includes fixing the review_sources backend bug to enable real source citation links. Follow-up chips get restyled to match the editorial theme.

</domain>

<decisions>
## Implementation Decisions

### Message bubble styling
- User bubbles: right-aligned, bg var(--primary) (#1B4DFF), white text, DM Sans Regular 15px
- User bubble corners: asymmetric — 20px top-left, 20px top-right, 4px bottom-right, 20px bottom-left (iMessage-style tail)
- User bubble max-width: 80% of chat area, padding 12px 16px
- AI bubbles: left-aligned, bg var(--surface-elevated) (#FFFFFF), border 1px solid var(--border), text var(--text)
- AI bubble corners: asymmetric — 4px top-left, 20px top-right, 20px bottom-right, 20px bottom-left
- AI bubble max-width: 85% of chat area, padding 16px
- "✦ ReviewGuide" label on EVERY AI message — DM Sans SemiBold 12px, var(--primary). Consistent, no message-type detection needed.
- All ui_blocks (product cards, source citations, itineraries) render INSIDE the white AI bubble — content is visually grouped within the bubble container

### Compact inline product cards
- New `inline_product_card` block type added to BlockRegistry — existing `product_cards` and `product_carousel` remain for backward compat
- Card height: 64px, horizontal layout, full width of bubble
- Left: product image (64x64, square, 8px radius) — use curated Amazon image if match found, generic category placeholder if not
- Center: rank number + product name (SemiBold 14px) + one-line "why" (Regular 12px, var(--text-secondary))
- Right: price (SemiBold 16px) + "Buy on Amazon" link in var(--primary)
- Rank badges by position: #1 = "🏆 Top Pick", #2 = "⚡ Best Value", #3 = "✨ Premium"
- Rank data derived from product position in response (position 1→Top Pick, 2→Best Value, 3→Premium)
- Cards separated by thin 1px var(--border) divider
- Affiliate links: curated data first, Amazon search URL fallback (`https://amazon.com/s?k=<product+name>&tag=<affiliate-id>`)
- Products without curated images get a generic category-themed placeholder — never show broken image icons

### Chat header status line
- MobileHeader enhanced: dynamic title + status line below
- Title: first user message in session, truncated to ~30 chars. "New Research" for fresh sessions with no messages yet.
- Status line: DM Sans Regular 12px, var(--text-secondary). Shows "Researching • 4 sources analyzed" during streaming, disappears when done.
- Expand icon (↗) on the right side of header — placeholder for Phase 15. Non-functional for now (navigates to # or shows "Results view coming soon" tooltip).
- Status data flow: Claude's discretion (React context, custom event, or prop drilling)

### Source citations
- Fix the review_sources backend bug (broken after product_compose refactor at bd4b5c3) — trace and restore source URL threading so real review URLs reach the frontend
- Source citations section: "Sources" header in DM Sans SemiBold 12px, var(--text-secondary)
- Colored dots by position: source 1 = red, source 2 = blue, source 3 = green, source 4 = orange. Dynamic assignment, no per-source mapping table.
- Each citation: colored dot + source name + article title (truncated) + external link icon
- Clickable — opens original review URL in new tab
- 3-4 sources visible, "+X more" expander if additional sources exist

### Follow-up suggestion chips
- Restyle existing `next_suggestions` chips to match spec
- Pill shape: var(--primary) border, var(--primary) text, transparent background
- 20px corner radius, 8px 16px padding, DM Sans Medium 13px
- Horizontal scrollable row below AI message (outside the bubble)
- Existing `sendSuggestion` custom event click behavior stays unchanged

### Claude's Discretion
- Status data flow mechanism (context vs custom event vs prop drilling)
- Exact review_sources bug fix approach (trace the broken threading)
- Loading/typing state animation style (shimmer vs pulse)
- Compact card image placeholder design
- Source citation "+X more" expander interaction
- Whether to add a new `inline_product_card` ui_block type to backend or handle frontend-only via normalizeBlocks

</decisions>

<specifics>
## Specific Ideas

- AI responses should feel scannable — summary at top gives the quick answer, product cards provide actionable picks, sources prove the research, chips offer next steps
- "✦ ReviewGuide" label gives AI responses an editorial identity — like a byline
- The asymmetric bubble corners give a chat-app feel (iMessage) vs the current flat message rendering
- Source citations are critical for trust — "Based on Wirecutter, RTINGS, and 3 other sources" with clickable links proves the AI did real research

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Message.tsx`: Message renderer — already has `ui_blocks` rendering via `UIBlocks` component, `next_suggestions` chips, `statusText`, `isThinking` states. Needs bubble wrapper + chip restyle.
- `BlockRegistry.tsx`: Maps `ui_block.type` strings to React components. New `inline_product_card` type will be added here.
- `ChatContainer.tsx`: Owns SSE streaming state, messages, sessionId. Has `statusText` flowing to Message already. DO NOT modify streaming logic.
- `MobileHeader.tsx`: Phase 12 component — has back-arrow on `/chat`, shows "Research Session". Needs dynamic title + status line.
- `normalizeBlocks.ts`: Normalizes block types — can map old types to new inline format
- `useStreamReducer.ts`: Stream state reducer — has `errored`, `interrupted` states
- `curatedLinks.ts` / `curated_amazon_links.py`: Static curated product data with images, prices, affiliate links (120+ products)
- `ReviewSources.tsx`: Existing component for source display — may be reusable or replaceable

### Established Patterns
- CSS variables exclusively (`var(--*)`)
- `'use client'` on all interactive components
- `window.dispatchEvent(new CustomEvent('sendSuggestion', ...))` for chip clicks — DO NOT CHANGE
- All render functions in Message.tsx are protected — never modify ui_blocks dispatch logic
- SSE streaming in ChatContainer — do not modify streaming logic

### Integration Points
- `Message.tsx`: Bubble wrapper goes around existing content — must not break ui_blocks rendering
- `BlockRegistry.tsx`: New `inline_product_card` type registered here
- `MobileHeader.tsx`: Needs to receive streaming status from ChatContainer (across component tree via NavLayout)
- `backend/mcp_server/tools/product_compose.py`: review_sources bug is here — source URLs dropped during product_compose refactor
- `backend/app/schemas/graph_state.py`: May need review_sources field verified in GraphState

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-chat-screen*
*Context gathered: 2026-03-17*
