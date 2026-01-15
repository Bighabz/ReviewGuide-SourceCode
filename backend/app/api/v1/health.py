"""
Health Check Endpoint
"""
import sqlalchemy
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.core.centralized_logger import get_logger

from app.core.redis_client import get_redis
from app.core.database import engine

logger = get_logger(__name__)

router = APIRouter()


class LivenessResponse(BaseModel):
    """Simple liveness check response"""
    status: str
    timestamp: datetime


@router.get("/", response_model=LivenessResponse)
async def liveness():
    """
    Simple liveness probe for ALB health checks
    Always returns 200 OK if the server is running
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow()
    }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    database: str
    redis: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns the status of the application and its dependencies
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": "unknown",
        "redis": "unknown",
        "version": "1.0.0"
    }

    # Check database
    try:
        if engine:
            async with engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["redis"] = "unhealthy"
        health_status["status"] = "degraded"

    # Return 503 if any service is down
    if health_status["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
