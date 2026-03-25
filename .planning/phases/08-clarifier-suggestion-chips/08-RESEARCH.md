# Phase 8: Clarifier Suggestion Chips - Research

**Researched:** 2026-03-25
**Domain:** Backend clarifier agent + frontend chip rendering (full-stack feature)
**Confidence:** HIGH

## Summary

This phase adds tappable suggestion chips to clarifier agent responses so users can answer clarifying questions with a single tap instead of typing. The implementation touches three layers: (1) the backend clarifier agent must generate chip options alongside each follow-up question, (2) the GraphState TypedDict must include a `clarifier_chips` field with a default in `initial_state`, and (3) the frontend Message.tsx component must render chips below clarifier follow-up questions using the existing `sendSuggestion` CustomEvent pattern.

The codebase already has all the plumbing needed. The clarifier agent already generates structured followup data (`{intro, questions: [{slot, question}], closing}`), the frontend already renders these as clickable buttons in Message.tsx (lines 217-249), and the `sendSuggestion` CustomEvent pattern already works for both follow-up questions and next_suggestion chips. The key missing piece is that the clarifier does NOT generate multiple-choice answer options for each question -- it only generates the question text. This phase adds those answer options.

**Primary recommendation:** Extend the clarifier agent's LLM prompt to generate 2-4 `chips` (short answer options) per follow-up question, pass them through GraphState and the SSE stream, and render them as styled pill buttons in Message.tsx using the established `sendSuggestion` dispatch pattern.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UX-01 | A clarifier agent response includes 2-4 suggestion chips below the prose question | Clarifier agent `_generate_followup_questions` method already returns structured JSON from LLM; extend prompt to include `chips` array per question. Frontend already renders followup questions as buttons -- add chip sub-buttons beneath each. |
| UX-02 | Tapping a chip sends its text as the user's reply without typing | The `sendSuggestion` CustomEvent pattern is already implemented in Message.tsx and handled by ChatContainer.tsx (lines 650-661). Chip click handler follows identical pattern. |
</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| LangGraph | current | Agent workflow state machine | Already powers all agent state flow |
| FastAPI | current | Backend API with SSE streaming | Already serves chat endpoint |
| Next.js 14 | 14.x | Frontend framework | Already renders all chat UI |
| React 18 | 18.x | Component rendering | Already used for Message.tsx |
| Tailwind CSS | current | Styling | Already used for Editorial Luxury theme |

### Supporting (already in project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| framer-motion | current | Animation | Already wraps Message component |
| lucide-react | current | Icons (ArrowRight) | Already used in followup buttons |

### No New Dependencies Required
This feature requires zero new libraries. Everything is built using existing patterns.

## Architecture Patterns

### End-to-End Data Flow (Existing)

```
Clarifier Agent
  -> _generate_followup_questions() returns {intro, questions: [{slot, question}], closing}
  -> clarifier_node() sets assistant_text = structured data, status = "halted"
  -> chat.py detects halted state, sets followups_to_send = result_state["assistant_text"]
  -> SSE done event sends followups field to frontend
  -> ChatContainer onComplete callback attaches followups to message
  -> Message.tsx renders followups as clickable buttons
  -> Click dispatches sendSuggestion CustomEvent
  -> ChatContainer handleSuggestionClick sends message with "You chose:" prefix
```

### Extended Data Flow (New -- Chips Added)

```
Clarifier Agent
  -> _generate_followup_questions() returns {intro, questions: [{slot, question, chips: ["opt1", "opt2", ...]}], closing}
  -> Same flow as above -- chips ride along in the structured followup data
  -> Message.tsx renders chips as pill buttons BELOW each question
  -> Click dispatches sendSuggestion with chip text as the question
```

### Pattern 1: GraphState Field Addition
**What:** Add `clarifier_chips` field to GraphState TypedDict and initial_state
**When to use:** Required to prevent LangGraph channel crashes on existing sessions
**Critical note from CLAUDE.md memory:** "When adding fields to GraphState TypedDict, MUST also add default value to initial_state dict in chat.py (~line 243) or LangGraph channels crash."

```python
# In backend/app/schemas/graph_state.py (GraphState TypedDict)
clarifier_chips: List[Dict[str, Any]]  # Chip options per clarifier question

# In backend/app/api/v1/chat.py (initial_state dict, ~line 295)
"clarifier_chips": [],  # Default empty list
```

### Pattern 2: LLM Prompt Extension
**What:** Extend the clarifier's `_generate_followup_questions` system prompt to generate chip options
**When to use:** In `clarifier_agent.py` `_generate_followup_questions` method (line 606)
**Example:**

```python
# Current JSON schema in prompt:
# {
#   "intro": "<your generated intro>",
#   "questions": [
#     {"slot": "<slot_name>", "question": "<your question>"},
#   ],
#   "closing": "<your generated closing>"
# }

# New JSON schema in prompt:
# {
#   "intro": "<your generated intro>",
#   "questions": [
#     {
#       "slot": "<slot_name>",
#       "question": "<your question>",
#       "chips": ["<option 1>", "<option 2>", "<option 3>"]
#     },
#   ],
#   "closing": "<your generated closing>"
# }
```

### Pattern 3: Frontend Chip Rendering
**What:** Render chips as horizontal pill buttons below each follow-up question
**When to use:** In Message.tsx, inside the existing followups rendering block (lines 217-249)
**Example:**

```tsx
// Source: existing pattern from next_suggestions chips (Message.tsx lines 268-291)
// Chips should use the same sendSuggestion CustomEvent pattern:
{q.chips && q.chips.length > 0 && (
  <div className="flex flex-row flex-wrap gap-2 mt-2">
    {q.chips.map((chip: string, chipIdx: number) => (
      <button
        key={chipIdx}
        className="rounded-[20px] border border-[var(--primary)] text-[var(--primary)] bg-transparent px-3 py-1.5 text-[12px] font-medium transition-all hover:bg-[var(--primary-light)]"
        onClick={() => {
          const event = new CustomEvent('sendSuggestion', {
            detail: { question: chip }
          })
          window.dispatchEvent(event)
        }}
      >
        {chip}
      </button>
    ))}
  </div>
)}
```

### Anti-Patterns to Avoid
- **Do NOT create a separate component for clarifier chips:** The rendering is 10-15 lines inside existing Message.tsx followups block. Extracting it adds indirection for no benefit.
- **Do NOT add a new SSE event type:** Chips ride inside the existing `followups` structured data. No new wire protocol needed.
- **Do NOT modify the sendSuggestion CustomEvent handler:** The existing handler in ChatContainer already handles any text dispatched through this pattern.
- **Do NOT modify streaming logic in ChatContainer:** The chips are part of the followups data already handled by onComplete callback.
- **Do NOT use clarifier_chips GraphState field for rendering:** The chips travel inside `assistant_text` (the structured followup dict) which becomes `followups` on the frontend. The GraphState field is only needed for potential future use (e.g., logging, analytics). The actual rendering data flows through the existing `followups` path.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chip click handling | Custom click handler with new API call | Existing `sendSuggestion` CustomEvent + `handleSuggestionClick` in ChatContainer | Pattern already works, tested, handles streaming state correctly |
| Chip styling | Custom CSS classes | Existing Editorial Luxury CSS variables (`--primary`, `--primary-light`, `--border`) with same pattern as next_suggestion chips | Consistency with established design system |
| Structured data transport | New GraphState field + new SSE event | Extend existing structured followup data format that already flows through `assistant_text` -> `followups` | Path already works end-to-end, no new plumbing needed |

**Key insight:** This feature is a minimal extension of two existing patterns (structured followups and next_suggestion chips). Nearly all infrastructure exists. The new code is: (1) ~15 lines of prompt changes in clarifier_agent.py, (2) ~1 line in GraphState, (3) ~1 line in initial_state, (4) ~10-15 lines of chip rendering in Message.tsx, (5) update the FollowupQuestion TypeScript interface to include optional `chips` field.

## Common Pitfalls

### Pitfall 1: LangGraph Channel Crash on Missing Default
**What goes wrong:** Adding a field to GraphState TypedDict without adding a default in initial_state causes LangGraph to crash with a channel initialization error on ALL requests.
**Why it happens:** LangGraph uses TypedDict fields as channel names and requires every channel to have an initial value.
**How to avoid:** Add `"clarifier_chips": []` to the initial_state dict in `chat.py` (line ~295-353) at the same time as adding to GraphState.
**Warning signs:** Backend logs show channel/key errors immediately after deployment.

### Pitfall 2: Chips Showing Empty for Non-Clarifier Responses
**What goes wrong:** If the LLM omits the `chips` key from its JSON response, frontend code crashes or renders empty containers.
**Why it happens:** LLM JSON output is not guaranteed to include optional fields.
**How to avoid:** (1) Use optional chaining in frontend: `q.chips && q.chips.length > 0`, (2) In the backend fallback (clarifier_agent.py line 671-675), include `chips: []` in fallback questions, (3) The prompt should specify chips are required per question.
**Warning signs:** Console errors about accessing properties of undefined.

### Pitfall 3: Chip Text Too Long for Pill Buttons
**What goes wrong:** LLM generates verbose chip text that wraps and looks ugly as pills.
**Why it happens:** Without explicit length guidance, LLM generates natural-language phrases.
**How to avoid:** Prompt must specify "2-6 words per chip" and provide examples. Add `max_length` guidance in the system prompt.
**Warning signs:** Chips wrapping to multiple lines on mobile.

### Pitfall 4: Clarifier Question Already Contains Answer Options in Text
**What goes wrong:** The clarifier asks "Are you looking for vacuums, hair dryers, or fans?" AND shows chips for the same options, creating redundancy.
**Why it happens:** The question text and chip options are generated together but the question may naturally contain the options.
**How to avoid:** The prompt should instruct the LLM to keep the question brief and put the options in chips only, not in the question text.
**Warning signs:** Repeated text between question prose and chip labels.

### Pitfall 5: TypeScript Interface Out of Sync
**What goes wrong:** The FollowupQuestion interface in ChatContainer.tsx (line 18-21) does not include `chips`, so TypeScript may strip it during type checking.
**Why it happens:** The interface is explicitly typed but the data flows through `any` types in the SSE parsing.
**How to avoid:** Update the `FollowupQuestion` interface to include `chips?: string[]`.
**Warning signs:** TypeScript build warnings, chips data present in network tab but not rendered.

## Code Examples

### Backend: Extended LLM Prompt (clarifier_agent.py)

```python
# Source: backend/app/agents/clarifier_agent.py, _generate_followup_questions method
# Current return format from LLM:
# {"intro": "...", "questions": [{"slot": "budget", "question": "What's your budget?"}], "closing": "..."}

# New return format from LLM:
# {"intro": "...", "questions": [{"slot": "budget", "question": "What's your budget range?", "chips": ["Under $100", "$100-$300", "$300-$500", "Over $500"]}], "closing": "..."}

# Add to system prompt (line ~606-635):
# For each question, also include "chips": an array of 2-4 short answer options (2-6 words each).
# These appear as tappable buttons so users can answer in one tap.
# Keep chip text concise and mutually exclusive.
# Example: for budget, use ["Under $100", "$100-$300", "$300+"]
# Example: for category, use ["Vacuums", "Hair dryers", "Air purifiers"]
```

### Backend: GraphState Addition

```python
# Source: backend/app/schemas/graph_state.py
# Add to GraphState TypedDict:
clarifier_chips: List[Dict[str, Any]]  # Chip options from clarifier [{slot, chips: [...]}]
```

### Backend: initial_state Default

```python
# Source: backend/app/api/v1/chat.py, ~line 295
# Add to initial_state dict:
"clarifier_chips": [],
```

### Frontend: TypeScript Interface Update

```typescript
// Source: frontend/components/ChatContainer.tsx, line 18-21
export interface FollowupQuestion {
  slot: string
  question: string
  chips?: string[]  // NEW: tappable answer options
}
```

### Frontend: Chip Rendering in Message.tsx

```tsx
// Source: frontend/components/Message.tsx, inside followups rendering block (after line 236)
// Add after the question button, inside the same map:
{q.chips && q.chips.length > 0 && (
  <div className="flex flex-row flex-wrap gap-1.5 mt-1.5 ml-3.5">
    {q.chips.map((chip: string, chipIdx: number) => (
      <button
        key={chipIdx}
        data-testid={`clarifier-chip-${idx}-${chipIdx}`}
        className="rounded-[20px] border border-[var(--primary)] text-[var(--primary)] bg-transparent px-3 py-1 text-[12px] font-medium transition-all hover:bg-[var(--primary-light)]"
        onClick={() => {
          const event = new CustomEvent('sendSuggestion', {
            detail: { question: chip }
          })
          window.dispatchEvent(event)
        }}
      >
        {chip}
      </button>
    ))}
  </div>
)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Clarifier shows plain text question, user must type answer | Clarifier shows question + tappable chips, user can tap to answer | This phase | Dramatically reduces friction for clarifier interactions |
| Followup questions are full-width buttons (current) | Followup questions retain full-width format; chips appear as small pills below each question | This phase | Users can either tap a chip for a quick answer or tap the question to answer with custom text |

**Existing patterns preserved:**
- `sendSuggestion` CustomEvent dispatch (Message.tsx + ChatContainer.tsx) -- unchanged
- Structured followups data format (`{intro, questions, closing}`) -- extended with `chips` key
- SSE streaming protocol -- unchanged, chips ride inside existing followups payload
- Editorial Luxury theme variables -- reused for chip styling

## Open Questions

1. **Should tapping a clarifier chip answer ONLY that one question, or all questions at once?**
   - What we know: Currently the clarifier presents ALL missing-slot questions at once and expects a single free-form answer. The slot extraction LLM (`_extract_all_slots_from_answer`) tries to extract all slots from one message.
   - What's unclear: If user taps ONE chip (e.g., "Under $100" for budget), it sends only that text. The other questions remain unanswered. The slot extractor may only fill the budget slot and the clarifier will re-halt for remaining slots.
   - Recommendation: This is fine -- the existing multi-turn flow handles this. If 2 of 3 slots are filled, the clarifier generates a new question for the remaining slot. The chip click sends "Under $100" which the extractor maps to the budget slot, then the clarifier loops to ask the next question with new chips. This is actually better UX -- one question at a time with chips.

2. **Should chips be generated for ALL slot types or only common ones?**
   - What we know: Budget, category, brand, and use_case slots have predictable option spaces. Slots like "destination" or "product_name" are open-ended.
   - What's unclear: Whether the LLM can generate useful chips for open-ended slots.
   - Recommendation: Let the LLM decide. The prompt should say "include chips for questions where predefined options make sense. For open-ended questions like specific product names or destinations, omit chips." The frontend already handles `chips` being absent or empty.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (frontend) | Vitest + @testing-library/react |
| Config file (frontend) | `frontend/vitest.config.ts` |
| Quick run command (frontend) | `cd frontend && npx vitest run tests/suggestions.test.tsx` |
| Framework (backend) | pytest + asyncio |
| Config file (backend) | `backend/pytest.ini` |
| Quick run command (backend) | `cd backend && python -m pytest tests/test_chat_streaming.py -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UX-01 | Clarifier response includes 2-4 chips per question | unit (backend) | `cd backend && python -m pytest tests/test_clarifier_chips.py::test_chips_in_followup_response -x` | No -- Wave 0 |
| UX-01 | Chips render below followup questions in frontend | unit (frontend) | `cd frontend && npx vitest run tests/clarifierChips.test.tsx` | No -- Wave 0 |
| UX-02 | Tapping chip dispatches sendSuggestion with chip text | unit (frontend) | `cd frontend && npx vitest run tests/clarifierChips.test.tsx` | No -- Wave 0 |
| UX-02 | GraphState clarifier_chips field has default value | unit (backend) | `cd backend && python -m pytest tests/test_clarifier_chips.py::test_graph_state_default -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd frontend && npx vitest run tests/clarifierChips.test.tsx`
- **Per wave merge:** `cd frontend && npx vitest run && cd ../backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/tests/clarifierChips.test.tsx` -- covers UX-01 (chip rendering) and UX-02 (chip click dispatch)
- [ ] `backend/tests/test_clarifier_chips.py` -- covers UX-01 (LLM generates chips) and UX-02 (GraphState default)

## Sources

### Primary (HIGH confidence)
- `backend/app/agents/clarifier_agent.py` -- Complete clarifier agent with `_generate_followup_questions` method (line 557-676)
- `backend/app/schemas/graph_state.py` -- GraphState TypedDict definition (all fields, line 11-109)
- `backend/app/api/v1/chat.py` -- initial_state dict (lines 295-353), followups pass-through (lines 621-626, 716)
- `backend/app/services/halt_state_manager.py` -- Redis halt state with followups persistence
- `frontend/components/Message.tsx` -- Followup question rendering (lines 217-249), next_suggestions chips (lines 268-291)
- `frontend/components/ChatContainer.tsx` -- Message type with FollowupQuestion interface (lines 18-21), sendSuggestion handler (lines 650-661), handleSuggestionClick (lines 625-643)
- `frontend/lib/chatApi.ts` -- StreamChunk with followups field (line 79), SSE done event handling (lines 341-363)
- `CLAUDE.md` -- GraphState initialization requirement ("MUST also add default value to initial_state dict")

### Secondary (MEDIUM confidence)
- `frontend/tests/suggestions.test.tsx` -- Existing test patterns for chip rendering and click dispatch (used as template for new tests)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No new dependencies; all existing libraries verified in codebase
- Architecture: HIGH -- End-to-end data flow traced through actual source code; all integration points identified
- Pitfalls: HIGH -- GraphState crash pitfall documented in project memory (CLAUDE.md); other pitfalls derived from code inspection
- Code examples: HIGH -- All examples derived from actual codebase patterns, not hypothetical

**Research date:** 2026-03-25
**Valid until:** Indefinite (stable codebase patterns, no external dependency changes)
