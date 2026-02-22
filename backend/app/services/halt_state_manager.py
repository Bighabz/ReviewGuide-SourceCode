"""
Halt State Manager
Centralized service for saving and loading halt state to/from Redis with process-level caching
"""
import json
from app.core.centralized_logger import get_logger
from typing import Dict, Any, Optional

from app.core.redis_client import get_redis
from app.services.state_serializer import (
    safe_serialize_state, StateOverflowError, check_state_size, MAX_TOOL_INPUTS_BYTES
)

logger = get_logger(__name__)


class HaltStateManager:
    """
    Manages halt state persistence in Redis with process-level caching.

    Architecture:
    1. First access in a request: Load from Redis and cache in memory
    2. Subsequent accesses: Read from memory cache (no Redis call)
    3. Any update: Update memory cache AND save to Redis
    4. This ensures Redis is always in sync while minimizing Redis calls

    Halt state is saved when workflow halts (status="halted", halt=True)
    and loaded when resuming from a halted state.

    This ensures slots, intent, and other workflow state persist across
    user interactions in the travel booking flow.
    """

    # TTL for halt state in Redis - loaded from config
    from app.core.config import settings
    HALT_STATE_TTL = settings.HALT_STATE_TTL

    # Process-level cache: {session_id: halt_state_data}
    # This cache is shared across all method calls within the same request/process
    _cache: Dict[str, Optional[Dict[str, Any]]] = {}

    @staticmethod
    def _get_halt_key(session_id: str) -> str:
        """Generate Redis key for halt state"""
        return f"halt_state:{session_id}"

    @staticmethod
    async def get_halt_state(session_id: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get halt state from cache or Redis.

        This is the MAIN method that all code should use to access halt state.

        Flow:
        1. If force_reload=True, bypass cache and load from Redis
        2. Check if data exists in process cache
        3. If yes, return cached data (no Redis call)
        4. If no, load from Redis and cache it

        Args:
            session_id: Session identifier
            force_reload: If True, bypass cache and reload from Redis

        Returns:
            Halt state dict if found, None otherwise
        """
        # Check cache first (unless force_reload)
        if not force_reload and session_id in HaltStateManager._cache:
            cached_data = HaltStateManager._cache[session_id]
            # if cached_data:
            #     logger.info(
            #         f"📦 GET halt state (CACHED): session={session_id}\n"
            #         f"  Data: {json.dumps(cached_data, indent=2, default=str)}"
            #     )
            # else:
            #     logger.debug(f"📦 GET halt state (CACHED): session={session_id}, data=None")
            return cached_data

        # Not in cache - load from Redis
        try:
            redis = await get_redis()
            halt_key = HaltStateManager._get_halt_key(session_id)

            # Check if halt state exists
            exists = await redis.exists(halt_key)
            if not exists:
                logger.debug(f"No halt state found in Redis: session={session_id}")
                # Cache the "None" result to avoid repeated Redis calls
                HaltStateManager._cache[session_id] = None
                return None

            # Load from Redis
            halt_state_json = await redis.get(halt_key)
            if not halt_state_json:
                HaltStateManager._cache[session_id] = None
                return None

            # Deserialize
            halt_state_data = json.loads(halt_state_json)

            # Cache it
            HaltStateManager._cache[session_id] = halt_state_data

            reload_msg = " (FORCE RELOAD)" if force_reload else ""
            logger.info(
                f"🔄 GET halt state (from Redis{reload_msg}): session={session_id}\n"
                f"  Data: {json.dumps(halt_state_data, indent=2, default=str)}"
            )

            return halt_state_data

        except Exception as e:
            logger.error(f"Failed to load halt state from Redis: {e}", exc_info=True)
            return None

    @staticmethod
    async def update_halt_state(
        session_id: str,
        result_state: Dict[str, Any]
    ) -> bool:
        """
        Update halt state in BOTH cache and Redis.

        This is the MAIN method that all code should use to update halt state.

        Flow:
        1. Update process cache immediately
        2. Save to Redis for persistence

        Args:
            session_id: Session identifier
            result_state: Full workflow result state

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Start with core fields
            halt_state_data = {
                "intent": result_state.get("intent"),
                "slots": result_state.get("slots", {}),
                "followups": result_state.get("followups", [])
            }

            # Preserve any additional fields from result_state
            for key, value in result_state.items():
                if key not in halt_state_data and not key.startswith("_"):
                    halt_state_data[key] = value

            # Update cache FIRST
            HaltStateManager._cache[session_id] = halt_state_data

            # Then persist to Redis
            redis = await get_redis()
            halt_key = HaltStateManager._get_halt_key(session_id)

            # Serialize with non-serializable value stripping (RFC §1.6)
            try:
                # Check the plan key which can be large
                if "plan" in halt_state_data:
                    check_state_size(halt_state_data, "plan", MAX_TOOL_INPUTS_BYTES)
                json_data = safe_serialize_state(halt_state_data)
            except StateOverflowError as exc:
                logger.warning(
                    f"[halt_state_manager] StateOverflowError for session={session_id}: {exc}. "
                    "Serializing without size enforcement."
                )
                json_data = safe_serialize_state(halt_state_data)

            # Save to Redis with TTL
            await redis.setex(halt_key, HaltStateManager.HALT_STATE_TTL, json_data)

            logger.info(
                f"💾 UPDATE halt state (cache + Redis): session={session_id}\n"
                f"  Data: {json.dumps(halt_state_data, indent=2, default=str)}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update halt state: {e}", exc_info=True)
            return False

    @staticmethod
    async def delete_halt_state(session_id: str) -> bool:
        """
        Delete halt state from BOTH cache and Redis.

        Called when workflow completes successfully.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Remove from cache
            if session_id in HaltStateManager._cache:
                del HaltStateManager._cache[session_id]

            # Remove from Redis
            redis = await get_redis()
            halt_key = HaltStateManager._get_halt_key(session_id)
            await redis.delete(halt_key)

            logger.info(f"🗑️ DELETE halt state (cache + Redis): session={session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete halt state: {e}", exc_info=True)
            return False

    @staticmethod
    async def check_if_resume(session_id: str, current_intent: Optional[str] = None) -> bool:
        """
        Check if this is a resume from a halted state.

        If intent differs from halted intent, automatically clears halt state
        and returns False (treat as new request).

        Args:
            session_id: Session identifier
            current_intent: Current request intent (optional)

        Returns:
            True if resuming valid halt state, False otherwise
        """
        try:
            halt_state = await HaltStateManager.get_halt_state(session_id)
            if not halt_state:
                return False

            # Check if intent matches
            halted_intent = halt_state.get("intent")
            if current_intent and halted_intent and current_intent != halted_intent:
                logger.info(
                    f"Intent changed from '{halted_intent}' to '{current_intent}' - "
                    f"clearing halt state for session={session_id}"
                )
                await HaltStateManager.delete_halt_state(session_id)
                return False

            return True
        except Exception as e:
            logger.error(f"Failed to check if resume: {e}", exc_info=True)
            return False

    @staticmethod
    async def update_field(session_id: str, field_name: str, field_value: Any) -> bool:
        """
        Update a single field in halt state.

        Args:
            session_id: Session identifier
            field_name: Name of field to update
            field_value: New value for the field

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Load current halt state
            halt_state = await HaltStateManager.get_halt_state(session_id)
            if not halt_state:
                logger.warning(f"Cannot update field '{field_name}' - no halt state exists for session={session_id}")
                return False

            # Update the field
            halt_state[field_name] = field_value

            # Save back to Redis and cache
            await HaltStateManager.update_halt_state(session_id, halt_state)

            logger.info(f"✏️ Updated field '{field_name}' in halt state: session={session_id}, value={field_value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update field '{field_name}': {e}", exc_info=True)
            return False

    @staticmethod
    async def check_halt_exists(session_id: str) -> bool:
        """
        Check if halt state exists (checks cache first, then Redis).

        Args:
            session_id: Session identifier

        Returns:
            True if halt state exists, False otherwise
        """
        # Check cache first
        if session_id in HaltStateManager._cache:
            return HaltStateManager._cache[session_id] is not None

        # Not in cache - check Redis
        try:
            redis = await get_redis()
            halt_key = HaltStateManager._get_halt_key(session_id)
            exists = await redis.exists(halt_key)
            return bool(exists)

        except Exception as e:
            logger.error(f"Failed to check halt state exists: {e}", exc_info=True)
            return False

    @staticmethod
    def clear_cache(session_id: Optional[str] = None):
        """
        Clear process cache.

        Args:
            session_id: If provided, clear only this session. If None, clear all.
        """
        if session_id:
            if session_id in HaltStateManager._cache:
                del HaltStateManager._cache[session_id]
                logger.debug(f"Cleared cache for session: {session_id}")
        else:
            HaltStateManager._cache.clear()
            logger.debug("Cleared all cache")

    # Backward compatibility aliases
    @staticmethod
    async def save_halt_state(session_id: str, result_state: Dict[str, Any]) -> bool:
        """Alias for update_halt_state (backward compatibility)"""
        return await HaltStateManager.update_halt_state(session_id, result_state)

    @staticmethod
    async def load_halt_state(session_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_halt_state (backward compatibility)"""
        return await HaltStateManager.get_halt_state(session_id)
