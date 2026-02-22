"""
Web Context Builder

Sanitizes, filters, deduplicates, and token-caps search results before
injecting them into LLM prompts. Prevents prompt injection and token bloat.
"""
import re
import hashlib
from dataclasses import dataclass

from app.core.centralized_logger import get_logger

logger = get_logger(__name__)

# Prompt injection heuristics — lines containing these patterns are stripped
_INJECTION_PATTERNS = re.compile(
    r"ignore (previous|all|prior)|system\s*:|<\|.*?\|>|\[INST\]|<<SYS>>|"
    r"you are now|disregard (previous|prior|all)|new instructions|"
    r"override (previous|prior)|forget (previous|prior|all)",
    re.IGNORECASE,
)

# Max characters per individual snippet (before token estimation)
_MAX_SNIPPET_CHARS = 300
# Default token budget for total web context injected into prompt
_DEFAULT_MAX_TOKENS = 800
# Chars-per-token approximation (conservative)
_CHARS_PER_TOKEN = 4


@dataclass
class WebContext:
    text: str          # Formatted, sanitized string ready for prompt injection
    source_count: int  # Number of sources included
    omitted_count: int # Sources dropped (low relevance or over token budget)
    token_estimate: int


def _sanitize_snippet(text: str) -> str:
    """Strip injection patterns, HTML entities, and excess whitespace from a snippet."""
    # Remove lines that match injection heuristics
    lines = text.splitlines()
    safe_lines = [line for line in lines if not _INJECTION_PATTERNS.search(line)]
    text = " ".join(safe_lines)
    # Strip basic HTML entities
    text = re.sub(r"&[a-z]+;|&#\d+;", " ", text)
    # Strip markdown formatting
    text = re.sub(r"[*_`#\[\]()>]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _jaccard_similarity(a: str, b: str) -> float:
    """Simple token Jaccard similarity between two strings."""
    tokens_a = set(re.findall(r"\w+", a.lower()))
    tokens_b = set(re.findall(r"\w+", b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def build_web_context(
    results: list,  # list[SearchResult]
    query: str,
    slots: dict | None = None,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    min_relevance_score: float = 0.1,
) -> WebContext:
    """
    Build a sanitized, token-budgeted web context string for LLM prompt injection.

    Args:
        results: List of SearchResult objects from search provider
        query: The search query used (for relevance scoring)
        slots: Optional structured slots (for relevance scoring)
        max_tokens: Maximum tokens to inject (default 800)
        min_relevance_score: Minimum Jaccard similarity to query (default 0.1)

    Returns:
        WebContext with formatted text and metadata
    """
    if not results:
        return WebContext(text="", source_count=0, omitted_count=0, token_estimate=0)

    # Build relevance query string (query + slot values)
    relevance_ref = query
    if slots:
        slot_vals = " ".join(str(v) for v in slots.values() if v)
        relevance_ref = f"{query} {slot_vals}"

    kept = []
    omitted = 0

    for r in results:
        title = _sanitize_snippet(r.title or "")
        snippet = _sanitize_snippet(r.snippet or "")

        # Skip empty results after sanitization
        if not snippet and not title:
            omitted += 1
            continue

        # Truncate snippet
        combined = f"{title}: {snippet}" if title else snippet
        if len(combined) > _MAX_SNIPPET_CHARS:
            combined = combined[:_MAX_SNIPPET_CHARS].rsplit(" ", 1)[0]

        # Relevance filter
        score = _jaccard_similarity(combined, relevance_ref)
        if score < min_relevance_score:
            logger.debug(f"[web_context] Dropped low-relevance snippet (score={score:.2f}): {combined[:60]}")
            omitted += 1
            continue

        kept.append((score, combined))

    # Sort by relevance descending so we keep the best within the token budget
    kept.sort(key=lambda x: x[0], reverse=True)

    # Apply token budget — trim from lowest relevance first
    lines = []
    total_chars = 0
    budget_chars = max_tokens * _CHARS_PER_TOKEN

    for score, line in kept:
        if total_chars + len(line) + 4 > budget_chars:  # +4 for "- \n"
            omitted += 1
            continue
        lines.append(f"- {line}")
        total_chars += len(line) + 4

    text = "\n".join(lines)
    token_estimate = total_chars // _CHARS_PER_TOKEN

    if omitted:
        logger.info(f"[web_context] Kept {len(lines)}/{len(results)} results, omitted {omitted} (budget/relevance)")

    return WebContext(
        text=text,
        source_count=len(lines),
        omitted_count=omitted,
        token_estimate=token_estimate,
    )
