"""
Config Service

Business logic for config management operations.
Handles listing, masking, and managing config values from DB and .env.
"""
from app.core.centralized_logger import get_logger
from app.services.config_encryption import get_config_encryption
from app.repositories.config_repository import ConfigRepository
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = get_logger(__name__)


class ConfigService:
    """Service for managing configuration operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConfigRepository(db)
        self.encryption = get_config_encryption()

    async def list_all_configs(self) -> List[Dict[str, Any]]:
        """
        List all configuration items from both database and .env.

        Returns configs from core_config table merged with .env defaults.
        Sensitive values (API keys, secrets, passwords) are masked with *********.

        Returns:
            List of config items with keys: id, key, value, source, created_at, updated_at
        """
        try:
            # Get configs from database
            db_configs = await self.repo.get_all()

            # Convert to dict for easy lookup, masking sensitive values
            db_config_dict = {}
            for config in db_configs:
                key = config["key"]
                value = config["value"]

                # Mask sensitive values
                if self.encryption.should_encrypt(key):
                    value = self.encryption.mask_value(value)

                db_config_dict[key] = {
                    **config,
                    "value": value,
                    "source": "db"
                }

            # Get configs from .env file
            env_configs = self._parse_env_file(db_config_dict)

            # Combine DB configs (priority) + env configs
            all_configs = list(db_config_dict.values()) + env_configs

            return all_configs

        except Exception as e:
            logger.error(f"[ConfigService] Error listing configs: {str(e)}")
            raise

    async def get_config_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single config item by ID.

        Sensitive values are masked with *********.

        Args:
            config_id: Database ID of the config

        Returns:
            Config dict with keys: id, key, value, source, created_at, updated_at
            None if not found
        """
        try:
            config = await self.repo.get_by_id(config_id)

            if not config:
                return None

            # Mask sensitive values
            key = config["key"]
            value = config["value"]
            if self.encryption.should_encrypt(key):
                value = self.encryption.mask_value(value)

            return {**config, "value": value, "source": "db"}

        except Exception as e:
            logger.error(f"[ConfigService] Error getting config {config_id}: {str(e)}")
            raise

    async def update_config(self, config_id: int, new_value: str) -> Dict[str, Any]:
        """
        Update a config value (updates DB, Redis cache, and in-memory settings).

        Args:
            config_id: Database ID of the config
            new_value: New value to set

        Returns:
            Updated config dict

        Raises:
            ValueError: If config not found
        """
        from app.services.config_cache import get_config_cache

        try:
            # Check if exists
            config = await self.repo.get_by_id(config_id)
            if not config:
                raise ValueError("Config not found")

            key = config["key"]

            # Update through config cache (updates DB + Redis + settings)
            config_cache = get_config_cache()
            if config_cache:
                success = await config_cache.set(key, new_value)
                if not success:
                    raise RuntimeError("Failed to update config cache")
                logger.info(f"[ConfigService] Updated config {key} through cache")
            else:
                # Fallback to direct DB update
                await self.repo.update(config_id, new_value)
                logger.warning(f"[ConfigService] Config cache not available, updated DB only")

            # Return updated config (masked if sensitive)
            return await self.get_config_by_id(config_id)

        except Exception as e:
            logger.error(f"[ConfigService] Error updating config {config_id}: {str(e)}")
            raise

    async def delete_config(self, config_id: int) -> None:
        """
        Delete a config (deletes from DB and Redis, reverts to .env default).

        Args:
            config_id: Database ID of the config

        Raises:
            ValueError: If config not found
        """
        from app.services.config_cache import get_config_cache

        try:
            # Check if exists
            config = await self.repo.get_by_id(config_id)
            if not config:
                raise ValueError("Config not found")

            key = config["key"]

            # Delete through config cache (removes from DB + Redis + resets settings)
            config_cache = get_config_cache()
            if config_cache:
                success = await config_cache.delete(key)
                if not success:
                    raise RuntimeError("Failed to delete from config cache")
                logger.info(f"[ConfigService] Deleted config {key} from cache")
            else:
                # Fallback to direct DB delete
                await self.repo.delete(config_id)
                logger.warning(f"[ConfigService] Config cache not available, deleted from DB only")

        except Exception as e:
            logger.error(f"[ConfigService] Error deleting config {config_id}: {str(e)}")
            raise

    async def create_config(self, key: str, value: str) -> Dict[str, Any]:
        """
        Create a new config override (saves to DB, Redis cache, and in-memory settings).

        Args:
            key: Config key name
            value: Config value

        Returns:
            Newly created config dict (masked if sensitive)

        Raises:
            ValueError: If key already exists
        """
        from app.services.config_cache import get_config_cache

        try:
            # Check if key already exists
            if await self.repo.exists(key):
                raise ValueError("Config key already exists")

            # Create through config cache (saves to DB + Redis + settings)
            config_cache = get_config_cache()
            if config_cache:
                success = await config_cache.set(key, value)
                if not success:
                    raise RuntimeError("Failed to save to config cache")
                logger.info(f"[ConfigService] Created config {key} through cache")
            else:
                # Fallback to direct DB insert
                await self.repo.create(key, value)
                logger.warning(f"[ConfigService] Config cache not available, saved to DB only")

            # Return newly created config (masked if sensitive)
            new_config = await self.repo.get_by_key(key)

            # Mask sensitive values
            masked_value = value
            if self.encryption.should_encrypt(key):
                masked_value = self.encryption.mask_value(value)

            return {**new_config, "value": masked_value, "source": "db"}

        except Exception as e:
            logger.error(f"[ConfigService] Error creating config: {str(e)}")
            raise

    async def clear_cache(self) -> bool:
        """
        Invalidate config cache snapshot and rebuild (cache warming).

        Returns:
            True if successful, False if Redis not available
        """
        from app.services.config_cache import get_config_cache

        try:
            config_cache = get_config_cache()
            success = await config_cache.invalidate_all(rebuild=True)

            if success:
                logger.info(f"[ConfigService] Invalidated and rebuilt config snapshot cache")
            else:
                logger.warning(f"[ConfigService] Redis not available, cache not cleared")

            return success

        except Exception as e:
            logger.error(f"[ConfigService] Error clearing config cache: {str(e)}")
            raise

    def _parse_env_file(self, db_config_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse .env file to get all environment variables.

        Args:
            db_config_dict: Dictionary of configs from database (to avoid duplicates)

        Returns:
            List of env config items
        """
        env_configs = []

        try:
            # Find .env file (3 levels up from this file)
            backend_dir = Path(__file__).parent.parent.parent
            env_file = backend_dir / ".env"

            if not env_file.exists():
                logger.warning(f"[ConfigService] .env file not found at {env_file}")
                return []

            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse key=value
                    if '=' not in line:
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # If not in DB, add as env source
                    if key not in db_config_dict:
                        # Mask sensitive values from .env
                        if self.encryption.should_encrypt(key):
                            value = self.encryption.mask_value(value)

                        env_configs.append({
                            "id": None,
                            "key": key,
                            "value": value,
                            "source": "env",
                            "created_at": None,
                            "updated_at": None
                        })

        except Exception as e:
            logger.error(f"[ConfigService] Error parsing .env file: {str(e)}")

        return env_configs
