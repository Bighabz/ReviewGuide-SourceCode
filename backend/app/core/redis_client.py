"""
Redis Client with Retry Logic
Connection pooling and automatic retry for failed operations
"""
from app.core.centralized_logger import get_logger
from typing import Any, Optional
import asyncio
from redis import asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import settings

logger = get_logger(__name__)

# Global Redis client
redis_client: Optional[Redis] = None
connection_pool: Optional[ConnectionPool] = None


async def init_redis() -> None:
    """Initialize Redis connection with connection pooling"""
    global redis_client, connection_pool

    try:
        # Create connection pool
        connection_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_keepalive=True,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
        )

        # Create Redis client
        redis_client = Redis(connection_pool=connection_pool)

        # Test connection
        await redis_client.ping()

        logger.info("Redis connection initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connections"""
    global redis_client, connection_pool

    if redis_client:
        await redis_client.close()

    if connection_pool:
        await connection_pool.disconnect()

    logger.info("Redis connections closed")


async def get_redis() -> Redis:
    """Get Redis client instance"""
    if not redis_client:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_client


async def redis_get_with_retry(key: str, max_retries: int = None) -> Optional[str]:
    """Get value from Redis with automatic retry"""
    max_retries = max_retries or settings.REDIS_RETRY_MAX_ATTEMPTS
    client = await get_redis()

    for attempt in range(max_retries):
        try:
            return await client.get(key)
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis GET failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Redis GET attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(settings.REDIS_RETRY_BACKOFF_BASE * (2 ** attempt))  # Exponential backoff


async def redis_set_with_retry(
    key: str,
    value: str,
    ex: Optional[int] = None,
    max_retries: int = None
) -> bool:
    """Set value in Redis with automatic retry"""
    max_retries = max_retries or settings.REDIS_RETRY_MAX_ATTEMPTS
    client = await get_redis()

    for attempt in range(max_retries):
        try:
            return await client.set(key, value, ex=ex)
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis SET failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Redis SET attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(settings.REDIS_RETRY_BACKOFF_BASE * (2 ** attempt))


async def redis_delete_with_retry(key: str, max_retries: int = None) -> int:
    """Delete key from Redis with automatic retry"""
    max_retries = max_retries or settings.REDIS_RETRY_MAX_ATTEMPTS
    client = await get_redis()

    for attempt in range(max_retries):
        try:
            return await client.delete(key)
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Redis DELETE failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Redis DELETE attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(settings.REDIS_RETRY_BACKOFF_BASE * (2 ** attempt))
