"""
Pytest Configuration and Fixtures
Shared fixtures for integration tests
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set test environment before importing app
os.environ["ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"
os.environ["ADMIN_PASSWORD"] = "testpassword123"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["LOG_ENABLED"] = "false"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.zadd = AsyncMock(return_value=1)
    mock.zremrangebyscore = AsyncMock(return_value=0)
    mock.zcard = AsyncMock(return_value=0)
    mock.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload"""
    return {
        "message": "What are the best wireless headphones?",
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }


@pytest.fixture
def sample_user():
    """Sample admin user for testing"""
    from app.utils.auth import hash_password
    return {
        "id": 1,
        "username": "testadmin",
        "email": "admin@test.com",
        "password_hash": hash_password("testpassword123"),
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_login": None
    }


@pytest.fixture
def auth_headers(sample_user):
    """Generate auth headers with valid JWT token"""
    from app.utils.auth import create_access_token
    token = create_access_token({
        "sub": str(sample_user["id"]),
        "username": sample_user["username"],
        "type": "admin"
    })
    return {"Authorization": f"Bearer {token}"}
