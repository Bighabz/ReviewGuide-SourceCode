"""
Admin Authentication Middleware

Middleware to verify JWT tokens from Authorization header for admin routes.
This provides an alternative to using dependencies in each endpoint.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.core.centralized_logger import get_logger
from app.utils.auth import verify_token

logger = get_logger(__name__)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify JWT tokens for admin routes

    Checks Authorization header for Bearer token and verifies it.
    Only applies to routes starting with /v1/admin/ (except /v1/admin/auth/login).
    """

    def __init__(self, app, exclude_paths: list = None):
        """
        Initialize middleware

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from authentication check
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/v1/admin/auth/login",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health"
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and verify authentication if needed

        Args:
            request: Incoming request
            call_next: Next middleware or endpoint handler

        Returns:
            Response from next handler or 401 error
        """
        # Check if path should be authenticated
        path = request.url.path

        # Skip authentication for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Only check admin routes
        if not path.startswith("/v1/admin/"):
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"Missing Authorization header for admin route: {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract Bearer token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            logger.warning(f"Invalid Authorization header format for admin route: {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        payload = verify_token(token)
        if not payload:
            logger.warning(f"Invalid or expired token for admin route: {path}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is admin
        user_type = payload.get("type")
        if user_type != "admin":
            logger.warning(f"Non-admin user attempted to access admin route: {path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        # Store user info in request state for use in endpoints
        request.state.user = payload

        # Continue to next handler
        return await call_next(request)
