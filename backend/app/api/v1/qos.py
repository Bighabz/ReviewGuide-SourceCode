"""
RFC §4.2 — QoS Dashboard API

Admin endpoint serving p50/p95/p99 latency and reliability metrics
over a rolling 24-hour window (configurable via `hours` query parameter).

Latency targets:  p50 < 8 s, p95 < 20 s, p99 < 45 s
Reliability targets: stream completion > 98 %, degraded < 5 %
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.centralized_logger import get_logger
from app.core.database import get_db
from app.core.dependencies import require_admin


logger = get_logger(__name__)
router = APIRouter()


@router.get("/admin/qos/summary")
async def get_qos_summary(
    hours: int = 24,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Return QoS metrics for the past `hours` hours (default: 24).

    Requires admin authentication.

    Metrics returned:
    - total_requests: count of completed requests in the window
    - latency.p50_ms / p95_ms / p99_ms: percentile latencies in milliseconds
    - latency.targets: RFC §4.2 SLO targets
    - reliability.completion_rate: fraction of requests with a recorded duration
    - reliability.degraded_rate: fraction where completeness != 'full'
    - reliability.targets: RFC §4.2 SLO targets
    """
    # Clamp hours to a safe range to prevent runaway queries
    hours = max(1, min(hours, 8760))  # 1 hour to 1 year

    result = await db.execute(
        text("""
            SELECT
                COUNT(*) AS total_requests,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_duration_ms) AS p50_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms) AS p95_ms,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_duration_ms) AS p99_ms,
                AVG(CASE WHEN total_duration_ms IS NOT NULL THEN 1.0 ELSE 0.0 END) AS completion_rate,
                AVG(CASE WHEN completeness != 'full' THEN 1.0 ELSE 0.0 END) AS degraded_rate
            FROM request_metrics
            WHERE created_at > NOW() - CAST(:hours_interval AS INTERVAL)
        """),
        {"hours_interval": f"{hours} hours"},
    )

    row = result.fetchone()

    logger.info(
        "[qos] summary requested",
        extra={"admin": admin.get("username"), "window_hours": hours},
    )

    return {
        "window_hours": hours,
        "total_requests": int(row.total_requests or 0),
        "latency": {
            "p50_ms": int(row.p50_ms or 0),
            "p95_ms": int(row.p95_ms or 0),
            "p99_ms": int(row.p99_ms or 0),
            "targets": {
                "p50_ms": 8000,
                "p95_ms": 20000,
                "p99_ms": 45000,
            },
        },
        "reliability": {
            "completion_rate": round(float(row.completion_rate or 0), 4),
            "degraded_rate": round(float(row.degraded_rate or 0), 4),
            "targets": {
                "completion_rate": 0.98,
                "degraded_rate": 0.05,
            },
        },
    }
