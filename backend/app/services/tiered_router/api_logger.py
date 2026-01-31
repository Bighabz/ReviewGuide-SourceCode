# backend/app/services/tiered_router/api_logger.py
"""API Usage Logger - Track API costs and consent events."""

import logging
from typing import Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.api_usage_log import APIUsageLog

logger = logging.getLogger(__name__)


async def log_api_usage(
    user_id: Optional[str],
    session_id: Optional[str],
    api_name: str,
    tier: int,
    cost_cents: int,
    latency_ms: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Log an API call to the database.

    Args:
        user_id: User ID (optional for anonymous users)
        session_id: Chat session ID
        api_name: Name of the API called
        tier: Tier level (1-4)
        cost_cents: Cost in cents
        latency_ms: Response time in milliseconds
        success: Whether the call succeeded
        error: Error message if failed
    """
    if not settings.LOG_API_COSTS:
        return

    try:
        async with AsyncSessionLocal() as session:
            log_entry = APIUsageLog(
                user_id=user_id,
                session_id=session_id,
                api_name=api_name,
                tier=tier,
                cost_cents=cost_cents,
                latency_ms=latency_ms,
                success=success,
                error=error,
            )
            session.add(log_entry)
            await session.commit()
    except Exception as e:
        # Don't fail the request if logging fails
        logger.warning(f"Failed to log API usage: {e}")


async def log_consent_event(
    user_id: str,
    session_id: str,
    consent_type: str,
    tier_requested: int,
) -> None:
    """Log a consent event for compliance tracking.

    This creates a special API log entry with api_name="consent_{type}"
    to create an audit trail of user consent actions.
    """
    await log_api_usage(
        user_id=user_id,
        session_id=session_id,
        api_name=f"consent_{consent_type}",
        tier=tier_requested,
        cost_cents=0,
        success=True,
    )
    logger.info(f"Consent logged: user={user_id}, type={consent_type}, tier={tier_requested}")
