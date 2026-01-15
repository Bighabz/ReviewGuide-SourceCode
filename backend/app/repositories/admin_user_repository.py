"""
Admin User Repository

Handles all database operations for admin_users table.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.centralized_logger import get_logger

logger = get_logger(__name__)


class AdminUserRepository:
    """Repository for managing admin users"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all admin users"""
        result = await self.db.execute(
            text("""
                SELECT id, username, email, is_active, created_at, updated_at, last_login
                FROM admin_users
                ORDER BY created_at DESC
            """)
        )
        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "is_active": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "last_login": row[6]
            }
            for row in rows
        ]

    async def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get admin user by ID"""
        result = await self.db.execute(
            text("""
                SELECT id, username, email, password_hash, is_active, created_at, updated_at, last_login
                FROM admin_users
                WHERE id = :id
            """),
            {"id": user_id}
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "password_hash": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "last_login": row[7]
        }

    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get admin user by username"""
        result = await self.db.execute(
            text("""
                SELECT id, username, email, password_hash, is_active, created_at, updated_at, last_login
                FROM admin_users
                WHERE username = :username
            """),
            {"username": username}
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "password_hash": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "last_login": row[7]
        }

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get admin user by email"""
        result = await self.db.execute(
            text("""
                SELECT id, username, email, password_hash, is_active, created_at, updated_at, last_login
                FROM admin_users
                WHERE email = :email
            """),
            {"email": email}
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "password_hash": row[3],
            "is_active": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "last_login": row[7]
        }

    async def create(self, username: str, email: str, password_hash: str, is_active: bool = True) -> Dict[str, Any]:
        """Create new admin user"""
        now = datetime.utcnow()
        result = await self.db.execute(
            text("""
                INSERT INTO admin_users (username, email, password_hash, is_active, created_at, updated_at)
                VALUES (:username, :email, :password_hash, :is_active, :created_at, :updated_at)
                RETURNING id
            """),
            {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "is_active": is_active,
                "created_at": now,
                "updated_at": now
            }
        )
        new_id = result.fetchone()[0]
        await self.db.commit()

        return {
            "id": new_id,
            "username": username,
            "email": email,
            "is_active": is_active,
            "created_at": now,
            "updated_at": now,
            "last_login": None
        }

    async def update(self, user_id: int, **kwargs) -> bool:
        """
        Update admin user fields

        Accepts any combination of: username, email, password_hash, is_active
        """
        # Build dynamic update query
        allowed_fields = ["username", "email", "password_hash", "is_active"]
        update_fields = []
        params = {"id": user_id, "updated_at": datetime.utcnow()}

        for field in allowed_fields:
            if field in kwargs:
                update_fields.append(f"{field} = :{field}")
                params[field] = kwargs[field]

        if not update_fields:
            return False

        update_fields.append("updated_at = :updated_at")
        query = f"UPDATE admin_users SET {', '.join(update_fields)} WHERE id = :id"

        await self.db.execute(text(query), params)
        await self.db.commit()
        return True

    async def delete(self, user_id: int) -> bool:
        """Delete admin user"""
        await self.db.execute(
            text("DELETE FROM admin_users WHERE id = :id"),
            {"id": user_id}
        )
        await self.db.commit()
        return True

    async def update_last_login(self, user_id: int) -> bool:
        """Update last_login timestamp"""
        await self.db.execute(
            text("UPDATE admin_users SET last_login = :last_login WHERE id = :id"),
            {"last_login": datetime.utcnow(), "id": user_id}
        )
        await self.db.commit()
        return True

    async def exists_username(self, username: str) -> bool:
        """Check if username exists"""
        result = await self.db.execute(
            text("SELECT id FROM admin_users WHERE username = :username"),
            {"username": username}
        )
        return result.fetchone() is not None

    async def exists_email(self, email: str) -> bool:
        """Check if email exists"""
        result = await self.db.execute(
            text("SELECT id FROM admin_users WHERE email = :email"),
            {"email": email}
        )
        return result.fetchone() is not None
