"""
RFC §4.2 — QoS Dashboard API

Admin endpoint serving p50/p95/p99 latency and reliability metrics
over a rolling 24-hour window (configurable via `hours` query parameter).

Latency targets:  p50 < 8 s, p95 < 20 s, p99 < 45 s
Reliability targets: stream completion > 98 %, degraded < 5 %

Alert thresholds (RFC §4.2: p95 > 30s for 5 min):
    Alerting requires external infrastructure (Railway log drain → Datadog/Grafana/Axiom).
    The SLO targets embedded in this response can be used to configure alert rules
    against the structured [qos] log lines emitted to stdout.
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
    - provider_errors.rate: fraction of requests that logged any provider error
    - provider_errors.target: RFC §4.2 SLO target (< 1 %)

    Per-provider timeout rates require §1.1 stage telemetry data
    (StageTelemetry.tool_name + timeout_hit). Until §1.1 is implemented,
    `provider_errors` reflects errors logged by tools in provider_errors
    GraphState key.
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
            WHERE created_at > NOW() - (:hours * INTERVAL '1 hour')
        """),
        {"hours": hours},
    )

    row = result.fetchone()

    # Second query: count rows that have any provider errors logged.
    # Uses jsonb_array_length to detect non-empty provider_errors arrays.
    # Per-provider breakdown requires §1.1 stage telemetry (tool_name +
    # timeout_hit fields); this query provides an aggregate rate in the interim.
    pe_result = await db.execute(
        text("""
            SELECT
                COUNT(*) AS rows_with_provider_errors
            FROM request_metrics
            WHERE created_at > NOW() - (:hours * INTERVAL '1 hour')
              AND provider_errors IS NOT NULL
              AND jsonb_array_length(provider_errors) > 0
        """),
        {"hours": hours},
    )

    pe_row = pe_result.fetchone()

    total = int(row.total_requests or 0)
    rows_with_errors = int(pe_row.rows_with_provider_errors or 0) if pe_row else 0
    provider_error_rate = rows_with_errors / total if total > 0 else 0.0

    logger.info(
        "[qos] summary requested",
        extra={"admin": admin.get("username"), "window_hours": hours},
    )

    return {
        "window_hours": hours,
        "total_requests": total,
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
            "note": "degraded_rate requires RFC §1.8 completeness tracking (currently always 0.0 — completeness field deferred to §1.8).",
            "targets": {
                "completion_rate": 0.98,
                "degraded_rate": 0.05,
            },
        },
        "provider_errors": {
            "rate": round(float(provider_error_rate), 4),
            "note": (
                "Per-provider breakdown requires §1.1 stage telemetry "
                "(tool_name + timeout_hit fields). Currently reflects "
                "requests with any provider_errors logged."
            ),
            "target": 0.01,  # < 1% per RFC §4.2
        },
    }
