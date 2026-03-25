# Phase 9: Top Pick Block + Help Me Decide - Research

**Researched:** 2026-03-25
**Domain:** Backend LLM composition, frontend block rendering, intent classification
**Confidence:** HIGH

## Summary

Phase 9 touches three distinct subsystems: (1) the `product_compose` tool in the backend that assembles product responses with UI blocks, (2) the `BlockRegistry` in the frontend that dispatches normalized blocks to React components, and (3) the `IntentAgent` that classifies user messages. All three are well-documented in code and the changes required are additive -- no existing logic needs modification, only extension.

The product_compose tool already caps product_review cards at 5 (line 802) and the concierge path caps at 5 products (line 976). The 5-product cap for UX-04 is largely already enforced for review cards; the gap is in the `products_by_provider` dict which stores up to 10 per provider (line 406). The top_pick block is a new block type that can be added to the existing `BLOCK_RENDERERS` registry without touching the dispatch logic in `Message.tsx`. The comparison intent detection requires extending the intent agent's system prompt or adding post-intent reclassification logic when `last_search_context` contains an active product shortlist.

**Primary recommendation:** Add `top_pick` as a new ui_block type produced by `product_compose` and rendered by a new `TopPickBlock` component registered in `BlockRegistry`. Extend intent classification to detect comparison follow-ups. Cap all product output paths at 5.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UX-03 | Product response displays a "Top Pick" block above carousel with: product name, headline reason, who it's for, who should look elsewhere | New `top_pick` block type in product_compose, new TopPickBlock component registered in BlockRegistry |
| UX-04 | No product response returns more than 5 product cards | Review cards already capped at 5 (line 802); need to also cap products_by_provider at 5 per provider and enforce in all carousel/products block output paths |
| UX-05 | Follow-up comparison messages auto-trigger ComparisonTable without explicit table request | Extend intent agent or add comparison detection in product_compose when last_search_context has active products; route to existing product_comparison tool and ComparisonTable component |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | current | Backend API | Already in use |
| LangGraph | current | Workflow orchestration | Already in use |
| Next.js 14 | 14.x | Frontend framework | Already in use |
| React 18 | 18.x | UI library | Already in use |
| TypeScript | current | Type safety | Already in use |
| Tailwind CSS | current | Styling | Already in use |
| OpenAI GPT-4o | current | LLM for top pick generation | Already used by model_service |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | current | Icons for TopPickBlock | Already in project |
| framer-motion | current | Animations | Already in project, optional for TopPickBlock |
| DOMPurify | current | HTML sanitization | Already in BlockRegistry, not needed for top_pick |

No new packages required for this phase.

## Architecture Patterns

### Backend: product_compose Tool Structure

The `product_compose` tool (`backend/mcp_server/tools/product_compose.py`) follows a 4-phase pattern:

```
Phase 1: Build products_by_provider (pure data)
Phase 2: Prepare LLM coroutines (fired in parallel)
Phase 3: Fire all LLM calls via asyncio.gather
Phase 4: Assemble ui_blocks and assistant_text
```

**Key observations:**
- `ui_blocks` list is built in Phase 4 with three append calls: comparison_html (line 752), product_review (line 885), review_sources (line 917)
- Editorial labels ("Best Overall", "Budget Pick") are already computed by `_assign_editorial_labels()` using review quality_score and price data
- `review_data` contains product-level ReviewBundle with `quality_score`, `avg_rating`, `total_reviews`, `sources`
- The `products_with_offers` list already contains merged affiliate + review data per product
- The `last_search_context` is saved at end of product_compose with `product_names`, `category`, `top_prices`, `avg_rating`

### Frontend: Block Registry Pattern

The BlockRegistry (`frontend/components/blocks/BlockRegistry.tsx`) uses a simple `Record<string, BlockRenderer>` map:

```typescript
const BLOCK_RENDERERS: Record<string, BlockRenderer> = {
    carousel: (b) => <ProductCarousel ... />,
    products: (b) => <ProductCarousel ... />,
    product_review: (b) => <ProductReview ... />,
    product_comparison: (b) => <ComparisonTable data={b.data} title={b.title} />,
    // ... 16 total renderers
}
```

Adding a new block type means:
1. Add a new entry to `BLOCK_RENDERERS` (e.g., `top_pick: (b) => <TopPickBlock ... />`)
2. Create the component file
3. Import it in BlockRegistry

**No changes needed to Message.tsx** -- the `<UIBlocks>` component already renders all blocks from the registry. The block dispatch at line 169-171 falls through to the renderer lookup:
```typescript
const renderer = BLOCK_RENDERERS[block.type] ??
    (block.type?.endsWith('_products') ? BLOCK_RENDERERS['products'] : null)
```

### Frontend: Block Ordering

The `UIBlocks` component renders blocks in array order. The backend controls ordering by the order in which blocks are appended to the `ui_blocks` list. To make top_pick appear above product cards, it must be prepended (or inserted at index 0) before product_review blocks.

### Intent Classification

The `IntentAgent` (`backend/app/agents/intent_agent.py`) uses an LLM call with a system prompt that classifies into: `intro`, `product`, `service`, `travel`, `general`, `unclear`.

**Critical finding:** There is NO "comparison" intent in the intent agent's output categories, even though `routing_gate.py` lists `"comparison"` in `DETERMINISTIC_INTENTS`. The intent agent classifies "compare" queries as `"product"` (see system prompt line 99: "product -> user wants to find, buy, compare, or get recommendations"). The planner agent then selects the `product_comparison` tool when comparison is detected.

The `_is_follow_up_query()` function in product_compose (line 147) already has reference signals including `"compare them"`, `"which one"`, `"between those"` -- but this function is used for context continuity, not for triggering comparison tables.

### GraphState: New Field Requirements

**CRITICAL (from MEMORY.md):** When adding fields to `GraphState` TypedDict, MUST also add default value to `initial_state` dict in `chat.py` (~line 295) or LangGraph channels crash.

Current relevant fields:
- `comparison_table: Optional[Dict[str, Any]]` -- already exists in GraphState
- `comparison_html: Optional[str]` -- NOT in GraphState but used via state dict passthrough
- `comparison_data: Optional[Dict[str, Any]]` -- NOT in GraphState but used via state dict passthrough
- `last_search_context: Dict[str, Any]` -- already persists product names between turns

### SSE Streaming: ui_blocks Delivery

Product intent ui_blocks are sent to the frontend in an early SSE artifact event (chat.py line 591-599):
```python
if ui_blocks and result_state.get("intent") == "product" and not data_already_streamed:
    yield _sse_event("artifact", {"type": "ui_blocks", "blocks": ui_blocks, "clear": True})
```

The final done payload conditionally omits ui_blocks if already sent early (line 714):
```python
"ui_blocks": [] if ui_blocks_sent_early else ui_blocks
```

This means the top_pick block will be delivered with all other product ui_blocks in a single batch. No special streaming treatment needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Top pick selection logic | Custom ranking algorithm | Extend `_assign_editorial_labels()` which already picks "Best Overall" by quality_score | Already has the right data pipeline (review scores, prices, offers) |
| Comparison table rendering | New comparison component | Existing `ComparisonTable` component + `product_comparison` tool | Already handles structured data with images, prices, pros/cons |
| Block rendering dispatch | Custom if/else chain in Message.tsx | `BLOCK_RENDERERS` registry in BlockRegistry.tsx | Registry pattern avoids modifying protected Message.tsx render logic |
| Follow-up detection | Regex-only pattern matching | LLM intent classification with `last_search_context` hint | Already passes context_hint to system prompt; more robust than regex |
| Block normalization | Manual type checking | `normalizeBlocks()` utility | Already handles both old and new block formats |

## Common Pitfalls

### Pitfall 1: Modifying Message.tsx Render Functions
**What goes wrong:** Project memory explicitly warns "All render functions in Message.tsx are protected -- never modify ui_blocks logic"
**Why it happens:** Temptation to add special rendering for top_pick inline
**How to avoid:** Register the new block type exclusively in BlockRegistry.tsx. The `<UIBlocks>` dispatcher already handles arbitrary block types via the registry lookup.
**Warning signs:** Any diff touching the JSX inside Message.tsx's assistant render path

### Pitfall 2: GraphState Field Without Default in initial_state
**What goes wrong:** LangGraph channels crash on existing sessions because the new field has no default value
**Why it happens:** TypedDict field added to schema but not to the initial_state dict in chat.py
**How to avoid:** For every new GraphState field, immediately add a default value in chat.py's `initial_state` dict (around line 295-353)
**Warning signs:** Runtime crash: "Channel X not found in state"

### Pitfall 3: Top Pick Block Ordering
**What goes wrong:** Top pick block renders below product cards instead of above them
**Why it happens:** In product_compose, `ui_blocks.append()` is called sequentially -- comparison_html first, then product_review cards, then review_sources
**How to avoid:** Insert top_pick block at the beginning of the ui_blocks list (index 0) or before product_review blocks. Use `ui_blocks.insert(0, ...)` instead of `ui_blocks.append(...)`.
**Warning signs:** top_pick appears after the product carousel in the chat

### Pitfall 4: Comparison Intent Misrouting
**What goes wrong:** "How do these compare?" triggers a full product search instead of using cached shortlist data
**Why it happens:** Intent agent classifies as "product" (correct) but planner generates a full search plan instead of comparison-only
**How to avoid:** Detection must happen at the planner level or within product_compose's follow-up detection (`_is_follow_up_query()`). When `last_search_context.product_names` exists and the message matches comparison signals, route directly to `product_comparison` tool with the cached product names.
**Warning signs:** A comparison follow-up triggers expensive affiliate/review searches instead of reusing cached data

### Pitfall 5: Top Pick LLM Call Latency
**What goes wrong:** Adding another LLM call for top_pick generation increases total response time
**Why it happens:** Top pick generation is sequential rather than parallel with existing LLM calls
**How to avoid:** Add the top_pick LLM coroutine to the existing `llm_tasks` dict in Phase 2. It will automatically be fired in parallel with concierge/consensus/blog_article via `asyncio.gather()`.
**Warning signs:** Response latency increases by >1 second compared to baseline

### Pitfall 6: Products Still Exceeding 5 After Cap
**What goes wrong:** While review_card_count caps at 5, products_by_provider stores up to 10 per provider, and the carousel block (if produced by any code path) could show more than 5
**Why it happens:** The 5-cap is only enforced in the review card loop and concierge text loop, not on the raw products_by_provider data
**How to avoid:** Apply a hard cap of 5 in the products_by_provider construction loop (line 406: change `[:10]` to `[:5]`) and in the blog_data_parts product list
**Warning signs:** More than 5 products visible in any response card layout

## Code Examples

### Example 1: Adding a New Block Type to BlockRegistry

```typescript
// In frontend/components/blocks/BlockRegistry.tsx
import TopPickBlock from '@/components/TopPickBlock'

const BLOCK_RENDERERS: Record<string, BlockRenderer> = {
    // ... existing renderers ...
    top_pick: (b) => (
        <TopPickBlock
            productName={(b.data as any)?.product_name ?? ''}
            headline={(b.data as any)?.headline ?? ''}
            bestFor={(b.data as any)?.best_for ?? ''}
            notFor={(b.data as any)?.not_for ?? ''}
            imageUrl={(b.data as any)?.image_url}
            affiliateUrl={(b.data as any)?.affiliate_url}
        />
    ),
}
```

### Example 2: Top Pick Block Data Shape (Backend)

```python
# In product_compose, Phase 4 (after LLM results gathered)
top_pick_data = {
    "product_name": best_product_name,
    "headline": top_pick_result.get("headline", ""),
    "best_for": top_pick_result.get("best_for", ""),
    "not_for": top_pick_result.get("not_for", ""),
    "image_url": best_product_image,
    "affiliate_url": best_product_url,
}
ui_blocks.insert(0, {
    "type": "top_pick",
    "title": "Our Top Pick",
    "data": top_pick_data,
})
```

### Example 3: Adding Top Pick LLM Task in Parallel

```python
# In product_compose, Phase 2 (inside llm_tasks dict)
if products_with_offers and review_data:
    best_product = sorted_by_quality[0] if sorted_by_quality else None
    if best_product:
        product_name = best_product[0]
        bundle = best_product[1]
        llm_tasks['top_pick'] = model_service.generate(
            messages=[
                {"role": "system", "content": "You are an editorial product reviewer. Given a top-rated product, write a JSON object with: headline (one sentence why it's the best), best_for (who should buy it, one sentence), not_for (who should look elsewhere, one sentence). Be specific and opinionated."},
                {"role": "user", "content": f'Product: {product_name}\nRating: {bundle.get("avg_rating", 0)}/5\nUser asked: "{user_message}"'}
            ],
            model=settings.COMPOSER_MODEL,
            temperature=0.5,
            max_tokens=150,
            response_format={"type": "json_object"},
            agent_name="top_pick_composer"
        )
```

### Example 4: Comparison Follow-up Detection

```python
# In product_compose or a new helper, detect comparison intent from follow-up
COMPARISON_SIGNALS = [
    "compare", "comparison", "which one", "which should",
    "help me decide", "help me choose", "between these",
    "how do these compare", "side by side", "vs", "versus",
    "differences", "pros and cons of each",
]

def _is_comparison_follow_up(query: str, last_context: dict) -> bool:
    """Detect if a follow-up message is asking for comparison of the active shortlist."""
    if not last_context or not last_context.get("product_names"):
        return False
    q = query.lower().strip()
    return any(signal in q for signal in COMPARISON_SIGNALS)
```

### Example 5: TopPickBlock Component (Editorial Luxury Theme)

```typescript
// frontend/components/TopPickBlock.tsx
interface TopPickBlockProps {
    productName: string
    headline: string
    bestFor: string
    notFor: string
    imageUrl?: string
    affiliateUrl?: string
}

export default function TopPickBlock({ productName, headline, bestFor, notFor, imageUrl, affiliateUrl }: TopPickBlockProps) {
    return (
        <div className="rounded-xl border-2 border-[var(--primary)] bg-[var(--surface-elevated)] p-5 mb-4">
            <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary)] bg-[var(--primary-light)] px-2.5 py-1 rounded-full">
                    Our Top Pick
                </span>
            </div>
            <h3 className="text-lg font-serif font-bold text-[var(--text)] mb-2">
                {productName}
            </h3>
            <p className="text-sm text-[var(--text)] leading-relaxed mb-3">
                {headline}
            </p>
            <div className="space-y-1.5 text-sm">
                <p className="text-[var(--text-secondary)]">
                    <span className="font-semibold text-emerald-600">Best for:</span> {bestFor}
                </p>
                <p className="text-[var(--text-secondary)]">
                    <span className="font-semibold text-[var(--accent)]">Look elsewhere if:</span> {notFor}
                </p>
            </div>
        </div>
    )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 14 inline renderXxx() functions in Message.tsx | Registry-driven BlockRegistry.tsx with `BLOCK_RENDERERS` map | Phase 1 (2026-03-17) | New block types require ONLY a registry entry, not Message.tsx changes |
| Sequential LLM calls in product_compose | Parallel via `asyncio.gather()` on `llm_tasks` dict | Phase 1 (2026-03-17) | Top pick LLM call can be added to parallel batch at zero latency cost |
| Hardcoded intent routing | Planner agent selects tools dynamically based on intent + tool contracts | Current architecture | Comparison follow-up can be handled via planner tool selection |

## Open Questions

1. **Top pick selection: LLM vs. deterministic?**
   - What we know: `_assign_editorial_labels()` already picks "Best Overall" deterministically using `quality_score`. The LLM would add the "headline", "best_for", "not_for" prose.
   - What's unclear: Should selection itself use LLM judgment (might pick differently than quality_score), or should LLM only generate the prose for the deterministically-selected product?
   - Recommendation: Use deterministic selection (existing "Best Overall" logic) + LLM for prose generation. Simpler, faster, predictable.

2. **Comparison follow-up: where to detect?**
   - What we know: Intent agent classifies "compare them" as "product" intent. The planner then selects tools. `_is_follow_up_query()` in product_compose detects reference signals but doesn't trigger comparison tables.
   - What's unclear: Should comparison detection be in (a) the intent agent (add "comparison" to output categories), (b) the planner agent (already sees `last_search_context`), or (c) product_compose itself?
   - Recommendation: Option (c) -- detect in product_compose. When `_is_comparison_follow_up()` returns true and `last_search_context.product_names` has 2+ products, call `product_comparison` tool inline (or add a `product_comparison` block using the cached product data). This avoids modifying the intent classification contract.

3. **5-product cap: where to enforce globally?**
   - What we know: Review cards are capped at 5 (line 802), concierge text caps at 5 (line 976), but products_by_provider stores up to 10 (line 406).
   - What's unclear: Whether any downstream code path could produce > 5 visible products.
   - Recommendation: Change `[:10]` to `[:5]` on line 406 and audit all code paths that produce product blocks.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest with pytest-asyncio |
| Framework (frontend) | vitest 4.x + @testing-library/react 14.x |
| Backend config file | `backend/tests/conftest.py` |
| Frontend config file | `frontend/vitest.config.ts` |
| Backend quick run | `cd backend && python -m pytest tests/test_product_compose.py -x` |
| Frontend quick run | `cd frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-03 | Top pick block present in ui_blocks output with correct fields | unit | `cd backend && python -m pytest tests/test_product_compose.py::test_top_pick_block_present -x` | No - Wave 0 |
| UX-03 | TopPickBlock renders in BlockRegistry for type "top_pick" | unit | `cd frontend && npx vitest run --reporter=verbose -t "top_pick"` | No - Wave 0 |
| UX-04 | No response path produces > 5 product cards | unit | `cd backend && python -m pytest tests/test_product_compose.py::test_max_five_products -x` | No - Wave 0 |
| UX-05 | Comparison follow-up with active shortlist produces ComparisonTable block | unit | `cd backend && python -m pytest tests/test_product_compose.py::test_comparison_follow_up -x` | No - Wave 0 |
| UX-05 | ComparisonTable block renders via product_comparison type in BlockRegistry | unit | `cd frontend && npx vitest run --reporter=verbose -t "comparison"` | Partially (ComparisonTable exists, but no follow-up trigger test) |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_product_compose.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x && cd ../frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_product_compose.py::test_top_pick_block_present` -- covers UX-03 backend
- [ ] `backend/tests/test_product_compose.py::test_max_five_products` -- covers UX-04
- [ ] `backend/tests/test_product_compose.py::test_comparison_follow_up` -- covers UX-05
- [ ] `frontend/tests/TopPickBlock.test.tsx` -- covers UX-03 frontend rendering
- [ ] `frontend/tests/BlockRegistry.test.tsx` -- covers top_pick dispatch in registry

## Sources

### Primary (HIGH confidence)
- `backend/mcp_server/tools/product_compose.py` -- Full product composition pipeline, ui_blocks construction, editorial labels, LLM parallel calls
- `frontend/components/blocks/BlockRegistry.tsx` -- Block type registry with 16 renderers, dispatch logic
- `frontend/components/Message.tsx` -- UIBlocks rendering via `<UIBlocks blocks={normalizeBlocks(message.ui_blocks ?? [])} />`
- `frontend/lib/normalizeBlocks.ts` -- Block normalization: {type, data, title?} canonical shape
- `backend/app/schemas/graph_state.py` -- GraphState TypedDict with all 40+ fields
- `backend/app/api/v1/chat.py` -- initial_state construction (lines 295-353), SSE streaming of ui_blocks
- `backend/app/agents/intent_agent.py` -- Intent classification categories and LLM prompt
- `backend/app/services/langgraph/nodes/routing_gate.py` -- DETERMINISTIC_INTENTS routing
- `frontend/components/ComparisonTable.tsx` -- Existing comparison table component with ComparisonProduct interface

### Secondary (MEDIUM confidence)
- `backend/mcp_server/tools/product_comparison.py` -- Existing comparison tool (generates HTML comparison table)
- `backend/app/agents/planner_agent.py` -- Dynamic tool selection based on intent + contracts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new dependencies
- Architecture: HIGH -- BlockRegistry pattern is well-documented, product_compose pipeline is clear
- Pitfalls: HIGH -- based on direct code reading and project memory warnings (GraphState, Message.tsx)
- Comparison detection: MEDIUM -- multiple valid approaches; recommendation is pragmatic but alternatives exist

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable architecture, no external dependency changes expected)
