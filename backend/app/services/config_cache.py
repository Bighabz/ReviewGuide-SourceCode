"""
Config Cache Service

Redis-based configuration caching with single snapshot approach (Magento 2 style).
Priority: Redis snapshot → Database → .env

Single snapshot: All configs cached as one serialized object in Redis.
No TTL: Cache only invalidated on admin changes, then immediately rebuilt.

Security: Sensitive configs (API keys, secrets) are encrypted in database.
"""
from app.core.centralized_logger import get_logger
from app.services.config_encryption import get_config_encryption
from typing import Optional, Any, Dict
import json

logger = get_logger(__name__)

# Config snapshot key (single key for entire config)
CONFIG_SNAPSHOT_KEY = "config:snapshot"


class ConfigCache:
    """
    Configuration cache manager with Redis single snapshot approach.

    Stores entire config as single snapshot in Redis.
    Cache invalidated only on admin changes, then immediately rebuilt.
    No TTL - cache lives forever until explicitly invalidated.
    """

    def __init__(self, settings_instance):
        self.settings = settings_instance
        self.encryption = get_config_encryption()

    async def _get_redis(self):
        """Get Redis client lazily"""
        from app.core.redis_client import get_redis
        try:
            return await get_redis()
        except Exception as e:
            logger.warning(f"[ConfigCache] Failed to get Redis client: {e}")
            return None

    async def load_all(self) -> Dict[str, Any]:
        """
        Load all configs with priority: Redis snapshot → Database → .env

        Returns:
            Dictionary of all config values with correct types
        """
        try:
            redis = await self._get_redis()

            # 1. Try Redis snapshot first (if Redis available)
            if redis:
                snapshot = await redis.get(CONFIG_SNAPSHOT_KEY)
                if snapshot:
                    logger.info(f"[ConfigCache] Snapshot HIT - loaded all configs from Redis cache")
                    return self._deserialize_snapshot(snapshot)

                logger.info(f"[ConfigCache] Snapshot MISS - will load from DB and rebuild cache")

            # 2. Load from database + .env and build snapshot
            config_dict = await self._build_config_dict()

            # 3. Save snapshot to Redis (cache warming)
            if redis:
                await self._save_snapshot(config_dict, redis)

            return config_dict

        except Exception as e:
            logger.error(f"[ConfigCache] Error loading configs: {e}", exc_info=True)
            # Fall back to .env only
            return self._get_all_from_env()

    async def _build_config_dict(self) -> Dict[str, Any]:
        """
        Build config dictionary from Database → .env priority.

        Returns:
            Dictionary with all config values
        """
        from app.core.database import AsyncSessionLocal
        from app.repositories.config_repository import ConfigRepository

        config_dict = {}

        # Start with .env defaults
        for key in self.settings.model_fields.keys():
            env_value = self._get_from_env(key)
            if env_value is not None:
                config_dict[key] = env_value

        # Override with database values
        if AsyncSessionLocal:
            async with AsyncSessionLocal() as db:
                config_repo = ConfigRepository(db)
                db_configs = await config_repo.get_all()

                for config in db_configs:
                    key = config["key"]
                    if key in config_dict:  # Only override if key exists in Settings
                        raw_value = config["value"]

                        # Decrypt if encrypted
                        if self.encryption.is_encrypted(raw_value):
                            decrypted_value = self.encryption.decrypt(raw_value)
                            typed_value = self._convert_type(key, decrypted_value)
                            logger.debug(f"[ConfigCache] DB override (encrypted): {key} = <masked>")
                        else:
                            typed_value = self._convert_type(key, raw_value)
                            logger.debug(f"[ConfigCache] DB override: {key} = {typed_value}")

                        config_dict[key] = typed_value

        return config_dict

    async def set(self, key: str, value: Any) -> bool:
        """
        Set config value in database, invalidate cache, and rebuild snapshot.

        Args:
            key: Config key name
            value: Config value

        Returns:
            True if successful
        """
        try:
            redis = await self._get_redis()

            # 1. Save to database
            await self._set_in_db(key, value)

            # 2. Invalidate and rebuild snapshot (cache warming)
            if redis:
                await self._invalidate_and_rebuild(redis)

            # 3. Update in-memory settings for current process
            self._set_in_settings(key, value)

            logger.info(f"[ConfigCache] Set config {key} = {value}, rebuilt cache snapshot")
            return True

        except Exception as e:
            logger.error(f"[ConfigCache] Error setting config {key}: {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete config from database, invalidate cache, and rebuild snapshot.

        Args:
            key: Config key name

        Returns:
            True if successful
        """
        try:
            redis = await self._get_redis()

            # 1. Delete from database
            await self._delete_from_db(key)

            # 2. Invalidate and rebuild snapshot (cache warming)
            if redis:
                await self._invalidate_and_rebuild(redis)

            # 3. Reset to .env value in settings for current process
            env_value = self._get_original_env_value(key)
            if env_value is not None:
                self._set_in_settings(key, env_value)

            logger.info(f"[ConfigCache] Deleted config {key}, rebuilt cache snapshot")
            return True

        except Exception as e:
            logger.error(f"[ConfigCache] Error deleting config {key}: {e}", exc_info=True)
            return False

    async def invalidate_all(self, rebuild: bool = True) -> bool:
        """
        Invalidate entire config snapshot cache.

        Args:
            rebuild: If True, immediately rebuild snapshot after invalidation (cache warming)

        Returns:
            True if successful
        """
        try:
            redis = await self._get_redis()
            if not redis:
                return False

            if rebuild:
                # Invalidate + rebuild (cache warming)
                await self._invalidate_and_rebuild(redis)
            else:
                # Just invalidate
                await redis.delete(CONFIG_SNAPSHOT_KEY)
                logger.info(f"[ConfigCache] Invalidated config snapshot")

            return True
        except Exception as e:
            logger.error(f"[ConfigCache] Error invalidating snapshot: {e}", exc_info=True)
            return False

    async def _get_from_db(self, key: str) -> Optional[Any]:
        """Get config value from database"""
        from app.core.database import AsyncSessionLocal
        from app.repositories.config_repository import ConfigRepository

        if not AsyncSessionLocal:
            return None

        async with AsyncSessionLocal() as db:
            config_repo = ConfigRepository(db)
            config = await config_repo.get_by_key(key)

            if not config:
                return None

            # Convert to correct type
            return self._convert_type(key, config["value"])

    async def _set_in_db(self, key: str, value: Any) -> bool:
        """Set config value in database (encrypts sensitive values)"""
        from app.core.database import AsyncSessionLocal
        from app.repositories.config_repository import ConfigRepository

        if not AsyncSessionLocal:
            return False

        async with AsyncSessionLocal() as db:
            config_repo = ConfigRepository(db)

            # Check if exists
            existing = await config_repo.get_by_key(key)

            # Convert value to string
            str_value = str(value)

            # Encrypt if this is a sensitive field
            if self.encryption.should_encrypt(key):
                str_value = self.encryption.encrypt(str_value)
                logger.debug(f"[ConfigCache] Encrypted {key} before saving to DB")

            if existing:
                # Update
                await config_repo.update(existing["id"], str_value)
            else:
                # Create
                await config_repo.create(key, str_value)

            return True

    async def _delete_from_db(self, key: str) -> bool:
        """Delete config from database"""
        from app.core.database import AsyncSessionLocal
        from app.repositories.config_repository import ConfigRepository

        if not AsyncSessionLocal:
            return False

        async with AsyncSessionLocal() as db:
            config_repo = ConfigRepository(db)
            config = await config_repo.get_by_key(key)

            if config:
                await config_repo.delete(config["id"])

            return True

    async def _save_snapshot(self, config_dict: Dict[str, Any], redis):
        """Save config snapshot to Redis (no TTL - lives forever)"""
        try:
            serialized = json.dumps(config_dict, default=str)
            await redis.set(CONFIG_SNAPSHOT_KEY, serialized)
            logger.info(f"[ConfigCache] Saved config snapshot to Redis ({len(config_dict)} configs)")
        except Exception as e:
            logger.warning(f"[ConfigCache] Failed to save snapshot: {e}")

    def _deserialize_snapshot(self, snapshot: str) -> Dict[str, Any]:
        """Deserialize config snapshot from Redis"""
        try:
            raw_dict = json.loads(snapshot)
            # Convert types based on Settings fields
            typed_dict = {}
            for key, value in raw_dict.items():
                typed_dict[key] = self._convert_type(key, value)
            return typed_dict
        except Exception as e:
            logger.error(f"[ConfigCache] Failed to deserialize snapshot: {e}")
            return {}

    async def _invalidate_and_rebuild(self, redis):
        """Invalidate cache and immediately rebuild (cache warming)"""
        try:
            # 1. Delete snapshot
            await redis.delete(CONFIG_SNAPSHOT_KEY)
            logger.info(f"[ConfigCache] Invalidated config snapshot")

            # 2. Rebuild snapshot immediately (cache warming)
            config_dict = await self._build_config_dict()
            await self._save_snapshot(config_dict, redis)
            logger.info(f"[ConfigCache] Rebuilt config snapshot (cache warming)")
        except Exception as e:
            logger.error(f"[ConfigCache] Failed to invalidate and rebuild: {e}")

    def _get_from_env(self, key: str) -> Optional[Any]:
        """Get config value from .env (current settings)"""
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
        return None

    def _get_all_from_env(self) -> Dict[str, Any]:
        """Get all config values from .env"""
        config_dict = {}
        for key in self.settings.model_fields.keys():
            value = self._get_from_env(key)
            if value is not None:
                config_dict[key] = value
        return config_dict

    def _get_original_env_value(self, key: str) -> Optional[Any]:
        """Get original .env value (before database overrides)"""
        # This would require storing original values, for now just return current value
        return self._get_from_env(key)

    def _set_in_settings(self, key: str, value: Any):
        """Update in-memory settings instance"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)

    def _convert_type(self, key: str, value: str) -> Any:
        """Convert string value to correct type based on Settings field"""
        if not hasattr(self.settings, key):
            return value

        field_info = self.settings.model_fields.get(key)
        if not field_info:
            return value

        field_type = field_info.annotation

        try:
            if field_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else bool(value)
            elif field_type == int:
                return int(value)
            elif field_type == float:
                return float(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f"[ConfigCache] Type conversion failed for {key}: {e}")
            return value



# Global config cache instance
_config_cache: Optional[ConfigCache] = None


def get_config_cache() -> ConfigCache:
    """
    Get global config cache instance (lazy initialization).
    Creates instance on first call.
    """
    global _config_cache
    if _config_cache is None:
        from app.core.config import settings
        _config_cache = ConfigCache(settings)
        logger.info("[ConfigCache] Lazy initialized config cache")
    return _config_cache
