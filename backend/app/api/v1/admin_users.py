"""
Admin User Management API Endpoints

Provides CRUD endpoints for managing admin users:
- List all admin users
- Create new admin user
- Update admin user
- Delete admin user

All endpoints require admin authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.centralized_logger import get_logger
from app.repositories.admin_user_repository import AdminUserRepository
from app.utils.auth import hash_password
from app.api.v1.admin_auth import get_current_admin_user

logger = get_logger(__name__)
router = APIRouter()


# ===== Pydantic Models =====

class AdminUserResponse(BaseModel):
    """Admin user response model"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]


class CreateAdminUserRequest(BaseModel):
    """Request model for creating admin user"""
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    is_active: bool = Field(default=True, description="Active status")


class UpdateAdminUserRequest(BaseModel):
    """Request model for updating admin user"""
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    is_active: Optional[bool] = Field(None, description="Active status")


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


# ===== Admin User Management Endpoints =====

@router.get("", response_model=List[AdminUserResponse])
async def list_admin_users(
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all admin users

    Requires admin authentication.
    """
    try:
        repo = AdminUserRepository(db)
        users = await repo.get_all()

        logger.info(f"Admin user {current_user['username']} listed all admin users")

        return [
            {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "is_active": user["is_active"],
                "created_at": user["created_at"],
                "updated_at": user["updated_at"],
                "last_login": user["last_login"]
            }
            for user in users
        ]

    except Exception as e:
        logger.error(f"Error listing admin users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list admin users"
        )


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    user_data: CreateAdminUserRequest,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create new admin user

    Requires admin authentication.
    """
    try:
        repo = AdminUserRepository(db)

        # Check if username already exists
        if await repo.exists_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Check if email already exists
        if await repo.exists_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        new_user = await repo.create(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            is_active=user_data.is_active
        )

        logger.info(f"Admin user {current_user['username']} created new admin user: {user_data.username}")

        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "is_active": new_user["is_active"],
            "created_at": new_user["created_at"],
            "updated_at": new_user["updated_at"],
            "last_login": new_user["last_login"]
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: int,
    user_data: UpdateAdminUserRequest,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update admin user

    Requires admin authentication.
    Can update username, email, password, and active status.
    """
    try:
        repo = AdminUserRepository(db)

        # Check if user exists
        user = await repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )

        # Prepare update data
        update_data = {}

        if user_data.username is not None:
            # Check if new username conflicts with another user
            if user_data.username != user["username"]:
                if await repo.exists_username(user_data.username):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
            update_data["username"] = user_data.username

        if user_data.email is not None:
            # Check if new email conflicts with another user
            if user_data.email != user["email"]:
                if await repo.exists_email(user_data.email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
            update_data["email"] = user_data.email

        if user_data.password is not None:
            # Hash new password
            update_data["password_hash"] = hash_password(user_data.password)

        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active

        # Update user
        if update_data:
            await repo.update(user_id, **update_data)

        # Fetch updated user
        updated_user = await repo.get_by_id(user_id)

        logger.info(f"Admin user {current_user['username']} updated admin user: {updated_user['username']}")

        return {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "email": updated_user["email"],
            "is_active": updated_user["is_active"],
            "created_at": updated_user["created_at"],
            "updated_at": updated_user["updated_at"],
            "last_login": updated_user["last_login"]
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating admin user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin user"
        )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_admin_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete admin user

    Requires admin authentication.
    Users cannot delete themselves.
    """
    try:
        repo = AdminUserRepository(db)

        # Check if user exists
        user = await repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found"
            )

        # Prevent self-deletion
        if user_id == current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Delete user
        await repo.delete(user_id)

        logger.info(f"Admin user {current_user['username']} deleted admin user: {user['username']}")

        return {"message": f"Admin user {user['username']} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting admin user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete admin user"
        )
