"""
Preference Service

Extracts, merges, and persists user preferences from product conversations.
Preferences are accumulated across sessions and surfaced as LLM context hints.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.centralized_logger import get_logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


async def load_user_preferences(db: AsyncSession, user_id: int) -> dict:
    """Load preferences from the users table.

    Args:
        db: Active database session
        user_id: User ID to load preferences for

    Returns:
        Preferences dict (empty dict if none stored)
    """
    try:
        from app.models.user import User
        result = await db.execute(
            select(User.preferences).where(User.id == user_id)
        )
        row = result.scalar_one_or_none()
        return row if row else {}
    except Exception as e:
        logger.warning(f"[preference_service] Failed to load preferences for user {user_id}: {e}")
        return {}


async def update_user_preferences(
    user_id: int,
    slots: Dict[str, Any],
    search_context: Dict[str, Any],
) -> None:
    """Extract preferences from slots/context and merge into the user record.

    Runs with its own DB session so it can be fire-and-forget from product_compose.

    Args:
        user_id: User ID to update
        slots: Slot dict from the current query (brand, category, budget, etc.)
        search_context: The new_context dict built in product_compose
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.user import User

        if not AsyncSessionLocal:
            logger.warning("[preference_service] DB not initialized, skipping preference update")
            return

        extracted = _extract_preferences(slots, search_context)
        if not extracted:
            return

        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(User.preferences).where(User.id == user_id)
                )
                existing = result.scalar_one_or_none() or {}
                merged = _merge_preferences(existing, extracted)
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(preferences=merged)
                )

        logger.info(f"[preference_service] Updated preferences for user {user_id}: {list(merged.keys())}")

    except Exception as e:
        logger.warning(f"[preference_service] Failed to update preferences for user {user_id}: {e}")


def _extract_preferences(slots: Dict[str, Any], context: Dict[str, Any]) -> dict:
    """Pull preference-worthy fields from slots and search context.

    Returns a dict with the same shape as the stored preferences schema,
    but with raw single-occurrence values (counts=1, lists of length 1).
    """
    prefs: Dict[str, Any] = {}

    brand = slots.get("brand") or context.get("brand")
    if brand and isinstance(brand, str):
        prefs["brands"] = {brand: 1}

    category = slots.get("category") or context.get("category")
    if category and isinstance(category, str):
        prefs["categories"] = {category: 1}

    budget = slots.get("budget") or context.get("budget")
    if budget and isinstance(budget, str):
        prefs["budget_ranges"] = [budget]

    features = slots.get("features") or context.get("features")
    if features:
        if isinstance(features, str):
            prefs["features"] = [f.strip() for f in features.split(",")]
        elif isinstance(features, list):
            prefs["features"] = features

    use_case = slots.get("use_case") or context.get("use_case")
    if use_case and isinstance(use_case, str):
        prefs["use_cases"] = {use_case: 1}

    return prefs


def _merge_preferences(existing: dict, new: dict) -> dict:
    """Merge new preference signals into existing stored preferences.

    - brands / categories / use_cases: increment counts
    - budget_ranges: prepend (newest first), deduplicate, cap at 5
    - features: union / deduplicate
    """
    merged = {
        "brands": dict(existing.get("brands", {})),
        "categories": dict(existing.get("categories", {})),
        "budget_ranges": list(existing.get("budget_ranges", [])),
        "features": list(existing.get("features", [])),
        "use_cases": dict(existing.get("use_cases", {})),
    }

    # Count-based fields
    for key in ("brands", "categories", "use_cases"):
        for name, count in new.get(key, {}).items():
            merged[key][name] = merged[key].get(name, 0) + count

    # Budget ranges — newest first, deduplicated, max 5
    for budget in new.get("budget_ranges", []):
        if budget in merged["budget_ranges"]:
            merged["budget_ranges"].remove(budget)
        merged["budget_ranges"].insert(0, budget)
    merged["budget_ranges"] = merged["budget_ranges"][:5]

    # Features — deduplicated union
    existing_features_lower = {f.lower() for f in merged["features"]}
    for feat in new.get("features", []):
        if feat.lower() not in existing_features_lower:
            merged["features"].append(feat)
            existing_features_lower.add(feat.lower())

    merged["last_updated"] = datetime.now(timezone.utc).isoformat()
    return merged
