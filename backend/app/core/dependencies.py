"""
FastAPI Dependencies
Reusable dependency injection functions for authentication, database, etc.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional
from app.core.centralized_logger import get_logger

from app.core.config import settings
from app.core.redis_client import get_redis
from app.core.rate_limiter import RateLimiter
from app.services.geolocation import extract_client_ip

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user from JWT token

    Returns None if no token (allows anonymous access)
    Raises 401 if token is invalid
    """
    if not credentials:
        return None  # Anonymous access allowed

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        user_type = payload.get("type")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"username": username, "type": user_type}

    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_auth(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """
    Require authentication (no anonymous access)

    Raises 401 if not authenticated
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user


async def require_admin(
    current_user: dict = Depends(require_auth)
) -> dict:
    """
    Require admin authentication

    Raises 403 if not admin
    """
    if current_user.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


async def check_rate_limit(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user),
    redis = Depends(get_redis)
) -> None:
    """
    Check rate limit for request

    Uses different limits for guest vs authenticated users
    - Guest users: Identified by IP address
    - Authenticated users: Identified by user ID

    Raises 429 if rate limit exceeded
    """
    rate_limiter = RateLimiter(redis)

    # Determine identifier
    if current_user:
        # Authenticated user - use username as identifier
        identifier = current_user["username"]
        is_authenticated = True
    else:
        # Guest user - use IP address as identifier
        # X-Forwarded-For is only trusted when the connecting IP is a known proxy
        client_ip = extract_client_ip(request)
        if client_ip == "unknown":
            logger.warning("check_rate_limit: could not resolve client IP, skipping rate limit check")
            return
        identifier = f"ip:{client_ip}"
        is_authenticated = False

    # Check rate limit
    await rate_limiter.check_rate_limit(identifier, is_authenticated)
