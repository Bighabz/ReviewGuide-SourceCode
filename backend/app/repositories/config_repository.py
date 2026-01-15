"""
Config Repository

Handles all database operations for core_config table.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.centralized_logger import get_logger

logger = get_logger(__name__)


class ConfigRepository:
    """Repository for managing configuration overrides"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all configs from database"""
        result = await self.db.execute(
            text("SELECT id, key, value, created_at, updated_at FROM core_config ORDER BY key")
        )
        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "key": row[1],
                "value": row[2],
                "created_at": row[3],
                "updated_at": row[4]
            }
            for row in rows
        ]

    async def get_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Get config by ID"""
        result = await self.db.execute(
            text("SELECT id, key, value, created_at, updated_at FROM core_config WHERE id = :id"),
            {"id": config_id}
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "key": row[1],
            "value": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        }

    async def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Get config by key"""
        result = await self.db.execute(
            text("SELECT id, key, value, created_at, updated_at FROM core_config WHERE key = :key"),
            {"key": key}
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "key": row[1],
            "value": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        }

    async def create(self, key: str, value: str) -> Dict[str, Any]:
        """Create new config"""
        now = datetime.utcnow()
        result = await self.db.execute(
            text("INSERT INTO core_config (key, value, created_at, updated_at) VALUES (:key, :value, :created_at, :updated_at) RETURNING id"),
            {"key": key, "value": value, "created_at": now, "updated_at": now}
        )
        new_id = result.fetchone()[0]
        await self.db.commit()

        return {
            "id": new_id,
            "key": key,
            "value": value,
            "created_at": now,
            "updated_at": now
        }

    async def update(self, config_id: int, value: str) -> bool:
        """Update config value"""
        await self.db.execute(
            text("UPDATE core_config SET value = :value, updated_at = :updated_at WHERE id = :id"),
            {"value": value, "updated_at": datetime.utcnow(), "id": config_id}
        )
        await self.db.commit()
        return True

    async def delete(self, config_id: int) -> bool:
        """Delete config"""
        await self.db.execute(
            text("DELETE FROM core_config WHERE id = :id"),
            {"id": config_id}
        )
        await self.db.commit()
        return True

    async def exists(self, key: str) -> bool:
        """Check if config key exists"""
        result = await self.db.execute(
            text("SELECT id FROM core_config WHERE key = :key"),
            {"key": key}
        )
        return result.fetchone() is not None

    async def bulk_create(self, configs: List[Dict[str, str]]) -> int:
        """Bulk insert configs"""
        now = datetime.utcnow()
        count = 0

        for config in configs:
            # Check if exists first
            exists = await self.exists(config["key"])
            if not exists:
                await self.db.execute(
                    text("INSERT INTO core_config (key, value, created_at, updated_at) VALUES (:key, :value, :created_at, :updated_at)"),
                    {"key": config["key"], "value": config["value"], "created_at": now, "updated_at": now}
                )
                count += 1

        await self.db.commit()
        return count
