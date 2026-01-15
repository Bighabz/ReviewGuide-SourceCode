"""
Admin Authentication API Endpoints

Provides endpoints for admin user authentication:
- Login with username/password
- Get current user info
- Logout
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.centralized_logger import get_logger
from app.repositories.admin_user_repository import AdminUserRepository
from app.utils.auth import hash_password, verify_password, create_access_token, verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


# ===== Pydantic Models =====

class LoginRequest(BaseModel):
    """Login request body"""
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class UserResponse(BaseModel):
    """User information response"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]


class LoginResponse(BaseModel):
    """Login response with token and user info"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


# ===== Helper Functions =====

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated admin user from Bearer token

    Raises 401 if token is invalid or user not found
    """
    token = credentials.credentials

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = payload.get("sub")
    user_type = payload.get("type")

    if not user_id or user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    repo = AdminUserRepository(db)
    user = await repo.get_by_id(int(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ===== Authentication Endpoints =====

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Admin login endpoint

    Authenticates admin user with username and password.
    Returns JWT access token valid for 24 hours.
    """
    try:
        repo = AdminUserRepository(db)

        # Get user by username
        user = await repo.get_by_username(login_data.username)

        if not user:
            logger.warning(f"Login attempt with non-existent username: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Check if user is active
        if not user["is_active"]:
            logger.warning(f"Login attempt for inactive user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )

        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            logger.warning(f"Failed login attempt for user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Update last login timestamp
        await repo.update_last_login(user["id"])

        # Create access token
        token_data = {
            "sub": str(user["id"]),
            "username": user["username"],
            "type": "admin"
        }
        access_token = create_access_token(token_data)

        logger.info(f"Successful login for admin user: {login_data.username}")

        # Return token and user info
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_active": user["is_active"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "last_login": datetime.utcnow()  # Return current time as last_login
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get current authenticated admin user information

    Requires valid Bearer token in Authorization header.
    """
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"],
        "updated_at": current_user["updated_at"],
        "last_login": current_user["last_login"]
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_admin_user)):
    """
    Admin logout endpoint

    Requires valid Bearer token. Currently just returns success.
    Token invalidation is handled client-side by removing the token.
    """
    logger.info(f"Admin user logged out: {current_user['username']}")
    return {"message": "Logout successful"}
