# Phase B: Speculative Execution + Parallel Tools

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Fire product_search before intent classification, stream skeleton cards before affiliate links, and remove streaming delays. Target: 5-8s → 3-4s to first content.

**Architecture:** Speculative search runs in parallel with fast_router inside the safety node. If intent is product/comparison/service, results are reused. PlanExecutor detects pre-fetched results and skips redundant search. Skeleton cards stream as artifacts immediately after search returns.

**Tech Stack:** Python asyncio, LangGraph, SSE streaming.

**Spec:** `docs/superpowers/specs/2026-03-25-sub-3s-response-architecture-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `backend/app/services/fast_router.py` | Add speculative search to async fast_router |
| Modify | `backend/app/core/config.py` | Add USE_SPECULATIVE_SEARCH flag |
| Modify | `backend/app/services/langgraph/workflow.py` | Use async fast_router, pass search results to state |
| Modify | `backend/app/services/plan_executor.py` | Detect pre-fetched search, emit skeleton cards |
| Modify | `backend/app/api/v1/chat.py` | Add cards_update SSE event type, remove streaming delay if any |
| Create | `backend/tests/test_speculative.py` | Tests for speculative execution |

---

## Task 1: Config + Speculative Search in Fast Router

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/fast_router.py`
- Create: `backend/tests/test_speculative.py`

- [ ] **Step 1: Add feature flag**

In `backend/app/core/config.py`, add near `USE_FAST_ROUTER`:

```python
USE_SPECULATIVE_SEARCH: bool = Field(
    default=False,
    description="Start product_search before intent classification (Phase B)"
)
```

- [ ] **Step 2: Write failing tests**

Create `backend/tests/test_speculative.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestSpeculativeSearch:
    @pytest.mark.asyncio
    async def test_speculative_search_runs_parallel_with_router(self):
        """product_search should fire in parallel with fast_router classification."""
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Sony XM5"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.speculative_results is not None
            assert result.speculative_results["product_names"] == ["Sony XM5"]
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_speculative_results_discarded_for_non_product(self):
        """If intent is travel/general/intro, speculative search results are discarded."""
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(return_value={"product_names": ["Fake"], "success": True})
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("plan a trip to Tokyo", [], None, {})
            assert result.intent == "travel"
            assert result.speculative_results is None  # discarded

    @pytest.mark.asyncio
    async def test_speculative_search_failure_doesnt_block(self):
        """If speculative search fails, router still returns normally."""
        from app.services.fast_router import fast_router_with_speculation

        mock_search = AsyncMock(side_effect=Exception("Search API down"))
        with patch("app.services.fast_router.run_speculative_search", mock_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.intent == "product"
            assert result.speculative_results is None  # failed, but intent still classified

    @pytest.mark.asyncio
    async def test_speculative_search_timeout(self):
        """Speculative search has a 10s timeout."""
        import asyncio
        from app.services.fast_router import fast_router_with_speculation

        async def slow_search(*args, **kwargs):
            await asyncio.sleep(15)
            return {"product_names": [], "success": False}

        with patch("app.services.fast_router.run_speculative_search", slow_search):
            result = await fast_router_with_speculation("best headphones", [], None, {})
            assert result.intent == "product"
            assert result.speculative_results is None  # timed out
```

- [ ] **Step 3: Implement speculative search in fast_router.py**

Add to `backend/app/services/fast_router.py`:

1. Update `FastRouterResult` to include `speculative_results`:
```python
@dataclass
class FastRouterResult:
    intent: str
    slots: Dict[str, Any]
    tool_chain: List[str]
    plan: Dict[str, Any]
    confidence: float
    tier: int
    needs_clarification: bool = False
    speculative_results: Optional[Dict[str, Any]] = None  # NEW
```

2. Add `run_speculative_search()`:
```python
async def run_speculative_search(query: str, state: dict) -> Dict[str, Any]:
    """Run product_search speculatively using the raw query."""
    from mcp_server.tools.product_search import product_search
    minimal_state = {
        "user_message": query,
        "slots": state.get("slots", {}),
        "conversation_history": state.get("conversation_history", []),
        "last_search_context": state.get("last_search_context"),
    }
    return await product_search(minimal_state)
```

3. Add `fast_router_with_speculation()`:
```python
async def fast_router_with_speculation(
    query: str,
    conversation_history: list,
    last_search_context: Optional[dict],
    state: dict,
) -> FastRouterResult:
    """
    Async fast router with speculative product_search.
    Fires search in parallel with classification.
    """
    import asyncio
    import contextlib

    # Fire speculative search + classification in parallel
    search_task = asyncio.create_task(run_speculative_search(query, state))
    router_result = await fast_router(query, conversation_history, last_search_context)

    # Check if speculative results are useful
    if router_result.intent in ("product", "comparison", "service"):
        try:
            spec_results = await asyncio.wait_for(search_task, timeout=10.0)
            router_result.speculative_results = spec_results
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Speculative search failed/timed out: {e}")
            router_result.speculative_results = None
    else:
        # Wrong intent — cancel and cleanup
        search_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await search_task
        router_result.speculative_results = None

    return router_result
```

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_speculative.py -v --timeout=30`

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/app/services/fast_router.py
git add -f backend/tests/test_speculative.py
git commit -m "feat(phase-b): speculative search engine in fast_router"
```

---

## Task 2: Wire Speculative Search into Workflow

**Files:**
- Modify: `backend/app/services/langgraph/workflow.py`
- Modify: `backend/app/api/v1/chat.py` (add speculative_results to initial_state)
- Modify: `backend/app/schemas/graph_state.py` (add speculative_results field)

- [ ] **Step 1: Add speculative_results to GraphState**

In `backend/app/schemas/graph_state.py`, add:
```python
speculative_results: Optional[Dict[str, Any]]  # Pre-fetched search results from speculative execution
```

- [ ] **Step 2: Add default to chat.py initial_state**

In `backend/app/api/v1/chat.py`, add to initial_state:
```python
"speculative_results": None,
```

- [ ] **Step 3: Update workflow.py to use async speculation**

In `backend/app/services/langgraph/workflow.py`, modify the fast router bypass (from Phase A):

Replace the sync `fast_router_sync()` call with an async call to `fast_router_with_speculation()` when `USE_SPECULATIVE_SEARCH` is enabled:

```python
from app.services.fast_router import fast_router_sync, fast_router_with_speculation
import asyncio

# In the fast router bypass section:
if settings.USE_FAST_ROUTER and update.get("next_agent") == "intent":
    try:
        if settings.USE_SPECULATIVE_SEARCH:
            # Async speculative: run search in parallel with classification
            router_result = asyncio.get_event_loop().run_until_complete(
                fast_router_with_speculation(
                    state.get("user_message", ""),
                    state.get("conversation_history", []),
                    state.get("last_search_context"),
                    state,
                )
            )
            if router_result.speculative_results:
                update["speculative_results"] = router_result.speculative_results
        else:
            router_result = fast_router_sync(
                state.get("user_message", ""),
                state.get("conversation_history", []),
                state.get("last_search_context"),
            )
        # ... rest of update logic unchanged
```

NOTE: Since LangGraph nodes run inside an async event loop, use `await` directly if the node function is async, or use the loop's `run_in_executor` if it's sync. Check the existing pattern in workflow.py — the safety node may already be async. If so, just `await fast_router_with_speculation(...)` directly.

- [ ] **Step 4: Run tests**

Run: `cd backend && python -m pytest tests/test_fast_router.py tests/test_speculative.py -v --timeout=30`

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/graph_state.py backend/app/api/v1/chat.py backend/app/services/langgraph/workflow.py
git commit -m "feat(phase-b): wire speculative search into workflow, pass results via GraphState"
```

---

## Task 3: PlanExecutor Uses Pre-fetched Results + Skeleton Cards

**Files:**
- Modify: `backend/app/services/plan_executor.py`

- [ ] **Step 1: Detect and use speculative results**

In `plan_executor.py`, modify the step execution logic. When executing `product_search`, check if `state.get("speculative_results")` exists:

```python
# In _execute_step or _call_tool_direct, before calling product_search:
if tool_name == "product_search" and state.get("speculative_results"):
    logger.info("Using pre-fetched speculative search results")
    return state["speculative_results"]
```

- [ ] **Step 2: Emit skeleton cards after product_search**

After product_search completes (whether speculative or fresh), emit skeleton product cards via `stream_chunk_data`:

```python
# After product_search returns results:
if tool_name == "product_search" and result.get("product_names"):
    skeleton_cards = [
        {
            "type": "product_card",
            "name": name,
            "loading": True,  # Frontend shows "Finding best price..."
        }
        for name in result["product_names"][:5]
    ]
    state["stream_chunk_data"] = {
        "type": "skeleton_cards",
        "data": skeleton_cards,
    }
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/ -v --timeout=60 -x 2>&1 | tail -20`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/plan_executor.py
git commit -m "feat(phase-b): PlanExecutor uses speculative results, emits skeleton cards"
```

---

## Task 4: Frontend Skeleton Card Handling

**Files:**
- Modify: `frontend/lib/chatApi.ts` (handle skeleton_cards artifact)
- Modify: `frontend/components/ChatContainer.tsx` (render skeleton state)

- [ ] **Step 1: Handle skeleton_cards in chatApi.ts**

In the artifact event handler (~line 321), add handling for `skeleton_cards`:

```typescript
if (chunk.type === 'skeleton_cards' || chunk.skeleton_cards) {
    const skeletonBlocks = (chunk.data || chunk.skeleton_cards).map((card: any) => ({
        type: 'products',
        data: [{
            name: card.name,
            price: null,
            url: null,
            loading: true,
        }],
    }));
    onComplete({ ui_blocks: skeletonBlocks, skeleton: true });
}
```

- [ ] **Step 2: Handle cards_update in ChatContainer**

In `ChatContainer.tsx`, when a new artifact arrives with non-skeleton product cards, merge them with existing skeleton cards:

The existing `onComplete` handler already replaces `ui_blocks`. When the real product cards arrive (from product_compose), they'll naturally replace the skeleton cards. No special merge logic needed — the final `done` event sends complete ui_blocks which overwrites skeletons.

- [ ] **Step 3: Test manually**

Build frontend: `cd frontend && npm run build`
Verify no build errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/lib/chatApi.ts frontend/components/ChatContainer.tsx
git commit -m "feat(phase-b): frontend skeleton card handling for early product display"
```

---

## Task 5: Enable + Test

- [ ] **Step 1: Set Railway env var**

```
USE_SPECULATIVE_SEARCH=true
```

- [ ] **Step 2: Run full test suite**

```bash
cd backend && python -m pytest tests/ -v --timeout=60
```

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "feat(phase-b): speculative execution complete, deployed"
```
