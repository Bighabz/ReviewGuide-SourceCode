"""
Chat History Manager

Efficiently loads and caches conversation history from database.
Similar to HaltStateManager but focused on conversation history.
"""

from app.core.centralized_logger import get_logger
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.redis_client import redis_client

logger = get_logger(__name__)


class ChatHistoryManager:
    """
    Manages conversation history caching and retrieval.

    Uses Redis for caching to reduce database load.
    Falls back to database when Redis is unavailable.
    """

    CACHE_KEY_PREFIX = "chat_history:"
    from app.core.config import settings
    CACHE_TTL = settings.CHAT_HISTORY_CACHE_TTL

    @staticmethod
    def _get_cache_key(session_id: str) -> str:
        """Get Redis cache key for session history."""
        return f"{ChatHistoryManager.CACHE_KEY_PREFIX}{session_id}"

    @staticmethod
    async def get_history(
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return (None = all)

        Returns:
            List of conversation messages [{"role": "user"|"assistant", "content": str}, ...]
        """
        if limit is None:
            limit = settings.MAX_HISTORY_MESSAGES

        # Try Redis cache first
        if redis_client is not None:
            try:
                cache_key = ChatHistoryManager._get_cache_key(session_id)
                cached_data = await redis_client.get(cache_key)

                if cached_data:
                    import json
                    history = json.loads(cached_data)
                    logger.info(f"[ChatHistoryManager] Loaded {len(history)} messages from Redis cache for session {session_id}")

                    # Apply limit
                    if limit and len(history) > limit:
                        history = history[-limit:]

                    return history
            except Exception as e:
                logger.warning(f"[ChatHistoryManager] Redis cache read failed: {e}")

            # Fast path: check if session has any history at all (lightweight key existence check)
            try:
                exists_key = f"session:{session_id}:has_history"
                has_history = await redis_client.exists(exists_key)
                if not has_history:
                    logger.info(f"[ChatHistoryManager] New session {session_id} — skipping DB load")
                    return []
            except Exception as e:
                logger.warning(f"[ChatHistoryManager] Redis exists check failed: {e}")
                # Fall through to DB load

        # Fall back to database
        logger.info(f"[ChatHistoryManager] Cache miss, loading from database for session {session_id}")

        # Create ConversationRepository internally
        from app.repositories.conversation_repository import ConversationRepository
        from app.core.database import get_db
        from app.core.redis_client import get_redis

        # get_db() is an async generator, need to iterate it properly
        db_gen = get_db()
        db = await anext(db_gen)
        redis = await get_redis()

        try:
            conversation_repo = ConversationRepository(db=db, redis=redis)
            history = await conversation_repo.get_history(session_id, limit=limit)
        finally:
            # Close the database session
            await db_gen.aclose()

        # Cache the result in Redis
        if redis_client is not None and history:
            try:
                import json
                cache_key = ChatHistoryManager._get_cache_key(session_id)
                await redis_client.set(
                    cache_key,
                    json.dumps(history),
                    ex=ChatHistoryManager.CACHE_TTL
                )
                logger.info(f"[ChatHistoryManager] Cached {len(history)} messages in Redis for session {session_id}")
            except Exception as e:
                logger.warning(f"[ChatHistoryManager] Redis cache write failed: {e}")

        return history

    @staticmethod
    async def invalidate_cache(session_id: str) -> None:
        """
        Invalidate cached history for a session.

        Call this after adding new messages to force reload from database.

        Args:
            session_id: Session ID
        """
        if redis_client is not None:
            try:
                cache_key = ChatHistoryManager._get_cache_key(session_id)
                await redis_client.delete(cache_key)
                logger.info(f"[ChatHistoryManager] Invalidated cache for session {session_id}")
            except Exception as e:
                logger.warning(f"[ChatHistoryManager] Cache invalidation failed: {e}")

    @staticmethod
    async def update_cache(
        session_id: str,
        new_message: Dict[str, Any]
    ) -> None:
        """
        Add a new message to cached history (append-only optimization).

        Args:
            session_id: Session ID
            new_message: Message dict with role and content
        """
        if redis_client is not None:
            try:
                cache_key = ChatHistoryManager._get_cache_key(session_id)
                cached_data = await redis_client.get(cache_key)

                if cached_data:
                    import json
                    history = json.loads(cached_data)
                    history.append(new_message)

                    # Keep only last N messages
                    max_messages = settings.MAX_HISTORY_MESSAGES * 2  # Keep more in cache
                    if len(history) > max_messages:
                        history = history[-max_messages:]

                    await redis_client.set(
                        cache_key,
                        json.dumps(history),
                        ex=ChatHistoryManager.CACHE_TTL
                    )
                    logger.debug(f"[ChatHistoryManager] Updated cache with new message for session {session_id}")
            except Exception as e:
                logger.warning(f"[ChatHistoryManager] Cache update failed: {e}")

    @staticmethod
    async def save_turn(
        session_id: str,
        user_content: str,
        assistant_content: str,
        user_metadata: Optional[Dict] = None,
        assistant_metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Save both user and assistant messages atomically in one DB transaction.
        Should be called via asyncio.create_task() — does not block stream finalization.

        Args:
            session_id: Session ID
            user_content: User message text
            assistant_content: Assistant message text
            user_metadata: Optional metadata for user message
            assistant_metadata: Optional metadata for assistant message

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.repositories.conversation_repository import ConversationRepository
            from app.core.database import get_db
            from app.core.redis_client import get_redis

            db_gen = get_db()
            db = await anext(db_gen)
            redis = await get_redis()

            try:
                conversation_repo = ConversationRepository(db=db, redis=redis)
                # Save both messages in a single batch call (atomic DB write)
                messages = [
                    {"role": "user", "content": user_content, "message_metadata": user_metadata},
                    {"role": "assistant", "content": assistant_content, "message_metadata": assistant_metadata},
                ]
                success = await conversation_repo.save_messages_batch(session_id=session_id, messages=messages)
                if not success:
                    logger.error(f"[ChatHistoryManager] save_messages_batch failed for session {session_id}")
                    return False

                # Invalidate cache once after both saves
                await ChatHistoryManager.invalidate_cache(session_id)

                # Mark session as having history (lightweight key, 24h TTL)
                if redis_client is not None:
                    try:
                        await redis_client.set(f"session:{session_id}:has_history", "1", ex=86400)
                    except Exception as e:
                        logger.warning(f"[ChatHistoryManager] Failed to set has_history marker: {e}")

                logger.info(f"[ChatHistoryManager] Saved turn (user+assistant) for session {session_id}")
                return True
            finally:
                await db_gen.aclose()
        except Exception as e:
            logger.error(f"[ChatHistoryManager] Error saving turn: {e}", exc_info=True)
            return False

    @staticmethod
    async def save_user_message(
        session_id: str,
        content: str,
        message_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save a user message to the database and invalidate cache.

        Args:
            session_id: Session ID
            content: User message content
            message_metadata: Optional metadata dict (e.g., {is_suggestion_click: True})

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.repositories.conversation_repository import ConversationRepository
            from app.core.database import get_db
            from app.core.redis_client import get_redis

            db_gen = get_db()
            db = await anext(db_gen)
            redis = await get_redis()

            try:
                conversation_repo = ConversationRepository(db=db, redis=redis)
                success = await conversation_repo.save_message(
                    session_id=session_id,
                    role="user",
                    content=content,
                    message_metadata=message_metadata
                )

                if success:
                    logger.info(f"[ChatHistoryManager] 💾 Saved user message to database for session {session_id}")
                    # Invalidate cache to force reload on next request
                    await ChatHistoryManager.invalidate_cache(session_id)
                    return True
                else:
                    logger.error(f"[ChatHistoryManager] ❌ Failed to save user message for session {session_id}")
                    return False
            finally:
                await db_gen.aclose()
        except Exception as e:
            logger.error(f"[ChatHistoryManager] ❌ Error saving user message: {e}", exc_info=True)
            return False

    @staticmethod
    async def save_assistant_message(
        session_id: str,
        content: str,
        message_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save an assistant message to the database and invalidate cache.

        Args:
            session_id: Session ID
            content: Assistant message content (plain text)
            message_metadata: Optional metadata dict containing ALL message data
                             (followups, ui_blocks, next_suggestions, citations, intent, status, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            from app.repositories.conversation_repository import ConversationRepository
            from app.core.database import get_db
            from app.core.redis_client import get_redis

            db_gen = get_db()
            db = await anext(db_gen)
            redis = await get_redis()

            try:
                conversation_repo = ConversationRepository(db=db, redis=redis)
                success = await conversation_repo.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=content,
                    message_metadata=message_metadata
                )

                if success:
                    logger.info(f"[ChatHistoryManager] 💾 Saved assistant message to database for session {session_id}")
                    # Invalidate cache to force reload on next request
                    await ChatHistoryManager.invalidate_cache(session_id)
                    return True
                else:
                    logger.error(f"[ChatHistoryManager] ❌ Failed to save assistant message for session {session_id}")
                    return False
            finally:
                await db_gen.aclose()
        except Exception as e:
            logger.error(f"[ChatHistoryManager] ❌ Error saving assistant message: {e}", exc_info=True)
            return False


# Singleton instance
chat_history_manager = ChatHistoryManager()
