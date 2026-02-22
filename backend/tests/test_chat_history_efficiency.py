"""Tests for RFC §1.7 — Redis and DB Access Efficiency"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.chat_history_manager import ChatHistoryManager


class TestNewSessionFastPath:
    """New sessions should skip DB load when Redis marker is absent."""

    @pytest.mark.asyncio
    async def test_new_session_skips_db_when_redis_has_no_marker(self):
        """When has_history key is absent in Redis, return [] without DB call."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0  # Key does not exist
        mock_redis.get.return_value = None  # No cache hit

        with patch('app.services.chat_history_manager.redis_client', mock_redis):
            with patch('app.core.database.get_db') as mock_get_db:
                result = await ChatHistoryManager.get_history("new-session-123")

        assert result == []
        # DB should NOT have been queried — get_db should not have been called
        mock_get_db.assert_not_called()

    @pytest.mark.asyncio
    async def test_existing_session_hits_db_when_marker_present(self):
        """When has_history key is present, fast-path is bypassed and DB is queried."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1  # Marker present — fast-path must NOT fire
        mock_redis.get.return_value = None  # No Redis cache hit

        mock_history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        mock_repo = AsyncMock()
        mock_repo.get_history.return_value = mock_history

        async def mock_db_gen():
            yield AsyncMock()

        with patch('app.services.chat_history_manager.redis_client', mock_redis):
            with patch('app.core.database.get_db', return_value=mock_db_gen()):
                with patch('app.core.redis_client.get_redis', return_value=AsyncMock()):
                    with patch('app.repositories.conversation_repository.ConversationRepository', return_value=mock_repo):
                        result = await ChatHistoryManager.get_history("existing-session")

        # Repository must have been called to load history
        mock_repo.get_history.assert_called_once()
        assert result == mock_history


class TestSaveTurnMethod:
    """save_turn() should save both messages atomically and set the has_history marker."""

    @pytest.mark.asyncio
    async def test_save_turn_sets_has_history_marker(self):
        """After saving a turn, the has_history marker should be set with 24h TTL."""
        mock_redis = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.save_messages_batch.return_value = True

        async def mock_db_gen():
            yield AsyncMock()

        with patch('app.services.chat_history_manager.redis_client', mock_redis):
            with patch('app.core.database.get_db', return_value=mock_db_gen()):
                with patch('app.core.redis_client.get_redis', return_value=AsyncMock()):
                    with patch('app.repositories.conversation_repository.ConversationRepository', return_value=mock_repo):
                        result = await ChatHistoryManager.save_turn(
                            session_id="test-session",
                            user_content="hello",
                            assistant_content="hi there",
                        )

        assert result is True
        # Check that has_history marker was set with 24h TTL
        mock_redis.set.assert_called_with("session:test-session:has_history", "1", ex=86400)

    @pytest.mark.asyncio
    async def test_save_turn_uses_batch_with_both_roles(self):
        """save_turn() should call save_messages_batch with user+assistant (atomic DB write)."""
        mock_redis = AsyncMock()
        mock_repo = AsyncMock()
        mock_repo.save_messages_batch.return_value = True

        async def mock_db_gen():
            yield AsyncMock()

        with patch('app.services.chat_history_manager.redis_client', mock_redis):
            with patch('app.core.database.get_db', return_value=mock_db_gen()):
                with patch('app.core.redis_client.get_redis', return_value=AsyncMock()):
                    with patch('app.repositories.conversation_repository.ConversationRepository', return_value=mock_repo):
                        await ChatHistoryManager.save_turn(
                            session_id="test-session",
                            user_content="hello",
                            assistant_content="hi there",
                        )

        # Must use batch (one atomic call) not individual save_message calls
        mock_repo.save_messages_batch.assert_called_once()
        batch_args = mock_repo.save_messages_batch.call_args
        messages = batch_args.kwargs.get("messages") or batch_args.args[1]
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "hi there"
