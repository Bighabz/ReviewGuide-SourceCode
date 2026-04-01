"""
Fast Router - Tier 1 Keyword Classification + Tier 2 Haiku Fallback

Deterministic, zero-latency intent classification and slot extraction.
Tier 1: pure keyword/regex matching (no LLM calls).
Tier 2: Haiku LLM fallback for ambiguous queries that Tier 1 cannot classify.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool chains — flat ordered lists of tools per intent
# ---------------------------------------------------------------------------

TOOL_CHAINS: Dict[str, List[str]] = {
    "product": [
        "product_search",
        "product_normalize",
        "review_search",
        "product_affiliate",
        "product_compose",
        "next_step_suggestion",
    ],
    "comparison": [
        "product_search",
        "product_normalize",
        "product_affiliate",
        "product_comparison",
        "next_step_suggestion",
    ],
    "service": [
        "product_search",
        "product_normalize",
        "review_search",
        "product_affiliate",
        "product_compose",
        "next_step_suggestion",
    ],
    "travel": [
        "travel_itinerary",
        "travel_destination_facts",
        "travel_search_hotels",
        "travel_search_flights",
        "travel_compose",
        "next_step_suggestion",
    ],
    "general": [
        "general_search",
        "general_compose",
        "next_step_suggestion",
    ],
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
# Keyword lists
# ---------------------------------------------------------------------------

_PRODUCT_KEYWORDS: List[str] = [
    "best",
    "buy",
    "recommend",
    "top rated",
    "top picks",
    "top pick",
    "picks for",
    "review",
    "cheap",
    "affordable",
    "premium",
    "budget",
    "worth it",
    "which",
    "should i get",
    "looking for",
    "need a",
    "want a",
    "shopping for",
    "searching for",
    "in the market for",
    "where to buy",
    "price of",
    "how much",
    "ranked",
    "rating",
    "vs",
]

_COMPARISON_KEYWORDS: List[str] = [
    " vs ",
    " versus ",
    "compare",
    "comparison",
    "better than",
    "difference between",
    "which is better",
]

_TRAVEL_KEYWORDS: List[str] = [
    "trip to",
    "travel to",
    "visit",
    "vacation",
    "holiday",
    "hotels in",
    "flights to",
    "things to do in",
    "itinerary",
    "plan a trip",
    "where to stay",
    "destination",
]

_SERVICE_KEYWORDS: List[str] = [
    "service",
    "subscription",
    "provider",
    "vpn",
    "streaming",
    "insurance",
    "warranty",
]

_GENERAL_KEYWORDS: List[str] = [
    "what is",
    "what are",
    "how does",
    "how do",
    "explain",
    "define",
    "tell me about",
    "history of",
    "why does",
]

# Intro patterns — regex strings (will be compiled)
_INTRO_RAW_PATTERNS: List[str] = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^good\s+(?:morning|afternoon|evening)\b",
    r"^what can you (?:do|help)",
    r"^greetings\b",
    r"^howdy\b",
    r"^sup\b",
    r"^yo\b",
]

# Pre-compiled intro patterns (case-insensitive)
_INTRO_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in _INTRO_RAW_PATTERNS
]

# Known brands (lowercase for matching)
KNOWN_BRANDS: List[str] = [
    "apple",
    "samsung",
    "sony",
    "google",
    "lg",
    "dell",
    "hp",
    "lenovo",
    "asus",
    "bose",
    "jabra",
    "anker",
    "dyson",
    "shark",
    "philips",
    "panasonic",
    "microsoft",
    "amazon",
    "jbl",
    "sennheiser",
    "audio-technica",
    "beyerdynamic",
    "shure",
    "roborock",
    "irobot",
    "eufy",
    "nespresso",
    "breville",
    "de'longhi",
    "delonghi",
    "kitchenaid",
    "ninja",
    "instant pot",
    "cuisinart",
    "logitech",
    "razer",
    "corsair",
    "msi",
    "acer",
    "toshiba",
    "hitachi",
    "whirlpool",
    "bosch",
    "siemens",
    "john deere",
    "husqvarna",
    "honda",
    "toro",
    "dewalt",
    "makita",
    "milwaukee",
    "bissell",
    "hoover",
    "roomba",
    "ecovacs",
    "toyota",
    "weber",
    "traeger",
    "peloton",
    "garmin",
    "fitbit",
    "gopro",
    "nikon",
    "canon",
]

# Known categories (longer phrases first for greedy matching)
KNOWN_CATEGORIES: List[str] = [
    "robot vacuum",
    "air purifier",
    "espresso machine",
    "coffee maker",
    "stand mixer",
    "noise canceling headphones",
    "noise-canceling headphones",
    "wireless headphones",
    "true wireless earbuds",
    "smart speaker",
    "bluetooth speaker",
    "gaming laptop",
    "gaming headset",
    "mechanical keyboard",
    "ultrawide monitor",
    "standing desk",
    "laptop stand",
    "webcam",
    "headphones",
    "earbuds",
    "speaker",
    "laptop",
    "phone",
    "tablet",
    "monitor",
    "vacuum",
    "printer",
    "router",
    "keyboard",
    "mouse",
    "microphone",
    "camera",
    "smartwatch",
    "fitness tracker",
    "tv",
    "projector",
    "soundbar",
    "lawn mower",
    "lawnmower",
    "pressure washer",
    "grill",
    "air fryer",
    "blender",
    "toaster",
    "dishwasher",
    "dryer",
    "washer",
    "refrigerator",
    "mattress",
    "stroller",
    "car seat",
    "treadmill",
    "exercise bike",
    "massage gun",
]

# ---------------------------------------------------------------------------
# Budget regex patterns (pre-compiled)
# ---------------------------------------------------------------------------

_BUDGET_UNDER: re.Pattern = re.compile(
    r"under\s*\$?\s*(\d[\d,]*)", re.IGNORECASE
)
_BUDGET_BELOW: re.Pattern = re.compile(
    r"below\s*\$?\s*(\d[\d,]*)", re.IGNORECASE
)
_BUDGET_MAX: re.Pattern = re.compile(
    r"(?:less\s+than|max|maximum|up\s+to)\s*\$?\s*(\d[\d,]*)", re.IGNORECASE
)
# Range: requires at least the first $ sign
_BUDGET_RANGE: re.Pattern = re.compile(
    r"(?:between\s+)?\$\s*(\d[\d,]*)\s*(?:-|to|and)\s*\$?\s*(\d[\d,]*)",
    re.IGNORECASE,
)
_BUDGET_AROUND: re.Pattern = re.compile(
    r"(?:around|about|roughly)\s*\$?\s*(\d[\d,]*)", re.IGNORECASE
)

# Travel destination pattern
_TRAVEL_DEST: re.Pattern = re.compile(
    r"(?:trip\s+to|travel\s+to|visit(?:ing)?|vacation\s+in|holiday\s+in"
    r"|hotels\s+in|flights\s+to|things\s+to\s+do\s+in|itinerary\s+(?:for\s+)?(?:a\s+trip\s+to\s+)?|"
    r"plan\s+a\s+trip\s+(?:to\s+)?|where\s+to\s+stay\s+in)\s+([A-Z][a-zA-Z\s\-,]+?)(?:\s*$|\s*[,.]|\s+for\s|\s+in\s|\s+with\s|\s+and\s)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class FastRouterResult:
    """Result returned by the fast router."""

    intent: str
    slots: Dict[str, Any]
    tool_chain: List[str]
    plan: Dict[str, Any]
    confidence: float
    tier: int  # 1 = keyword, 2 = Haiku LLM
    needs_clarification: bool = False
    speculative_results: Optional[Dict[str, Any]] = None  # Pre-fetched search results


# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------


def _parse_amount(raw: str) -> int:
    """Convert a digit string (possibly with commas) to int."""
    return int(raw.replace(",", ""))


def extract_slots(query: str) -> Dict[str, Any]:
    """
    Extract structured slots from a user query using regex patterns.

    Returns a dict with any subset of:
        max_budget (int), min_budget (int), budget_approx (int),
        brand (str), category (str), destination (str)
    """
    slots: Dict[str, Any] = {}
    q = query  # keep original case for destination; use lower for brands/cats

    # --- Budget ---

    # Range check first (most specific)
    m = _BUDGET_RANGE.search(q)
    if m:
        lo, hi = _parse_amount(m.group(1)), _parse_amount(m.group(2))
        slots["min_budget"] = min(lo, hi)
        slots["max_budget"] = max(lo, hi)
    else:
        # Under / below / max
        m_under = _BUDGET_UNDER.search(q)
        m_below = _BUDGET_BELOW.search(q)
        m_max = _BUDGET_MAX.search(q)
        for pat_match in filter(None, [m_under, m_below, m_max]):
            slots["max_budget"] = _parse_amount(pat_match.group(1))
            break  # take the first match only

        # Around / about / roughly (only if no max already found)
        if "max_budget" not in slots:
            m_around = _BUDGET_AROUND.search(q)
            if m_around:
                slots["budget_approx"] = _parse_amount(m_around.group(1))

    # --- Brand ---
    q_lower = q.lower()
    for brand in KNOWN_BRANDS:
        # Match as a whole word
        pattern = r"\b" + re.escape(brand) + r"\b"
        if re.search(pattern, q_lower):
            slots["brand"] = brand
            break

    # --- Category (longest match first — list is already sorted that way) ---
    for cat in KNOWN_CATEGORIES:
        pattern = r"\b" + re.escape(cat) + r"\b"
        if re.search(pattern, q_lower):
            slots["category"] = cat
            break

    # --- Travel destination ---
    m_dest = _TRAVEL_DEST.search(q)
    if m_dest:
        destination = m_dest.group(1).strip().rstrip(",.")
        if destination:
            slots["destination"] = destination

    return slots


# ---------------------------------------------------------------------------
# Tier 1 classification
# ---------------------------------------------------------------------------


def _has_keyword(text: str, keywords: List[str]) -> bool:
    """Return True if any keyword is present in text (case-insensitive)."""
    return any(kw in text for kw in keywords)


def _classify_tier1(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    last_search_context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Deterministic keyword-based intent classification.

    Returns the intent string or None if confidence is too low.

    Priority order (descending):
        1. intro (short greetings)
        2. comparison (explicit vs / compare)
        3. travel
        4. general informational (what is X, how does Y)
        5. service (overrides product when both match)
        6. service alone
        7. product
        8. follow-up with existing product context
    """
    q = query.strip().lower()

    # 1. Intro — only pure greetings (short messages).
    #    If the user says "hi I need a lawn mower", that's a product query,
    #    not an intro. Anything over 4 words is NOT just a greeting.
    is_greeting = any(pat.search(q) for pat in _INTRO_PATTERNS)
    if is_greeting and len(q.split()) <= 4:
        return "intro"
    # If greeting + substance, fall through to classify the real intent

    # 2. Comparison — explicit compare signals
    if _has_keyword(q, _COMPARISON_KEYWORDS):
        return "comparison"

    # 3. Travel
    if _has_keyword(q, _TRAVEL_KEYWORDS):
        return "travel"

    # 4. General informational — check BEFORE product so "what is the best X"
    #    still falls through (product keywords take priority when both match)
    has_general = _has_keyword(q, _GENERAL_KEYWORDS)
    has_product = _has_keyword(q, _PRODUCT_KEYWORDS)
    has_service = _has_keyword(q, _SERVICE_KEYWORDS)

    # If general but no product signal → informational
    if has_general and not has_product:
        return "general"

    # 5. Service + product co-occurrence → service wins
    if has_service and has_product:
        return "service"

    # 6. Service alone
    if has_service:
        return "service"

    # 7. Product
    if has_product:
        return "product"

    # 8. Follow-up: user hasn't triggered any keywords but there's product context
    if last_search_context and last_search_context.get("intent") in (
        "product",
        "comparison",
        "service",
    ):
        return last_search_context["intent"]

    # No match — caller should fall back to Tier 2 or "unclear"
    return None


# ---------------------------------------------------------------------------
# Public synchronous entry point
# ---------------------------------------------------------------------------


def fast_router_sync(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    last_search_context: Optional[Dict[str, Any]] = None,
) -> FastRouterResult:
    """
    Synchronous entry point for Tier 1 fast routing.

    Calls _classify_tier1; if no intent matches, returns "unclear" with
    low confidence (0.3) so the caller can escalate to Tier 2 (Haiku).

    Args:
        query: The raw user message.
        conversation_history: Prior turns, each {"role": ..., "content": ...}.
        last_search_context: The last search context dict from GraphState.

    Returns:
        FastRouterResult with intent, slots, tool_chain, plan, confidence, tier.
    """
    intent = _classify_tier1(query, conversation_history, last_search_context)

    if intent is None:
        # Before giving up, check if the query mentions a known brand or category
        # — if so, it's almost certainly a product query even if keywords missed
        fallback_slots = extract_slots(query)
        if "brand" in fallback_slots or "category" in fallback_slots:
            intent = "product"
        else:
            return FastRouterResult(
                intent="unclear",
                slots=fallback_slots,
                tool_chain=TOOL_CHAINS["unclear"],
                plan={"steps": PLAN_TEMPLATES["unclear"]},
                confidence=0.3,
                tier=1,
                needs_clarification=True,
            )

    slots = extract_slots(query)

    # Confidence heuristics
    q_lower = query.strip().lower()
    if intent == "intro":
        confidence = 0.99
    elif intent == "comparison":
        confidence = 0.95
    elif intent == "travel":
        # Higher confidence when destination slot extracted
        confidence = 0.92 if "destination" in slots else 0.82
    elif intent == "general":
        confidence = 0.85
    elif intent in ("product", "service"):
        # Higher confidence when brand or category slot present
        has_slot = "brand" in slots or "category" in slots
        confidence = 0.92 if has_slot else 0.80
    else:
        confidence = 0.75

    return FastRouterResult(
        intent=intent,
        slots=slots,
        tool_chain=TOOL_CHAINS[intent],
        plan={"steps": PLAN_TEMPLATES[intent]},
        confidence=confidence,
        tier=1,
        needs_clarification=False,
    )


# ---------------------------------------------------------------------------
# Tier 2 — Haiku LLM fallback
# ---------------------------------------------------------------------------

_HAIKU_SYSTEM_PROMPT = """You are an intent classifier for a product/travel review assistant.

Classify the user query into exactly one of these intents:
- product: user wants product recommendations, reviews, or to buy something
- comparison: user wants to compare products or options
- service: user asks about services (VPN, streaming, insurance, etc.)
- travel: user asks about travel, hotels, flights, destinations, itineraries
- general: user wants information/explanation (what is X, how does Y work)
- intro: user is greeting or asking what the assistant can do
- unclear: query is too vague to classify

Also extract these slots (only if clearly present, otherwise omit):
- category: product/service category (e.g. "headphones", "laptop")
- brand: brand name (e.g. "sony", "apple")
- max_budget: maximum budget as integer (e.g. 200)
- min_budget: minimum budget as integer (e.g. 100)
- destination: travel destination (e.g. "Tokyo")
- duration_days: trip duration in days as integer (e.g. 7)

Respond with ONLY valid JSON in this exact format:
{"intent": "<intent>", "slots": {<slot_key>: <slot_value>, ...}}

If no slots are present, use: {"intent": "<intent>", "slots": {}}"""


async def _call_haiku(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Call Claude Haiku to classify the intent of an ambiguous query.

    Returns a dict with 'intent' and 'slots' keys, or None on failure.
    """
    from app.core.config import settings

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        logger.warning("fast_router: ANTHROPIC_API_KEY not set — skipping Tier 2")
        return None

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=api_key)

        # Build messages: last 4 conversation turns + current query
        messages: List[Dict[str, str]] = []
        history = conversation_history or []
        for turn in history[-4:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": query})

        response = await client.messages.create(
            model=settings.FAST_ROUTER_MODEL,
            max_tokens=150,
            system=_HAIKU_SYSTEM_PROMPT,
            messages=messages,
        )

        raw_text = response.content[0].text.strip()
        result = json.loads(raw_text)

        # Validate structure
        if "intent" not in result:
            logger.warning("fast_router: Haiku response missing 'intent' key: %s", raw_text)
            return None

        if result["intent"] not in TOOL_CHAINS:
            logger.warning("fast_router: Haiku returned unknown intent '%s'", result["intent"])
            return None

        return result

    except Exception as exc:
        logger.error("fast_router: Haiku Tier 2 call failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public async entry point
# ---------------------------------------------------------------------------


async def fast_router(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    last_search_context: Optional[Dict[str, Any]] = None,
) -> FastRouterResult:
    """
    Async entry point for the two-tier fast router.

    Tier 1: deterministic keyword classification (zero latency).
    Tier 2: Haiku LLM fallback when Tier 1 cannot determine intent.

    Args:
        query: The raw user message.
        conversation_history: Prior turns, each {"role": ..., "content": ...}.
        last_search_context: The last search context dict from GraphState.

    Returns:
        FastRouterResult with intent, slots, tool_chain, plan, confidence, tier.
    """
    # --- Tier 1: keyword classification ---
    tier1_intent = _classify_tier1(query, conversation_history, last_search_context)
    tier1_slots = extract_slots(query)

    if tier1_intent is not None:
        logger.debug("fast_router: Tier 1 hit — intent=%s", tier1_intent)

        q_lower = query.strip().lower()
        if tier1_intent == "intro":
            confidence = 0.99
        elif tier1_intent == "comparison":
            confidence = 0.95
        elif tier1_intent == "travel":
            confidence = 0.92 if "destination" in tier1_slots else 0.82
        elif tier1_intent == "general":
            confidence = 0.85
        elif tier1_intent in ("product", "service"):
            has_slot = "brand" in tier1_slots or "category" in tier1_slots
            confidence = 0.92 if has_slot else 0.80
        else:
            confidence = 0.75

        return FastRouterResult(
            intent=tier1_intent,
            slots=tier1_slots,
            tool_chain=TOOL_CHAINS[tier1_intent],
            plan={"steps": PLAN_TEMPLATES[tier1_intent]},
            confidence=confidence,
            tier=1,
            needs_clarification=False,
        )

    # --- Tier 2: Haiku LLM fallback ---
    logger.debug("fast_router: Tier 1 miss — falling back to Tier 2 (Haiku)")

    try:
        haiku_result = await _call_haiku(query, conversation_history)
    except Exception as exc:
        logger.error("fast_router: Unexpected error calling Haiku: %s", exc)
        haiku_result = None

    if haiku_result is not None:
        intent = haiku_result.get("intent", "general")
        haiku_slots: Dict[str, Any] = haiku_result.get("slots", {}) or {}

        # Merge slots: regex (Tier 1) wins on conflict for precision
        merged_slots = {**haiku_slots, **tier1_slots}

        logger.debug("fast_router: Tier 2 hit — intent=%s slots=%s", intent, merged_slots)

        return FastRouterResult(
            intent=intent,
            slots=merged_slots,
            tool_chain=TOOL_CHAINS.get(intent, TOOL_CHAINS["general"]),
            plan={"steps": PLAN_TEMPLATES.get(intent, PLAN_TEMPLATES["general"])},
            confidence=0.75,
            tier=2,
            needs_clarification=False,
        )

    # --- Final fallback: general intent with low confidence ---
    logger.debug("fast_router: Tier 2 failed — using general fallback")

    return FastRouterResult(
        intent="general",
        slots=tier1_slots,
        tool_chain=TOOL_CHAINS["general"],
        plan={"steps": PLAN_TEMPLATES["general"]},
        confidence=0.3,
        tier=2,
        needs_clarification=False,
    )


# ---------------------------------------------------------------------------
# Phase B: Speculative search helpers
# ---------------------------------------------------------------------------


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


async def fast_router_with_speculation(
    query: str,
    conversation_history: list,
    last_search_context: Optional[dict],
    state: dict,
) -> FastRouterResult:
    """
    Async fast router with speculative product_search.
    Fires search in parallel with classification. If intent is
    product/comparison/service, results are reused. Otherwise discarded.
    """
    import asyncio
    import contextlib

    # Fire speculative search + classification in parallel
    search_task = asyncio.create_task(run_speculative_search(query, state))

    # Run the normal async fast_router (Tier 1 + Tier 2)
    router_result = await fast_router(query, conversation_history, last_search_context)

    # Check if speculative results are useful for this intent
    if router_result.intent in ("product", "comparison", "service"):
        try:
            spec_results = await asyncio.wait_for(search_task, timeout=10.0)
            router_result.speculative_results = spec_results
            logger.info(f"Speculative search hit: {len(spec_results.get('product_names', []))} products")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Speculative search failed/timed out: {e}")
            router_result.speculative_results = None
    else:
        # Wrong intent — cancel and cleanup
        search_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await search_task
        router_result.speculative_results = None
        logger.info(f"Speculative search discarded: intent={router_result.intent}")

    return router_result
