# Phase A: Fast Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 3 serial LLM agent calls (Intent + Planner + Clarifier) with a single deterministic fast router, cutting first-content latency from ~15s to ~5-8s.

**Architecture:** New `fast_router.py` service uses keyword/regex rules (Tier 1, <5ms) with a Haiku 4.5 LLM fallback (Tier 2, ~300ms) for ambiguous queries. Returns intent + slots + hardcoded tool chain in one pass. Gated by `USE_FAST_ROUTER` feature flag — when false, existing agents run unchanged.

**Tech Stack:** Python 3.11, FastAPI, LangGraph, regex, pytest. No new dependencies for Tier 1. Anthropic SDK (`anthropic`) added for Tier 2 Haiku fallback.

**Spec:** `docs/superpowers/specs/2026-03-25-sub-3s-response-architecture-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `backend/app/services/fast_router.py` | Deterministic intent classification + slot extraction + tool chain selection |
| Create | `backend/tests/test_fast_router.py` | Unit tests for fast router (keyword rules, slot extraction, tool chains) |
| Modify | `backend/app/core/config.py` | Add `USE_FAST_ROUTER` feature flag and `ANTHROPIC_API_KEY` setting |
| Modify | `backend/app/services/langgraph/workflow.py` | Wire fast router bypass into safety node when flag is on |
| Modify | `backend/app/schemas/graph_state.py` | Add `routing_mode` field to track fast vs legacy path |
| Modify | `backend/app/api/v1/chat.py` | Add `routing_mode` to initial_state default |

---

## Task 1: Add Feature Flag and Config Settings

**Files:**
- Modify: `backend/app/core/config.py` (add after line ~265, near other feature flags)
- Modify: `backend/app/schemas/graph_state.py` (add routing_mode field)
- Modify: `backend/app/api/v1/chat.py` (add routing_mode to initial_state)

- [ ] **Step 1: Add config settings**

In `backend/app/core/config.py`, find the feature flags section (near `USE_CURATED_LINKS`) and add:

```python
# Fast Router (Phase A - sub-3s architecture)
USE_FAST_ROUTER: bool = Field(
    default=False,
    description="Bypass intent/planner/clarifier agents with deterministic fast router"
)
ANTHROPIC_API_KEY: str = Field(
    default="",
    description="Anthropic API key for Haiku fallback in fast router"
)
FAST_ROUTER_MODEL: str = Field(
    default="claude-haiku-4-5-20251001",
    description="Model for fast router Tier 2 fallback"
)
```

- [ ] **Step 2: Add routing_mode to GraphState**

In `backend/app/schemas/graph_state.py`, add after the `plan` field:

```python
routing_mode: Optional[str]  # "fast" or "legacy" — tracks which path was taken
```

- [ ] **Step 3: Add routing_mode to initial_state in chat.py**

In `backend/app/api/v1/chat.py`, find the initial_state dict construction (~line 295-349) and add:

```python
"routing_mode": None,
```

This prevents LangGraph channel crashes per the GraphState init rule.

- [ ] **Step 4: Run existing tests to verify nothing broke**

Run: `cd backend && python -m pytest tests/test_query_complexity.py tests/test_chat_api.py -v --timeout=30`
Expected: All existing tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/app/schemas/graph_state.py backend/app/api/v1/chat.py
git commit -m "feat(phase-a): add USE_FAST_ROUTER flag and routing_mode GraphState field"
```

---

## Task 2: Build Fast Router — Keyword Classification (Tier 1)

**Files:**
- Create: `backend/app/services/fast_router.py`
- Create: `backend/tests/test_fast_router.py`

- [ ] **Step 1: Write failing tests for Tier 1 keyword classification**

Create `backend/tests/test_fast_router.py`:

```python
"""Tests for fast_router deterministic intent classification and slot extraction."""
import pytest


class TestTier1KeywordClassification:
    """Tier 1: Deterministic keyword/regex rules (<5ms, ~60% of queries)."""

    @pytest.mark.parametrize("query,expected_intent", [
        # Product intent — "best X", "buy X", "recommend X"
        ("best noise cancelling headphones", "product"),
        ("buy a laptop for college", "product"),
        ("recommend me a good vacuum", "product"),
        ("top rated espresso machines under $500", "product"),
        ("what's the best phone right now", "product"),
        # Comparison intent — "X vs Y", "compare"
        ("sony wh-1000xm5 vs bose qc ultra", "comparison"),
        ("compare airpods pro and galaxy buds", "comparison"),
        ("which is better dyson or shark", "comparison"),
        # Travel intent — "trip to", "hotels in", "flights"
        ("plan a 5 day trip to tokyo", "travel"),
        ("best hotels in paris for couples", "travel"),
        ("cheap flights from nyc to london", "travel"),
        ("things to do in barcelona", "travel"),
        # Intro intent — greetings
        ("hello", "intro"),
        ("hey there", "intro"),
        ("hi what can you do", "intro"),
        # General intent — informational (matches _GENERAL_KEYWORDS)
        ("what is machine learning", "general"),
        ("how does bluetooth work", "general"),
        ("explain how noise cancellation works", "general"),
        # Service intent — service keyword + product keyword co-occurrence → service wins
        ("best vpn service", "service"),
        ("recommend a good streaming service", "service"),
        ("top rated insurance plan", "service"),
    ])
    def test_keyword_classification(self, query, expected_intent):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync(query, [], None)
        assert result.intent == expected_intent, (
            f"Query '{query}' classified as '{result.intent}', expected '{expected_intent}'"
        )

    def test_returns_tool_chain(self):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("best headphones under $200", [], None)
        assert result.intent == "product"
        assert "product_search" in result.tool_chain
        assert "product_compose" in result.tool_chain

    def test_returns_confidence(self):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("best headphones", [], None)
        assert result.confidence >= 0.8  # Tier 1 should be high confidence

    def test_ambiguous_query_low_confidence(self):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("tell me about that thing", [], None)
        assert result.confidence < 0.6  # Ambiguous → low confidence → Tier 2 needed


class TestSlotExtraction:
    """Regex-based slot extraction from query text."""

    def test_budget_under_pattern(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("best headphones under $200")
        assert slots["max_budget"] == 200

    def test_budget_range_pattern(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("laptops between $500 and $1000")
        assert slots["min_budget"] == 500
        assert slots["max_budget"] == 1000

    def test_brand_extraction(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("best sony headphones")
        assert slots["brand"] == "sony"

    def test_category_extraction(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("best robot vacuum for pet hair")
        assert slots["category"] == "robot vacuum"

    def test_travel_destination(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("plan a trip to Tokyo")
        assert slots["destination"] == "Tokyo"

    def test_no_slots_extracted(self):
        from app.services.fast_router import extract_slots
        slots = extract_slots("hello")
        assert slots == {} or all(v is None for v in slots.values() if v is not None)


class TestToolChains:
    """Hardcoded tool chains per intent."""

    @pytest.mark.parametrize("intent,must_contain", [
        ("product", ["product_search", "product_normalize", "product_compose"]),
        ("comparison", ["product_search", "product_normalize", "product_comparison", "next_step_suggestion"]),
        ("service", ["product_search", "product_normalize", "product_compose"]),
        ("travel", ["travel_search_hotels", "travel_compose"]),
        ("general", ["general_search", "general_compose", "next_step_suggestion"]),
        ("intro", ["intro_compose"]),
        ("unclear", ["unclear_compose"]),
    ])
    def test_tool_chain_contents(self, intent, must_contain):
        from app.services.fast_router import TOOL_CHAINS
        chain = TOOL_CHAINS[intent]
        for tool in must_contain:
            assert tool in chain, f"Tool '{tool}' missing from '{intent}' chain: {chain}"


class TestPlanGeneration:
    """Fast router generates valid plan dicts compatible with PlanExecutor."""

    def test_plan_has_steps(self):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("best headphones under $200", [], None)
        assert "steps" in result.plan
        assert len(result.plan["steps"]) > 0

    def test_plan_step_format(self):
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("best headphones under $200", [], None)
        step = result.plan["steps"][0]
        assert "id" in step
        assert "tools" in step
        assert isinstance(step["tools"], list)

    def test_plan_respects_dependencies(self):
        """product_search must come before product_normalize in plan steps."""
        from app.services.fast_router import fast_router_sync
        result = fast_router_sync("best laptop", [], None)
        tools_in_order = []
        for step in result.plan["steps"]:
            tools_in_order.extend(step["tools"])
        search_idx = tools_in_order.index("product_search")
        normalize_idx = tools_in_order.index("product_normalize")
        assert search_idx < normalize_idx
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_fast_router.py -v --timeout=30 2>&1 | head -30`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.fast_router'`

- [ ] **Step 3: Implement fast_router.py**

Create `backend/app/services/fast_router.py`:

```python
"""
Fast Router — Deterministic intent classification + slot extraction.

Replaces 3 serial LLM agents (Intent, Planner, Clarifier) with:
- Tier 1: Keyword/regex rules (<5ms, ~60% of queries)
- Tier 2: Haiku 4.5 single LLM call (~300ms, ~40% of queries)

Gated by USE_FAST_ROUTER feature flag.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool chains — hardcoded per intent (replaces Planner LLM entirely)
# ---------------------------------------------------------------------------

TOOL_CHAINS: Dict[str, List[str]] = {
    "product": [
        "product_search", "product_normalize", "review_search",
        "product_affiliate", "product_compose", "next_step_suggestion",
    ],
    "comparison": [
        "product_search", "product_normalize",
        "product_affiliate", "product_comparison", "next_step_suggestion",
    ],
    "service": [
        "product_search", "product_normalize", "review_search",
        "product_affiliate", "product_compose", "next_step_suggestion",
    ],
    "travel": [
        "travel_itinerary", "travel_destination_facts",
        "travel_search_hotels", "travel_search_flights",
        "travel_compose", "next_step_suggestion",
    ],
    "general": ["general_search", "general_compose", "next_step_suggestion"],
    "intro": ["intro_compose"],
    "unclear": ["unclear_compose"],
}

# ---------------------------------------------------------------------------
# Plan templates — dependency-ordered steps for PlanExecutor
# ---------------------------------------------------------------------------

PLAN_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "product": [
        {"id": "step_1", "tools": ["product_search"], "parallel": False},
        {"id": "step_2", "tools": ["product_normalize", "review_search"], "parallel": True},
        {"id": "step_3", "tools": ["product_affiliate"], "parallel": False},
        {"id": "step_4", "tools": ["product_compose"], "parallel": False},
        {"id": "step_5", "tools": ["next_step_suggestion"], "parallel": False},
    ],
    "comparison": [
        {"id": "step_1", "tools": ["product_search"], "parallel": False},
        {"id": "step_2", "tools": ["product_normalize"], "parallel": False},
        {"id": "step_3", "tools": ["product_affiliate"], "parallel": False},
        {"id": "step_4", "tools": ["product_comparison"], "parallel": False},
        {"id": "step_5", "tools": ["next_step_suggestion"], "parallel": False},
    ],
    "service": [
        {"id": "step_1", "tools": ["product_search"], "parallel": False},
        {"id": "step_2", "tools": ["product_normalize", "review_search"], "parallel": True},
        {"id": "step_3", "tools": ["product_affiliate"], "parallel": False},
        {"id": "step_4", "tools": ["product_compose"], "parallel": False},
        {"id": "step_5", "tools": ["next_step_suggestion"], "parallel": False},
    ],
    "travel": [
        {"id": "step_1", "tools": ["travel_itinerary", "travel_destination_facts"], "parallel": True},
        {"id": "step_2", "tools": ["travel_search_hotels", "travel_search_flights"], "parallel": True},
        {"id": "step_3", "tools": ["travel_compose"], "parallel": False},
        {"id": "step_4", "tools": ["next_step_suggestion"], "parallel": False},
    ],
    "general": [
        {"id": "step_1", "tools": ["general_search"], "parallel": False},
        {"id": "step_2", "tools": ["general_compose"], "parallel": False},
        {"id": "step_3", "tools": ["next_step_suggestion"], "parallel": False},
    ],
    "intro": [
        {"id": "step_1", "tools": ["intro_compose"], "parallel": False},
    ],
    "unclear": [
        {"id": "step_1", "tools": ["unclear_compose"], "parallel": False},
    ],
}

# ---------------------------------------------------------------------------
# Keyword and pattern definitions
# ---------------------------------------------------------------------------

_PRODUCT_KEYWORDS = [
    "best", "buy", "recommend", "top rated", "top-rated", "review",
    "cheap", "affordable", "premium", "budget", "worth it",
    "which", "should i get", "looking for a", "looking for an",
    "need a", "need an", "want a", "want an", "shopping for",
]

_COMPARISON_KEYWORDS = [
    " vs ", " versus ", "compare", "comparison", "better than",
    "difference between", "which is better", "or should i",
]

_TRAVEL_KEYWORDS = [
    "trip to", "travel to", "visit", "vacation", "holiday",
    "hotels in", "hotel in", "flights to", "flights from",
    "things to do in", "itinerary", "plan a trip",
    "where to stay", "where to go", "destination",
]

_SERVICE_KEYWORDS = [
    "service", "subscription", "plan", "provider", "vpn",
    "streaming", "insurance", "warranty",
]

_GENERAL_KEYWORDS = [
    "what is", "what are", "how does", "how do", "how is",
    "explain", "define", "tell me about", "meaning of",
    "history of", "why does", "why do", "why is",
]

_INTRO_PATTERNS = [
    r"^(hi|hello|hey|howdy|greetings|yo|sup|what's up|whats up)\b",
    r"^(good (morning|afternoon|evening))\b",
    r"what can you (do|help)",
    r"how (do you|does this) work",
]

KNOWN_BRANDS = [
    "apple", "samsung", "sony", "google", "lg", "dell", "hp",
    "lenovo", "asus", "bose", "jabra", "anker", "canon", "nikon",
    "dyson", "shark", "roomba", "irobot", "kitchenaid", "breville",
    "ninja", "instant pot", "philips", "panasonic", "jbl", "beats",
    "sennheiser", "garmin", "fitbit", "microsoft", "acer",
]

KNOWN_CATEGORIES = [
    "headphones", "earbuds", "speaker", "bluetooth speaker",
    "laptop", "phone", "smartphone", "tablet", "monitor", "tv",
    "camera", "keyboard", "mouse", "router", "smartwatch",
    "vacuum", "robot vacuum", "air purifier", "air fryer",
    "espresso machine", "coffee maker", "blender", "toaster",
    "standing desk", "office chair", "mattress", "pillow",
    "running shoes", "hiking boots", "backpack", "luggage",
]

# Budget regex patterns
_BUDGET_UNDER = re.compile(r"under\s*\$?\s*(\d[\d,]*)", re.IGNORECASE)
_BUDGET_BELOW = re.compile(r"below\s*\$?\s*(\d[\d,]*)", re.IGNORECASE)
_BUDGET_MAX = re.compile(r"(?:less than|max|maximum|up to)\s*\$?\s*(\d[\d,]*)", re.IGNORECASE)
_BUDGET_RANGE = re.compile(
    r"(?:between\s+)?\$\s*(\d[\d,]*)\s*(?:-|to|and)\s*\$?\s*(\d[\d,]*)", re.IGNORECASE
)
_BUDGET_AROUND = re.compile(r"(?:around|about|roughly)\s*\$?\s*(\d[\d,]*)", re.IGNORECASE)

# Travel destination pattern (crude but effective for Tier 1)
_TRAVEL_DEST = re.compile(
    r"(?:trip to|travel to|visit|hotels? in|flights? to|things to do in|itinerary for|"
    r"vacation in|holiday in|where to stay in)\s+([A-Z][a-zA-Z\s]{2,20})",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class FastRouterResult:
    intent: str
    slots: Dict[str, Any]
    tool_chain: List[str]
    plan: Dict[str, Any]
    confidence: float
    tier: int  # 1 = keyword, 2 = Haiku LLM
    needs_clarification: bool = False


# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------

def extract_slots(query: str) -> Dict[str, Any]:
    """Extract structured slots from query using regex patterns."""
    slots: Dict[str, Any] = {}
    q_lower = query.lower()

    # Budget extraction
    m = _BUDGET_UNDER.search(query) or _BUDGET_BELOW.search(query) or _BUDGET_MAX.search(query)
    if m:
        slots["max_budget"] = int(m.group(1).replace(",", ""))
    else:
        m = _BUDGET_RANGE.search(query)
        if m:
            slots["min_budget"] = int(m.group(1).replace(",", ""))
            slots["max_budget"] = int(m.group(2).replace(",", ""))
        else:
            m = _BUDGET_AROUND.search(query)
            if m:
                val = int(m.group(1).replace(",", ""))
                slots["min_budget"] = int(val * 0.7)
                slots["max_budget"] = int(val * 1.3)

    # Brand extraction
    for brand in KNOWN_BRANDS:
        if brand in q_lower:
            slots["brand"] = brand
            break

    # Category extraction (longest match first)
    sorted_cats = sorted(KNOWN_CATEGORIES, key=len, reverse=True)
    for cat in sorted_cats:
        if cat in q_lower:
            slots["category"] = cat
            break

    # Travel destination
    m = _TRAVEL_DEST.search(query)
    if m:
        slots["destination"] = m.group(1).strip()

    return slots


# ---------------------------------------------------------------------------
# Tier 1: Deterministic keyword classification
# ---------------------------------------------------------------------------

def _classify_tier1(query: str, conversation_history: list, last_search_context: Optional[dict]) -> Optional[FastRouterResult]:
    """
    Tier 1: Keyword/regex classification. Returns None if not confident enough.
    """
    q_lower = query.lower().strip()

    # Follow-up detection: if we have active product context, bias toward product
    has_product_context = (
        last_search_context
        and last_search_context.get("product_names")
        and len(last_search_context["product_names"]) > 0
    )

    # Intro detection (highest priority — short greetings)
    if len(q_lower.split()) <= 6:
        for pattern in _INTRO_PATTERNS:
            if re.search(pattern, q_lower):
                return _build_result("intro", extract_slots(query), 0.95, tier=1)

    # Comparison detection (before product — "X vs Y" is comparison, not product)
    for kw in _COMPARISON_KEYWORDS:
        if kw in q_lower:
            return _build_result("comparison", extract_slots(query), 0.9, tier=1)

    # Travel detection
    for kw in _TRAVEL_KEYWORDS:
        if kw in q_lower:
            return _build_result("travel", extract_slots(query), 0.9, tier=1)

    # General detection (before product — "what is X" is informational, not a buy intent)
    for kw in _GENERAL_KEYWORDS:
        if kw in q_lower:
            return _build_result("general", extract_slots(query), 0.85, tier=1)

    # Service vs Product: check for co-occurrence first
    # "best vpn service" has both "best" (product) and "service" — service wins
    has_product_kw = any(kw in q_lower for kw in _PRODUCT_KEYWORDS)
    has_service_kw = any(kw in q_lower for kw in _SERVICE_KEYWORDS)

    if has_service_kw and has_product_kw:
        return _build_result("service", extract_slots(query), 0.8, tier=1)
    if has_service_kw:
        return _build_result("service", extract_slots(query), 0.8, tier=1)

    # Product detection
    if has_product_kw:
        return _build_result("product", extract_slots(query), 0.85, tier=1)

    # Follow-up with product context — assume product intent
    if has_product_context:
        return _build_result("product", extract_slots(query), 0.75, tier=1)

    # Not confident enough for Tier 1
    return None


def _build_result(intent: str, slots: dict, confidence: float, tier: int) -> FastRouterResult:
    """Build a FastRouterResult with the correct tool chain and plan."""
    tool_chain = TOOL_CHAINS.get(intent, TOOL_CHAINS["general"])
    plan_steps = PLAN_TEMPLATES.get(intent, PLAN_TEMPLATES["general"])
    plan = {"steps": [dict(step) for step in plan_steps]}  # deep copy
    return FastRouterResult(
        intent=intent,
        slots=slots,
        tool_chain=tool_chain,
        plan=plan,
        confidence=confidence,
        tier=tier,
    )


# ---------------------------------------------------------------------------
# Synchronous entry point (Tier 1 only — Tier 2 added in later task)
# ---------------------------------------------------------------------------

def fast_router_sync(
    query: str,
    conversation_history: list,
    last_search_context: Optional[dict],
) -> FastRouterResult:
    """
    Synchronous fast router. Tries Tier 1 (keyword), falls back to 'unclear'.

    This is the Tier 1-only version. Tier 2 (Haiku LLM) is added in Task 3.
    """
    result = _classify_tier1(query, conversation_history, last_search_context)
    if result:
        return result

    # Tier 1 couldn't classify — return unclear with low confidence
    # Tier 2 (Haiku) will override this when added
    return _build_result("unclear", extract_slots(query), 0.3, tier=1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_fast_router.py -v --timeout=30`
Expected: All tests pass except `test_ambiguous_query_low_confidence` (which tests Tier 2 fallback behavior — the unclear result should have confidence < 0.6, which our 0.3 satisfies).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/fast_router.py backend/tests/test_fast_router.py
git commit -m "feat(phase-a): fast router Tier 1 — keyword classification + slot extraction"
```

---

## Task 3: Add Haiku Tier 2 Fallback

**Files:**
- Modify: `backend/app/services/fast_router.py` (add async Tier 2)
- Modify: `backend/tests/test_fast_router.py` (add Tier 2 tests)

- [ ] **Step 1: Write failing tests for Tier 2**

Add to `backend/tests/test_fast_router.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestTier2HaikuFallback:
    """Tier 2: Haiku LLM fallback for ambiguous queries."""

    @pytest.mark.asyncio
    async def test_ambiguous_query_uses_tier2(self):
        """Queries that don't match Tier 1 keywords should hit Tier 2."""
        from app.services.fast_router import fast_router

        mock_response = {"intent": "product", "slots": {"category": "headphones"}}
        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, return_value=mock_response):
            result = await fast_router("tell me about those things for your ears", [], None)
            assert result.intent == "product"
            assert result.tier == 2

    @pytest.mark.asyncio
    async def test_tier1_hit_skips_tier2(self):
        """Clear product queries should NOT call Haiku."""
        from app.services.fast_router import fast_router

        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock) as mock_haiku:
            result = await fast_router("best headphones under $200", [], None)
            mock_haiku.assert_not_called()
            assert result.tier == 1

    @pytest.mark.asyncio
    async def test_tier2_failure_falls_back_to_general(self):
        """If Haiku call fails, fall back to general intent."""
        from app.services.fast_router import fast_router

        with patch("app.services.fast_router._call_haiku", new_callable=AsyncMock, side_effect=Exception("API error")):
            result = await fast_router("something weird and ambiguous", [], None)
            assert result.intent == "general"
            assert result.confidence < 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_fast_router.py::TestTier2HaikuFallback -v --timeout=30`
Expected: FAIL with `ImportError` (no `fast_router` async function yet)

- [ ] **Step 3: Add async fast_router and Haiku Tier 2**

Add to `backend/app/services/fast_router.py`:

```python
import json

# Add at top of file with other imports:
# import json


async def _call_haiku(
    query: str,
    conversation_history: list,
) -> Optional[Dict[str, Any]]:
    """
    Tier 2: Call Haiku 4.5 for intent + slot classification in one shot.
    Returns dict with 'intent' and 'slots' keys, or None on failure.
    """
    from app.core.config import settings

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, skipping Tier 2")
        return None

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_prompt = """You are a query classifier for ReviewGuide.ai, a product review and travel planning assistant.

Classify the user's query into exactly one intent and extract structured slots.

INTENTS:
- "product" — user wants to find, buy, or get recommendations for a physical product
- "comparison" — user wants to compare 2+ specific products
- "service" — user wants a service recommendation (VPN, streaming, insurance)
- "travel" — user wants trip planning, hotels, flights, or destination info
- "general" — user wants factual information, not to buy something
- "intro" — user is greeting or asking what the bot can do
- "unclear" — cannot determine intent

SLOTS (extract if present, omit if absent):
- "category": product category (e.g. "headphones", "laptop")
- "brand": specific brand mentioned
- "max_budget": maximum budget as integer
- "min_budget": minimum budget as integer
- "destination": travel destination
- "duration_days": trip duration as integer

Respond with ONLY valid JSON: {"intent": "...", "slots": {...}}"""

        # Build messages with conversation context
        messages = []
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": query})

        response = await client.messages.create(
            model=settings.FAST_ROUTER_MODEL,
            max_tokens=150,
            system=system_prompt,
            messages=messages,
        )

        text = response.content[0].text.strip()
        return json.loads(text)

    except Exception as e:
        logger.error(f"Haiku Tier 2 classification failed: {e}")
        return None


async def fast_router(
    query: str,
    conversation_history: list,
    last_search_context: Optional[dict],
) -> FastRouterResult:
    """
    Async fast router. Tries Tier 1 (keyword), then Tier 2 (Haiku).
    """
    # Tier 1: Deterministic
    result = _classify_tier1(query, conversation_history, last_search_context)
    if result:
        logger.info(f"Fast router Tier 1: intent={result.intent}, confidence={result.confidence}")
        return result

    # Tier 2: Haiku LLM
    try:
        haiku_result = await _call_haiku(query, conversation_history)
        if haiku_result and "intent" in haiku_result:
            intent = haiku_result["intent"]
            haiku_slots = haiku_result.get("slots", {})
            # Merge regex slots with Haiku slots (regex wins on conflict — more precise)
            merged_slots = {**haiku_slots, **extract_slots(query)}
            result = _build_result(intent, merged_slots, 0.75, tier=2)
            logger.info(f"Fast router Tier 2: intent={result.intent}, confidence={result.confidence}")
            return result
    except Exception as e:
        logger.error(f"Fast router Tier 2 failed: {e}")

    # Fallback: general with low confidence
    logger.warning(f"Fast router: all tiers failed for query: {query[:50]}")
    return _build_result("general", extract_slots(query), 0.3, tier=1)
```

- [ ] **Step 4: Run all fast router tests**

Run: `cd backend && python -m pytest tests/test_fast_router.py -v --timeout=30`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/fast_router.py backend/tests/test_fast_router.py
git commit -m "feat(phase-a): fast router Tier 2 — Haiku 4.5 LLM fallback for ambiguous queries"
```

---

## Task 4: Wire Fast Router into LangGraph Workflow

**Files:**
- Modify: `backend/app/services/langgraph/workflow.py` (add fast router bypass in safety node)
- Modify: `backend/tests/test_fast_router.py` (add integration test)

- [ ] **Step 1: Write failing integration test**

Add to `backend/tests/test_fast_router.py`:

```python
class TestWorkflowIntegration:
    """Test that fast router correctly sets GraphState fields for PlanExecutor."""

    def test_fast_router_sets_all_required_state(self):
        """Fast router result must set intent, plan, slots, next_agent, routing_mode."""
        from app.services.fast_router import fast_router_sync

        result = fast_router_sync("best headphones under $200", [], None)

        # Must set these for PlanExecutor compatibility
        assert result.intent is not None
        assert result.plan is not None
        assert "steps" in result.plan
        assert result.slots is not None

    def test_plan_executor_compatible_plan(self):
        """Plan format must match what PlanExecutor expects."""
        from app.services.fast_router import fast_router_sync

        result = fast_router_sync("best laptop for college", [], None)
        for step in result.plan["steps"]:
            assert "id" in step, "Step missing 'id'"
            assert "tools" in step, "Step missing 'tools'"
            assert isinstance(step["tools"], list), "Step 'tools' must be a list"
            for tool in step["tools"]:
                assert isinstance(tool, str), f"Tool must be string, got {type(tool)}"
```

- [ ] **Step 2: Run test to verify it passes (it should — format is already correct)**

Run: `cd backend && python -m pytest tests/test_fast_router.py::TestWorkflowIntegration -v --timeout=30`
Expected: PASS

- [ ] **Step 3: Wire fast router bypass into workflow.py**

Two changes are needed in `backend/app/services/langgraph/workflow.py`:

**Change 1: Add `plan_executor` routing edge from safety node.**

In `build_workflow()` (~line 516), find the conditional edges from `agent_safety`. Add `"plan_executor"` to the edge map:

```python
# Find this block (around line 516-525):
workflow.add_conditional_edges("agent_safety", route_next_agent, {
    "intent": "agent_intent",
    "clarifier": "agent_clarifier",
    "tiered_executor": "tiered_executor",
    END: END,
})

# Change it to:
workflow.add_conditional_edges("agent_safety", route_next_agent, {
    "intent": "agent_intent",
    "clarifier": "agent_clarifier",
    "tiered_executor": "tiered_executor",
    "plan_executor": "agent_plan_executor",  # <-- NEW: fast router bypass
    END: END,
})
```

**Change 2: Add fast router bypass AFTER safety node returns.**

The safety node uses `run_stage_with_budget()` which returns an `update` dict. The fast router bypass should be applied to this `update` dict AFTER it returns, not inside the inner coroutine. Find the safety node wrapper function (~line 50-172) and add the bypass after the `run_stage_with_budget` call returns:

```python
# Add import at top of file
from app.services.fast_router import fast_router_sync
from app.core.config import settings

# Inside the safety node function, AFTER run_stage_with_budget returns `update`,
# and BEFORE the function returns `update`:

# Fast router bypass: if enabled and this is a normal (non-resume) path
if (
    settings.USE_FAST_ROUTER
    and update.get("next_agent") == "intent"  # Only on fresh queries, not resumes
):
    try:
        router_result = fast_router_sync(
            state.get("user_message", ""),
            state.get("conversation_history", []),
            state.get("last_search_context"),
        )
        update["intent"] = router_result.intent
        # Merge: existing state slots (e.g. country_code) take precedence over regex
        update["slots"] = {**router_result.slots, **state.get("slots", {})}
        update["plan"] = router_result.plan
        update["routing_mode"] = "fast"
        update["next_agent"] = "plan_executor"
        logger.info(
            f"Fast router: intent={router_result.intent}, "
            f"tier={router_result.tier}, confidence={router_result.confidence:.2f}"
        )
    except Exception as e:
        logger.error(f"Fast router failed, falling back to legacy: {e}")
        update["routing_mode"] = "legacy"
        # next_agent stays "intent" — legacy path runs
else:
    update["routing_mode"] = update.get("routing_mode", "legacy")
```

**Why `update.get("next_agent") == "intent"` is the correct guard:**
- On fresh queries: safety sets `next_agent = "intent"` → fast router intercepts.
- On halt resume with followups: safety sets `next_agent = "clarifier"` → not "intent" → fast router skips.
- On consent resume: safety sets `next_agent = "tiered_executor"` → not "intent" → fast router skips.
- On safety block: safety sets `status = "error"` and `next_agent = END` → not "intent" → fast router skips.

This approach requires NO changes to the inner `_run_safety()` coroutine — it operates purely on the returned update dict.

- [ ] **Step 4: Run existing workflow tests to verify nothing broke**

Run: `cd backend && python -m pytest tests/ -v --timeout=60 -k "not test_tiered" 2>&1 | tail -20`
Expected: All existing tests pass (USE_FAST_ROUTER defaults to False, so legacy path runs).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/langgraph/workflow.py backend/tests/test_fast_router.py
git commit -m "feat(phase-a): wire fast router bypass into LangGraph workflow"
```

---

## Task 5: End-to-End Validation

**Files:**
- Modify: `backend/tests/test_fast_router.py` (add E2E test)

- [ ] **Step 1: Write E2E test that enables the fast router flag**

Add to `backend/tests/test_fast_router.py`:

```python
from unittest.mock import patch


class TestEndToEnd:
    """End-to-end: enable USE_FAST_ROUTER and verify the full path works."""

    def test_fast_router_flag_off_uses_legacy(self):
        """When USE_FAST_ROUTER=False, routing_mode should be 'legacy' or None."""
        from app.services.fast_router import fast_router_sync
        # Just verify the sync function works independently
        result = fast_router_sync("best headphones", [], None)
        assert result.intent == "product"

    def test_fast_router_produces_valid_state_for_all_intents(self):
        """Every intent must produce a valid plan with at least one step."""
        from app.services.fast_router import fast_router_sync, TOOL_CHAINS

        test_queries = {
            "product": "best noise cancelling headphones under $300",
            "comparison": "sony xm5 vs bose qc ultra",
            "service": "best vpn service for streaming",
            "travel": "plan a 5 day trip to Tokyo",
            "general": "how does noise cancellation work",
            "intro": "hello",
        }

        for expected_intent, query in test_queries.items():
            result = fast_router_sync(query, [], None)
            assert result.intent == expected_intent, (
                f"Query '{query}' got intent '{result.intent}', expected '{expected_intent}'"
            )
            assert len(result.plan["steps"]) > 0, (
                f"Intent '{result.intent}' has empty plan"
            )
            # Verify all tools in plan exist in tool chain
            plan_tools = []
            for step in result.plan["steps"]:
                plan_tools.extend(step["tools"])
            for tool in plan_tools:
                assert tool in TOOL_CHAINS[result.intent], (
                    f"Tool '{tool}' in plan but not in chain for '{result.intent}'"
                )

    def test_slot_extraction_integrated(self):
        """Slots should be populated when query has extractable data."""
        from app.services.fast_router import fast_router_sync

        result = fast_router_sync("best sony headphones under $200", [], None)
        assert result.intent == "product"
        assert result.slots.get("brand") == "sony"
        assert result.slots.get("max_budget") == 200
        assert result.slots.get("category") == "headphones"

    def test_follow_up_with_product_context(self):
        """Follow-up query with active product context should route to product."""
        from app.services.fast_router import fast_router_sync

        context = {"product_names": ["Sony WH-1000XM5", "Bose QC Ultra"]}
        result = fast_router_sync("what about a cheaper one", [], context)
        assert result.intent == "product"
```

- [ ] **Step 2: Run all fast router tests**

Run: `cd backend && python -m pytest tests/test_fast_router.py -v --timeout=30`
Expected: All tests pass.

- [ ] **Step 3: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v --timeout=60 2>&1 | tail -30`
Expected: All tests pass. No regressions.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_fast_router.py
git commit -m "test(phase-a): end-to-end fast router validation tests"
```

---

## Task 6: Enable on Railway and Measure

**Files:** No code changes — Railway env var + measurement.

- [ ] **Step 1: Set Railway env var to enable fast router**

Using Railway MCP or Railway dashboard, set:
```
USE_FAST_ROUTER=true
```

Note: Also needs `ANTHROPIC_API_KEY` set for Tier 2 Haiku fallback. If not available yet, Tier 2 will gracefully degrade to "general" intent for ambiguous queries — Tier 1 still works.

- [ ] **Step 2: Deploy and test with 5 sample queries**

Test these queries on the live app and note time-to-first-content:

1. "best noise cancelling headphones under $200" (product, Tier 1)
2. "plan a 5 day trip to Tokyo" (travel, Tier 1)
3. "hello" (intro, Tier 1)
4. "sony xm5 vs bose qc ultra" (comparison, Tier 1)
5. "what's good for my morning routine" (ambiguous, Tier 2)

Record `stage_telemetry` from the `done` SSE event for each query — compare fast_dispatch time vs old safety+intent+planner+clarifier combined time.

- [ ] **Step 3: Commit measurement results as a note**

```bash
git commit --allow-empty -m "docs(phase-a): fast router deployed, measuring latency improvement"
```

---

## Summary

| Task | What It Does | Tests |
|------|-------------|-------|
| 1 | Feature flag + config + GraphState field | Verify existing tests pass |
| 2 | Fast router Tier 1 (keywords + regex + slots) | 20+ parametrized tests |
| 3 | Fast router Tier 2 (Haiku fallback) | Async mock tests |
| 4 | Wire into workflow.py | Integration + legacy compatibility |
| 5 | E2E validation | All intents, slots, follow-ups |
| 6 | Deploy + measure | Live latency comparison |

**Expected result:** Product queries skip 3 LLM calls (intent + planner + clarifier) and go directly from safety → plan_executor. Estimated improvement: **15s → 5-8s** to first content.
