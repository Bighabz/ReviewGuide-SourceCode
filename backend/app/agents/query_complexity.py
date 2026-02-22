"""
Query Complexity Classifier

Deterministic heuristic classifier for product queries.
Classifies queries into one of four complexity classes to select
the appropriate execution plan template, bypassing the LLM planner.

Must complete in < 5 ms (no LLM call).
"""

from typing import Literal
import re

# ── Keyword lists ─────────────────────────────────────────────────────────────

COMPARISON_KEYWORDS = [
    "vs", "versus", "compare", "comparison", "difference", "better", "or"
]

RECOMMENDATION_KEYWORDS = [
    "best", "recommend", "should i buy", "worth it", "top",
    "which one", "what should"
]

REVIEW_KEYWORDS = [
    "review", "reviews", "complaints", "problems", "issues",
    "experience", "sentiment", "owner", "owners", "real world"
]

# Brand names used to detect product mentions in free text
KNOWN_BRANDS = [
    "apple", "samsung", "sony", "google", "lg", "dell", "hp",
    "lenovo", "asus", "bose", "jabra", "anker", "canon", "nikon"
]

# ── Helpers ───────────────────────────────────────────────────────────────────


def _contains_any(text_lower: str, keywords: list[str]) -> bool:
    """Return True if any keyword appears as a word/phrase in text_lower."""
    for kw in keywords:
        # Use word-boundary match for single tokens; phrase match otherwise
        if " " in kw:
            if kw in text_lower:
                return True
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                return True
    return False


def _count_brand_mentions(text_lower: str) -> int:
    """Count how many distinct known brand names appear in the text."""
    count = 0
    for brand in KNOWN_BRANDS:
        if re.search(r"\b" + re.escape(brand) + r"\b", text_lower):
            count += 1
    return count


# ── Public API ────────────────────────────────────────────────────────────────


def classify_query_complexity(
    user_message: str,
    slots: dict,
    intent: str,
) -> tuple[Literal["factoid", "comparison", "recommendation", "deep_research"], float]:
    """
    Deterministic heuristic classifier. Returns (complexity_class, confidence).
    Must complete in < 5 ms (no LLM call).

    Signals:
      - factoid:        len(tokens) < 10, no comparison/review/recommendation keywords,
                        entity_count == 1
      - comparison:     product_names count >= 2 OR comparison_keywords present
      - recommendation: recommendation_keywords present AND product_names count == 0
      - deep_research:  review_keywords present OR len(tokens) > 20
    """
    text_lower = user_message.lower()
    tokens = user_message.split()
    token_count = len(tokens)

    # Slot-based product count
    slot_products: list = slots.get("product_names", []) if slots else []
    slot_product_count = len(slot_products)

    # Text-based brand/product count (used when slots are sparse)
    brand_mentions = _count_brand_mentions(text_lower)

    # Total named-product signal: use slot count if populated, else brand mentions
    named_product_count = slot_product_count if slot_product_count > 0 else brand_mentions

    has_comparison  = _contains_any(text_lower, COMPARISON_KEYWORDS)
    has_review      = _contains_any(text_lower, REVIEW_KEYWORDS)
    has_recommend   = _contains_any(text_lower, RECOMMENDATION_KEYWORDS)

    # ── Rule 1: Comparison ────────────────────────────────────────────────────
    # Comparison keywords found AND (>=2 named products OR keyword alone is enough)
    if has_comparison and named_product_count >= 2:
        return ("comparison", 0.85)

    # Explicit compare/versus even with just one product in slots
    if _contains_any(text_lower, ["vs", "versus", "compare", "comparison", "difference"]):
        return ("comparison", 0.85)

    # ── Rule 2: Deep research — review keywords ───────────────────────────────
    if has_review:
        return ("deep_research", 0.9)

    # ── Rule 3: Deep research — long query ───────────────────────────────────
    # >20 tokens: confident deep_research; >14 tokens: likely multi-criteria deep_research
    if token_count > 20:
        return ("deep_research", 0.75)
    if token_count > 14:
        return ("deep_research", 0.75)

    # ── Rule 4: Recommendation ────────────────────────────────────────────────
    if has_recommend and slot_product_count == 0:
        return ("recommendation", 0.8)

    # ── Rule 5: Factoid ───────────────────────────────────────────────────────
    if token_count <= 10 and not has_comparison and not has_review and not has_recommend:
        return ("factoid", 0.85)

    # ── Rule 6: Default fallback ──────────────────────────────────────────────
    # Low confidence → caller will fall through to LLM planner
    return ("deep_research", 0.6)
