from datetime import datetime, timezone


def get_current_date_str() -> str:
    """Return today's date formatted for LLM system prompts, e.g. 'February 23, 2026'."""
    return datetime.now(timezone.utc).strftime("%B %d, %Y")
