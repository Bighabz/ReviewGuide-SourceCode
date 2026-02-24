# Bug Fixes, Performance & UX — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the `product_general_information` data drop, shave ~400ms off cold-start latency by parallelising startup I/O, and tighten three high-friction UX moments (suggestion auto-send, unreadable chip labels, over-verbose suggestion category display).

**Architecture:** All changes are surgical — one backend bug fix, one async I/O optimisation in the request entry-point, and two self-contained frontend component edits. No schema or API contract changes.

**Tech Stack:** FastAPI (Python asyncio), LangGraph, Next.js 14 / React 18, TypeScript, Tailwind CSS, Redis (existing).

---

## Task 1 — Fix `product_general_information` data drop in `product_compose`

When the planner uses the **minimal (factoid) path**, `product_general_information` fetches a detailed answer (1 000+ chars) and writes it to `state["general_product_info"]`. `product_compose` then runs but never reads that key, so it hits the "no results" branch and throws the answer away.

**Files:**
- Modify: `backend/mcp_server/tools/product_compose.py` — lines 266-295 (state reads + early-exit guard)
- Test: `backend/tests/test_product_compose.py` (add new test case)

---

### Step 1 — Write the failing test

Add a new test to `backend/tests/test_product_compose.py`:

```python
@pytest.mark.asyncio
async def test_compose_uses_general_product_info_when_no_listings(mock_model_service):
    """
    When product_general_information ran but no affiliate/review data exists,
    product_compose must return the general_product_info text as assistant_text
    rather than the generic fallback message.
    """
    state = {
        "user_message": "tell me more about Sony WH-1000XM5",
        "intent": "product",
        "slots": {},
        "normalized_products": [],
        "affiliate_products": {},
        "review_data": {},
        "comparison_html": None,
        "comparison_data": None,
        "general_product_info": "The Sony WH-1000XM5 is a premium over-ear headphone...",
        "conversation_history": [],
        "last_search_context": {},
        "search_history": [],
    }
    result = await product_compose(state)
    assert result["success"] is True
    assert "Sony WH-1000XM5" in result["assistant_text"]
    assert result["assistant_text"] != "I wasn't able to find current listings for that product."
    assert result["ui_blocks"] == []
```

### Step 2 — Run test to verify it fails

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/test_product_compose.py::test_compose_uses_general_product_info_when_no_listings -v
```

Expected: **FAIL** — `assert "Sony WH-1000XM5" in result["assistant_text"]` fails because the fallback message is returned instead.

---

### Step 3 — Implement the fix

In `backend/mcp_server/tools/product_compose.py`, find the block that reads state variables (around line 266). Add the new read **after** `review_data`:

```python
# EXISTING reads (already there):
review_data = state.get("review_data", {})

# ADD THIS LINE:
general_product_info = state.get("general_product_info", "")
```

Then find the early-exit guard (around line 289):

```python
# EXISTING (replace this block):
if not normalized_products and not affiliate_products and not review_data:
    assistant_text = (
        "I wasn't able to find current listings for that product. "
        "Try searching with a broader term — for example, the product category "
        "or brand name — and I'll pull up the best options available."
    )
    return {
        "assistant_text": assistant_text,
        "ui_blocks": [],
        "citations": [],
        "success": True
    }

# REPLACE WITH:
if not normalized_products and not affiliate_products and not review_data:
    if general_product_info:
        # product_general_information already fetched a full answer — use it
        return {
            "assistant_text": general_product_info,
            "ui_blocks": [],
            "citations": [],
            "success": True
        }
    assistant_text = (
        "I wasn't able to find current listings for that product. "
        "Try searching with a broader term — for example, the product category "
        "or brand name — and I'll pull up the best options available."
    )
    return {
        "assistant_text": assistant_text,
        "ui_blocks": [],
        "citations": [],
        "success": True
    }
```

### Step 4 — Run test to verify it passes

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/test_product_compose.py::test_compose_uses_general_product_info_when_no_listings -v
```

Expected: **PASS**

### Step 5 — Run full test suite to check no regressions

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/ -v --timeout=60 2>&1 | tail -20
```

Expected: 226 pass, same pre-existing failures only (6 SerpAPI-related).

### Step 6 — Commit

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode
git add backend/mcp_server/tools/product_compose.py backend/tests/test_product_compose.py
git commit -m "fix: surface general_product_info answer in product_compose

When the planner routes through product_general_information (factoid path),
the fetched answer is now returned as assistant_text instead of being silently
discarded by the no-results fallback."
```

---

## Task 2 — Parallelise startup I/O in chat endpoint (~300–500 ms saving)

`chat.py` performs two sequential async calls before the workflow starts:
1. `HaltStateManager.get_halt_state(session_id)` — Redis lookup
2. `chat_history_manager.get_history(session_id)` — Redis/Postgres lookup

These are independent and can run in parallel with `asyncio.gather`.

**Files:**
- Modify: `backend/app/api/v1/chat.py` — find the two sequential awaits (around line 260–270)
- Test: `backend/tests/test_chat_api.py` (verify the gather still propagates both results correctly — no new test needed if existing tests cover this path; add a smoke test if they don't)

---

### Step 1 — Read the current code

Open `backend/app/api/v1/chat.py` and locate the two sequential awaits. They look like:

```python
halt_state_data = await HaltStateManager.get_halt_state(session_id)
# ... possibly some code in between ...
conversation_history = await chat_history_manager.get_history(session_id)
```

Confirm there is no data dependency between them (one result is not fed into the other call). If there is any intervening code between them, read it carefully before proceeding.

### Step 2 — Write the failing test (timing assertion)

Add to `backend/tests/test_chat_api.py`:

```python
import asyncio, time

@pytest.mark.asyncio
async def test_startup_io_calls_are_concurrent(monkeypatch):
    """
    HaltStateManager.get_halt_state and chat_history_manager.get_history
    must be awaited concurrently, not sequentially.
    """
    call_order = []

    async def fake_halt(session_id):
        call_order.append("halt_start")
        await asyncio.sleep(0.05)
        call_order.append("halt_end")
        return {}

    async def fake_history(session_id):
        call_order.append("history_start")
        await asyncio.sleep(0.05)
        call_order.append("history_end")
        return []

    monkeypatch.setattr("app.api.v1.chat.HaltStateManager.get_halt_state", fake_halt)
    monkeypatch.setattr("app.api.v1.chat.chat_history_manager.get_history", fake_history)

    start = time.monotonic()
    # Call the internal helper that does the two awaits
    # (adjust import path to match the actual function name in chat.py)
    from app.api.v1.chat import _load_session_context
    halt, history = await _load_session_context("test-session")
    elapsed = time.monotonic() - start

    # If concurrent: elapsed ≈ 0.05s. If sequential: elapsed ≈ 0.10s
    assert elapsed < 0.09, f"Calls appear sequential (took {elapsed:.3f}s)"
    assert halt == {}
    assert history == []
```

> **Note:** This test requires the two awaits to be extracted into a named helper `_load_session_context`. If they are inline in the route handler, extract them as part of the implementation step.

### Step 3 — Run test to verify it fails

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/test_chat_api.py::test_startup_io_calls_are_concurrent -v
```

Expected: **FAIL** — elapsed > 0.09s because calls are sequential, OR `_load_session_context` import error.

### Step 4 — Implement the fix

In `backend/app/api/v1/chat.py`, replace the two sequential awaits with:

```python
import asyncio  # already imported, but verify

# BEFORE (sequential):
halt_state_data = await HaltStateManager.get_halt_state(session_id)
conversation_history = await chat_history_manager.get_history(session_id)

# AFTER (concurrent):
halt_state_data, conversation_history = await asyncio.gather(
    HaltStateManager.get_halt_state(session_id),
    chat_history_manager.get_history(session_id),
)
```

If there is any code between the two awaits that uses `halt_state_data` before `conversation_history` is fetched, move that code to **after** the `asyncio.gather` line.

If the test in Step 2 required a `_load_session_context` helper, extract the two gather lines into that function and call it from the route handler.

### Step 5 — Run test to verify it passes

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/test_chat_api.py::test_startup_io_calls_are_concurrent -v
```

Expected: **PASS** — elapsed < 0.09s.

### Step 6 — Run full test suite

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/backend
python -m pytest tests/ -v --timeout=60 2>&1 | tail -20
```

Expected: no new failures.

### Step 7 — Commit

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode
git add backend/app/api/v1/chat.py backend/tests/test_chat_api.py
git commit -m "perf: parallelise halt-state and conversation-history loading

Replace two sequential awaits at request startup with asyncio.gather,
saving ~300-500ms cold-start latency on every chat request."
```

---

## Task 3 — Welcome screen suggestion chips auto-send on click

Currently the three suggestion buttons on the welcome screen only populate the input field. Users must then manually press Enter or click Send. Every other AI chat product auto-sends on chip click — this is extra friction.

**Files:**
- Modify: `frontend/components/ChatContainer.tsx` — lines ~735–745 (welcome screen suggestion buttons)

---

### Step 1 — Read the current code

Open `frontend/components/ChatContainer.tsx` around line 735. The buttons look like:

```tsx
{['Best wireless earbuds under $100', 'Plan a 5-day trip to Tokyo', 'Compare MacBook Air vs Pro'].map((suggestion, idx) => (
  <button
    key={idx}
    onClick={() => {
      setInput(suggestion)   // ← only sets the input, does NOT send
    }}
    className="..."
  >
    {suggestion}
  </button>
))}
```

### Step 2 — Implement the fix

Change the `onClick` to call both `setInput` and then `handleSendMessage` immediately, passing the suggestion text directly:

```tsx
{['Best wireless earbuds under $100', 'Plan a 5-day trip to Tokyo', 'Compare MacBook Air vs Pro'].map((suggestion, idx) => (
  <button
    key={idx}
    onClick={() => {
      setInput(suggestion)
      // Small timeout lets React flush the input state before handleSendMessage reads it.
      // Alternatively pass the message directly if handleSendMessage accepts a parameter.
      setTimeout(() => handleSendMessage(suggestion), 0)
    }}
    className="..."
  >
    {suggestion}
  </button>
))}
```

> **Check first:** Read the `handleSendMessage` function signature. If it already accepts an optional `messageOverride` string parameter (or similar), pass the suggestion directly. If it reads from the `input` state variable, the `setTimeout` pattern is necessary to let React flush. Use whichever approach matches the existing signature.

### Step 3 — TypeScript check

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/frontend
npx tsc --noEmit 2>&1 | grep -v "tests/" | head -20
```

Expected: **no errors** in production source files.

### Step 4 — Verify in browser

1. Start frontend: `cd frontend && npm run dev`
2. Open http://localhost:3000/chat
3. Click "Best wireless earbuds under $100"
4. **Expected:** message auto-sends immediately without pressing Enter

### Step 5 — Commit

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode
git add frontend/components/ChatContainer.tsx
git commit -m "ux: welcome suggestion chips auto-send on click

Clicking a suggestion chip now immediately sends the query instead of
only populating the input box, removing the extra Enter-press step."
```

---

## Task 4 — Fix suggestion chip category label readability

The category label above each follow-up suggestion (e.g. `PRODUCT`, `COMPARE`, `REFINE_BUDGET`) renders at **10px uppercase** — too small to read, especially on mobile. Map the raw category codes to friendly human-readable labels and increase the font to 11px.

**Files:**
- Modify: `frontend/components/Message.tsx` — lines ~261–268 (category label render)

---

### Step 1 — Read the current code

Open `frontend/components/Message.tsx` around line 261. The label renders as:

```tsx
<span className="text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 ...">
  {suggestion.category}
</span>
```

`suggestion.category` is a raw string like `"refine_budget"`, `"compare"`, `"deeper_research"`, `"clarify"`, `"alternate_destination"`, `"refine_features"`.

Also check lines ~26–34 for any existing `CATEGORY_LABELS` map — if one already exists, update it. If not, create one.

### Step 2 — Implement the fix

Add a label map near the top of the component (or update the existing one):

```tsx
const CATEGORY_LABELS: Record<string, string> = {
  clarify: 'Clarify',
  compare: 'Compare',
  refine_budget: 'Budget',
  refine_features: 'Features',
  deeper_research: 'Deep dive',
  alternate_destination: 'Alternatives',
}
```

Update the label render:

```tsx
<span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 ...">
  {CATEGORY_LABELS[suggestion.category] ?? suggestion.category}
</span>
```

Changes made:
- Font: `text-[10px]` → `text-[11px]`
- Tracking: `tracking-widest` → `tracking-wider` (slightly tighter for readability)
- Text: raw category code → human-readable label with fallback

### Step 3 — TypeScript check

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/frontend
npx tsc --noEmit 2>&1 | grep -v "tests/" | head -20
```

Expected: **no errors**.

### Step 4 — Run frontend tests

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode/frontend
npm run test:run 2>&1 | tail -20
```

Expected: all existing tests pass (the label map doesn't affect test logic).

### Step 5 — Commit

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode
git add frontend/components/Message.tsx
git commit -m "ux: improve suggestion chip category label readability

Map raw category codes to human-readable labels (refine_budget → Budget,
deeper_research → Deep dive, etc.) and increase font from 10px to 11px."
```

---

## Final Step — Push

```bash
cd C:/Users/habib/downloads/Reviewguide-sourcecode
git push origin main
```

---

## Summary

| Task | Files | Type | Impact |
|------|-------|------|--------|
| 1. Fix `general_product_info` drop | `product_compose.py` | Bug fix | High — named product queries now return real answers |
| 2. Parallelise startup I/O | `chat.py` | Performance | ~300–500ms saved on every request |
| 3. Suggestion chips auto-send | `ChatContainer.tsx` | UX | Removes friction on welcome screen |
| 4. Chip label readability | `Message.tsx` | UX / Accessibility | Smaller type, cleaner labels |
