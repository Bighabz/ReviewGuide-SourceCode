"""
Rate Limiter using Redis
Implements sliding window rate limiting for guest and authenticated users
"""
import time
from app.core.centralized_logger import get_logger
from typing import Optional
from redis.asyncio import Redis
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.degradation_policy import DegradationPolicy

logger = get_logger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter with different limits for guest and authenticated users

    Uses sliding window algorithm for accurate rate limiting
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        identifier: str,
        is_authenticated: bool = False
    ) -> None:
        """
        Check if request should be rate limited

        Args:
            identifier: Unique identifier (session_id for guests, user_id for auth)
            is_authenticated: Whether user is authenticated

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if not settings.RATE_LIMIT_ENABLED:
            return  # Rate limiting disabled

        # Determine limits based on authentication status
        if is_authenticated:
            max_requests = settings.RATE_LIMIT_AUTH_REQUESTS
            window_seconds = settings.RATE_LIMIT_AUTH_WINDOW
            user_type = "authenticated"
        else:
            max_requests = settings.RATE_LIMIT_GUEST_REQUESTS
            window_seconds = settings.RATE_LIMIT_GUEST_WINDOW
            user_type = "guest"

        # Redis key for this user
        redis_key = f"rate_limit:{user_type}:{identifier}"

        try:
            # Get current timestamp
            now = int(time.time())
            window_start = now - window_seconds

            # Use Redis sorted set for sliding window
            # Remove old entries outside the window
            await self.redis.zremrangebyscore(redis_key, 0, window_start)

            # Count requests in current window
            current_count = await self.redis.zcard(redis_key)

            if current_count >= max_requests:
                # Rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded for {user_type} user: {identifier} "
                    f"({current_count}/{max_requests} in {window_seconds}s)"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "user_type": user_type,
                        "limit": max_requests,
                        "window_seconds": window_seconds,
                        "retry_after": window_seconds,
                        "message": (
                            f"Too many requests. "
                            f"{'Guests' if not is_authenticated else 'Authenticated users'} "
                            f"are limited to {max_requests} requests per "
                            f"{window_seconds // 60} minutes. "
                            f"{'Please login for higher limits.' if not is_authenticated else 'Please try again later.'}"
                        )
                    },
                    headers={"Retry-After": str(window_seconds)}
                )

            # Add current request to sorted set
            await self.redis.zadd(redis_key, {str(now): now})

            # Set expiry on the key (cleanup)
            await self.redis.expire(redis_key, window_seconds)

            logger.debug(
                f"Rate limit check passed for {user_type} user: {identifier} "
                f"({current_count + 1}/{max_requests})"
            )

        except HTTPException:
            raise  # Re-raise rate limit exception
        except Exception as e:
            if DegradationPolicy.is_fail_closed("redis_rate_limit"):
                logger.warning(
                    f"[DegradationPolicy] redis_rate_limit failure — policy=fail_closed, blocking request: {e}"
                )
                raise HTTPException(
                    status_code=503,
                    detail="Rate limiting service temporarily unavailable. Please try again."
                )
            # Default: fail_open — allow request through, log as WARNING
            logger.warning(f"[DegradationPolicy] redis_rate_limit failure — failing open: {e}")

    async def get_remaining_requests(
        self,
        identifier: str,
        is_authenticated: bool = False
    ) -> dict:
        """
        Get remaining requests for a user

        Returns:
            Dict with limit info
        """
        if not settings.RATE_LIMIT_ENABLED:
            return {
                "enabled": False,
                "remaining": "unlimited"
            }

        # Determine limits
        if is_authenticated:
            max_requests = settings.RATE_LIMIT_AUTH_REQUESTS
            window_seconds = settings.RATE_LIMIT_AUTH_WINDOW
            user_type = "authenticated"
        else:
            max_requests = settings.RATE_LIMIT_GUEST_REQUESTS
            window_seconds = settings.RATE_LIMIT_GUEST_WINDOW
            user_type = "guest"

        redis_key = f"rate_limit:{user_type}:{identifier}"

        try:
            # Get current timestamp
            now = int(time.time())
            window_start = now - window_seconds

            # Remove old entries
            await self.redis.zremrangebyscore(redis_key, 0, window_start)

            # Count current requests
            current_count = await self.redis.zcard(redis_key)
            remaining = max(0, max_requests - current_count)

            # Get oldest request in window for reset time
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            reset_at = None
            if oldest:
                reset_at = int(oldest[0][1]) + window_seconds

            return {
                "enabled": True,
                "user_type": user_type,
                "limit": max_requests,
                "remaining": remaining,
                "used": current_count,
                "window_seconds": window_seconds,
                "reset_at": reset_at
            }

        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}", exc_info=True)
            return {
                "enabled": True,
                "error": str(e)
            }

    async def reset_limit(self, identifier: str, is_authenticated: bool = False) -> bool:
        """
        Reset rate limit for a user (admin function)

        Returns:
            True if reset successful
        """
        user_type = "authenticated" if is_authenticated else "guest"
        redis_key = f"rate_limit:{user_type}:{identifier}"

        try:
            await self.redis.delete(redis_key)
            logger.info(f"Rate limit reset for {user_type} user: {identifier}")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}", exc_info=True)
            return False
