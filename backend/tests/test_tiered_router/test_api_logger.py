# backend/tests/test_tiered_router/test_api_logger.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.tiered_router.api_logger import log_api_usage, log_consent_event


@pytest.fixture
def mock_db_session():
    """Create a mock async database session context manager."""
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    # Create async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_session
    mock_context_manager.__aexit__.return_value = None

    return mock_context_manager, mock_session


@pytest.mark.asyncio
async def test_log_api_usage_creates_record(mock_db_session):
    """log_api_usage should create a database record"""
    mock_context_manager, mock_session = mock_db_session

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_context_manager):
        await log_api_usage(
            user_id="test-user-id",
            session_id="test-session",
            api_name="amazon_affiliate",
            tier=1,
            cost_cents=0,
            latency_ms=234,
            success=True,
        )

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_api_usage_handles_error(mock_db_session):
    """log_api_usage should log error field on failure"""
    mock_context_manager, mock_session = mock_db_session

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_context_manager):
        await log_api_usage(
            user_id="test-user-id",
            session_id="test-session",
            api_name="bestbuy_affiliate",
            tier=1,
            cost_cents=0,
            latency_ms=5000,
            success=False,
            error="timeout",
        )

    call_args = mock_session.add.call_args[0][0]
    assert call_args.success is False
    assert call_args.error == "timeout"


@pytest.mark.asyncio
async def test_log_consent_event(mock_db_session):
    """log_consent_event should create a consent record"""
    mock_context_manager, mock_session = mock_db_session

    with patch("app.services.tiered_router.api_logger.AsyncSessionLocal", return_value=mock_context_manager):
        await log_consent_event(
            user_id="test-user-id",
            session_id="test-session",
            consent_type="per_query",
            tier_requested=3,
        )

    mock_session.add.assert_called_once()
