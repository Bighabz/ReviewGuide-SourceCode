"""
Conversation Repository
Implements dual-write pattern: PostgreSQL (persistent) + Redis (cache)
Provides fallback mechanism for resilience
"""
import json
from app.core.centralized_logger import get_logger
from typing import List, Dict, Optional
from datetime import datetime
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert

from app.models.conversation_message import ConversationMessage
from app.core.config import settings

logger = get_logger(__name__)


class ConversationRepository:
    """
    Repository for managing conversation history with dual-write pattern

    Strategy:
    - Write: Save to both PostgreSQL (persistent) and Redis (cache)
    - Read: Configurable via USE_REDIS_FOR_HISTORY:
      * True: Try Redis first (fast), fallback to PostgreSQL if miss
      * False: Load directly from PostgreSQL (skip Redis)
    - Redis TTL: 24 hours (configurable)
    """

    REDIS_KEY_PREFIX = "conversation_history"
    REDIS_TTL_SECONDS = 86400  # 24 hours
    MAX_HISTORY_LIMIT = 100  # Maximum messages to retrieve

    def __init__(self, db: AsyncSession, redis: Redis):
        """
        Initialize repository with database and Redis connections

        Args:
            db: SQLAlchemy async session
            redis: Redis async client
        """
        self.db = db
        self.redis = redis

    async def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history with configurable Redis cache

        Args:
            session_id: Database session ID (UUID string)
            limit: Maximum number of messages to retrieve (default: MAX_HISTORY_LIMIT)

        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        if limit is None:
            limit = self.MAX_HISTORY_LIMIT

        try:
            # Check config: Use Redis cache or load directly from PostgreSQL?
            if settings.USE_REDIS_FOR_HISTORY:
                # Redis-first strategy: Try cache, fallback to DB
                redis_history = await self._get_from_redis(session_id, limit)

                if redis_history:
                    logger.debug(f"Cache HIT: Loaded {len(redis_history)} messages from Redis for session {session_id}")
                    return redis_history

                # Cache miss - fallback to PostgreSQL
                logger.debug(f"Cache MISS: Falling back to PostgreSQL for session {session_id}")
                db_history = await self._get_from_postgres(session_id, limit)

                if db_history:
                    # Warm the cache for future requests
                    await self._set_redis_cache(session_id, db_history)
                    logger.debug(f"Cache WARMED: Loaded {len(db_history)} messages from PostgreSQL and cached")

                return db_history
            else:
                # Direct PostgreSQL strategy: Skip Redis entirely
                logger.debug(f"Redis cache disabled, loading directly from PostgreSQL for session {session_id}")
                db_history = await self._get_from_postgres(session_id, limit)
                logger.debug(f"Loaded {len(db_history)} messages directly from PostgreSQL (cache bypassed)")
                return db_history

        except Exception as e:
            logger.error(f"Failed to get conversation history for session {session_id}: {e}", exc_info=True)
            # Return empty list on error to prevent cascade failures
            return []

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save a single message with dual-write to PostgreSQL + Redis (configurable)

        Args:
            session_id: Database session ID (UUID string)
            role: Message role ('user' or 'assistant')
            content: Message content (plain text)
            message_metadata: Optional metadata dict containing ALL message data
                             (followups, ui_blocks, next_suggestions, is_suggestion_click, citations, intent, status, etc.)

        Returns:
            True if successfully saved to at least one store, False otherwise
        """
        postgres_success = False
        redis_success = False

        try:
            # Step 1: Always save to PostgreSQL (persistent storage - source of truth)
            postgres_success = await self._save_to_postgres(
                session_id, role, content, message_metadata
            )

            # Step 2: Conditionally save to Redis cache (only if enabled)
            if settings.USE_REDIS_FOR_HISTORY:
                redis_success = await self._append_to_redis(
                    session_id, role, content, message_metadata
                )

                if postgres_success and redis_success:
                    logger.debug(f"Dual-write SUCCESS: Saved {role} message for session {session_id}")
                    return True
                elif postgres_success:
                    logger.warning(f"Partial write: PostgreSQL OK, Redis FAILED for session {session_id}")
                    return True  # Still consider success if persistent storage worked
                elif redis_success:
                    logger.error(f"CRITICAL: Redis OK but PostgreSQL FAILED for session {session_id}")
                    return False  # Fail if persistent storage failed
                else:
                    logger.error(f"Dual-write FAILED: Both stores failed for session {session_id}")
                    return False
            else:
                # Redis disabled - PostgreSQL only
                if postgres_success:
                    logger.debug(f"PostgreSQL-only write SUCCESS: Saved {role} message for session {session_id}")
                    return True
                else:
                    logger.error(f"PostgreSQL write FAILED for session {session_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to save message for session {session_id}: {e}", exc_info=True)
            return False

    async def save_messages_batch(self, session_id: str, messages: List[Dict]) -> bool:
        """
        Save multiple messages in batch (useful for initialization)

        Args:
            session_id: Database session ID (UUID string)
            messages: List of dicts with 'role' and 'content' keys

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save to PostgreSQL in batch (always)
            postgres_success = await self._save_batch_to_postgres(session_id, messages)

            # Save to Redis (only if enabled)
            if settings.USE_REDIS_FOR_HISTORY:
                redis_success = await self._set_redis_cache(session_id, messages)

                if postgres_success and redis_success:
                    logger.info(f"Batch save SUCCESS: {len(messages)} messages for session {session_id}")
                    return True
                elif postgres_success:
                    logger.warning(f"Batch partial: PostgreSQL OK, Redis FAILED for session {session_id}")
                    return True
                else:
                    logger.error(f"Batch save FAILED for session {session_id}")
                    return False
            else:
                # Redis disabled - PostgreSQL only
                if postgres_success:
                    logger.info(f"Batch save SUCCESS (PostgreSQL-only): {len(messages)} messages for session {session_id}")
                    return True
                else:
                    logger.error(f"Batch save FAILED for session {session_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to save batch messages for session {session_id}: {e}", exc_info=True)
            return False

    async def delete_history(self, session_id: str) -> bool:
        """
        Delete all conversation history for a session

        Args:
            session_id: Database session ID (UUID string)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from Redis
            redis_key = self._get_redis_key(session_id)
            await self.redis.delete(redis_key)

            # Delete from PostgreSQL (cascade delete via foreign key)
            # Note: Messages will be deleted when session is deleted
            # Or we can explicitly delete:
            from sqlalchemy import delete as sql_delete
            stmt = sql_delete(ConversationMessage).where(
                ConversationMessage.session_id == session_id
            )
            await self.db.execute(stmt)
            await self.db.commit()

            logger.info(f"Deleted conversation history for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete history for session {session_id}: {e}", exc_info=True)
            return False

    # ==================== PRIVATE METHODS ====================

    def _get_redis_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.REDIS_KEY_PREFIX}:{session_id}"

    async def _get_from_redis(self, session_id: str, limit: int) -> List[Dict]:
        """
        Get messages from Redis cache

        Returns empty list if cache miss or error
        """
        try:
            redis_key = self._get_redis_key(session_id)

            # Get last N messages (Redis LRANGE with negative indices)
            messages_json = await self.redis.lrange(redis_key, -limit, -1)

            if not messages_json:
                return []

            # Parse JSON messages
            messages = []
            for msg_json in messages_json:
                try:
                    msg = json.loads(msg_json)
                    messages.append(msg)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse Redis message: {e}")
                    continue

            return messages

        except Exception as e:
            logger.warning(f"Redis get error for session {session_id}: {e}")
            return []

    async def _get_from_postgres(self, session_id: str, limit: int) -> List[Dict]:
        """
        Get messages from PostgreSQL

        Returns empty list if no messages or error
        """
        try:
            # Query messages ordered by sequence number
            stmt = (
                select(ConversationMessage)
                .where(ConversationMessage.session_id == session_id)
                .order_by(ConversationMessage.sequence_number)
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            messages = result.scalars().all()

            return [msg.to_dict() for msg in messages]

        except Exception as e:
            logger.error(f"PostgreSQL get error for session {session_id}: {e}", exc_info=True)
            return []

    async def _save_to_postgres(
        self,
        session_id: str,
        role: str,
        content: str,
        message_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save single message to PostgreSQL with auto-incrementing sequence

        Args:
            session_id: Database session ID (UUID string)
            role: Message role ('user' or 'assistant')
            content: Plain text content
            message_metadata: Optional metadata dict with all message data

        Returns True if successful, False otherwise
        """
        try:
            # Get current max sequence number for this session
            stmt = select(ConversationMessage.sequence_number).where(
                ConversationMessage.session_id == session_id
            ).order_by(desc(ConversationMessage.sequence_number)).limit(1)

            result = await self.db.execute(stmt)
            max_seq = result.scalar()
            next_seq = (max_seq or 0) + 1

            # Create new message with metadata
            message = ConversationMessage(
                session_id=session_id,
                role=role,
                content=content,
                message_metadata=message_metadata,
                sequence_number=next_seq
            )

            self.db.add(message)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"PostgreSQL save error for session {session_id}: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def _save_batch_to_postgres(self, session_id: str, messages: List[Dict]) -> bool:
        """
        Save multiple messages to PostgreSQL in batch

        Returns True if successful, False otherwise
        """
        try:
            # Query current max sequence number to avoid overwriting existing messages
            stmt = select(ConversationMessage.sequence_number).where(
                ConversationMessage.session_id == session_id
            ).order_by(desc(ConversationMessage.sequence_number)).limit(1)
            result = await self.db.execute(stmt)
            max_seq = result.scalar() or 0

            # Create message objects with sequence numbers continuing from max_seq
            message_objects = []
            for idx, msg in enumerate(messages):
                message_objects.append(
                    ConversationMessage(
                        session_id=session_id,
                        role=msg["role"],
                        content=msg["content"],
                        message_metadata=msg.get("message_metadata"),
                        sequence_number=max_seq + idx + 1
                    )
                )

            self.db.add_all(message_objects)
            await self.db.commit()

            return True

        except Exception as e:
            logger.error(f"PostgreSQL batch save error for session {session_id}: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def _append_to_redis(
        self,
        session_id: str,
        role: str,
        content: str,
        message_metadata: Optional[Dict] = None
    ) -> bool:
        """
        Append a single message to Redis list

        Args:
            session_id: Database session ID (UUID string)
            role: Message role ('user' or 'assistant')
            content: Plain text content
            message_metadata: Optional metadata dict with all message data

        Returns True if successful, False otherwise
        """
        try:
            redis_key = self._get_redis_key(session_id)

            message = {
                "role": role,
                "content": content
            }

            # Include metadata if provided
            if message_metadata:
                message["message_metadata"] = message_metadata

            # Append to Redis list
            await self.redis.rpush(redis_key, json.dumps(message))

            # Set expiration (refresh TTL on each append)
            await self.redis.expire(redis_key, self.REDIS_TTL_SECONDS)

            return True

        except Exception as e:
            logger.warning(f"Redis append error for session {session_id}: {e}")
            return False

    async def _set_redis_cache(self, session_id: str, messages: List[Dict]) -> bool:
        """
        Set entire conversation history in Redis (overwrites existing)

        Returns True if successful, False otherwise
        """
        try:
            redis_key = self._get_redis_key(session_id)

            # Delete existing cache
            await self.redis.delete(redis_key)

            # Add all messages
            if messages:
                messages_json = [json.dumps(msg) for msg in messages]
                await self.redis.rpush(redis_key, *messages_json)

                # Set expiration
                await self.redis.expire(redis_key, self.REDIS_TTL_SECONDS)

            return True

        except Exception as e:
            logger.warning(f"Redis cache set error for session {session_id}: {e}")
            return False
