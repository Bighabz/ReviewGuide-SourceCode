"""
Telemetry Endpoints — RFC §4.1 Unified Trace Model

POST /v1/telemetry/render  — accept frontend render milestones for p95 TTFC calculation
GET  /v1/admin/trace/:id   — admin stub to look up a correlated trace by interaction ID
"""
import re

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, field_validator
from typing import Optional

from app.core.centralized_logger import get_logger
from app.core.dependencies import require_admin, check_rate_limit

logger = get_logger(__name__)
router = APIRouter()

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RenderMilestones(BaseModel):
    """Frontend render milestone timestamps sent after each chat stream completes."""
    interaction_id: str
    request_sent_ts: int
    first_status_ts: Optional[int] = None
    first_content_ts: Optional[int] = None
    first_artifact_ts: Optional[int] = None
    done_ts: Optional[int] = None

    @field_validator("interaction_id")
    @classmethod
    def must_be_uuid(cls, v: str) -> str:
        if not _UUID_RE.match(v):
            raise ValueError("interaction_id must be a UUID")
        return v


# ---------------------------------------------------------------------------
# POST /v1/telemetry/render
# ---------------------------------------------------------------------------

@router.post("/telemetry/render")
async def record_render_milestones(
    milestones: RenderMilestones,
    _rate_limit: None = Depends(check_rate_limit),
):
    """
    Record frontend render milestones for p95 time-to-first-content calculation.

    Called fire-and-forget from the frontend immediately after the SSE 'done'
    event arrives.  All timestamps are milliseconds since Unix epoch (Date.now()).
    """
    ttfc_ms: Optional[int] = None
    if milestones.first_content_ts is not None:
        ttfc_ms = milestones.first_content_ts - milestones.request_sent_ts

    ttfa_ms: Optional[int] = None
    if milestones.first_artifact_ts is not None:
        ttfa_ms = milestones.first_artifact_ts - milestones.request_sent_ts

    total_ms: Optional[int] = None
    if milestones.done_ts is not None:
        total_ms = milestones.done_ts - milestones.request_sent_ts

    logger.info(
        "[telemetry] render milestones",
        extra={
            "interaction_id": milestones.interaction_id,
            "request_sent_ts": milestones.request_sent_ts,
            "first_status_ts": milestones.first_status_ts,
            "first_content_ts": milestones.first_content_ts,
            "first_artifact_ts": milestones.first_artifact_ts,
            "done_ts": milestones.done_ts,
            "ttfc_ms": ttfc_ms,
            "ttfa_ms": ttfa_ms,
            "total_ms": total_ms,
        },
    )

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /v1/admin/trace/:interaction_id
# ---------------------------------------------------------------------------

@router.get("/admin/trace/{interaction_id}")
async def get_trace(
    interaction_id: str = Path(
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    ),
    admin: dict = Depends(require_admin),
):
    """
    Return correlated trace info for an interaction ID (admin only).

    This is a stub — full trace DB storage is deferred to RFC §4.2.
    For now, use the Langfuse UI and search for the tag
    'request_id:<interaction_id>' to locate the corresponding trace.
    """
    return {
        "interaction_id": interaction_id,
        "message": (
            "Trace lookup not yet implemented — check Langfuse with tag: "
            "request_id:" + interaction_id
        ),
    }
