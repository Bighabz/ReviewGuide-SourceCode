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


@pytest.fixture(autouse=True, scope="session")
def mock_app_startup():
    """
    Patch all lifespan startup/shutdown I/O so tests can use TestClient/AsyncClient
    without needing real PostgreSQL or Redis connections.

    Also patches the global redis_client and AsyncSessionLocal module-level variables
    so that get_redis() and get_db() work without real connections.
    """
    # Build a mock Redis client that passes basic checks
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=True)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.zadd = AsyncMock(return_value=1)
    mock_redis.zremrangebyscore = AsyncMock(return_value=0)
    mock_redis.zcard = AsyncMock(return_value=0)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.zrange = AsyncMock(return_value=[])

    # Build a mock DB session that FastAPI's get_db async generator can yield
    mock_session = MagicMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(
                return_value=MagicMock(first=MagicMock(return_value=None))
            )
        )
    )
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    # async_sessionmaker must be callable and return an async context manager
    mock_session_local = MagicMock(return_value=mock_session)

    with patch("app.main.init_db", new_callable=AsyncMock), \
         patch("app.main.close_db", new_callable=AsyncMock), \
         patch("app.main.init_redis", new_callable=AsyncMock), \
         patch("app.main.close_redis", new_callable=AsyncMock), \
         patch("app.main.load_config_overrides_from_db", new_callable=AsyncMock), \
         patch("app.main.setup_search_provider"), \
         patch("app.main.setup_travel_providers"), \
         patch("app.main.build_startup_manifest", return_value={}), \
         patch("app.main.log_startup_manifest"), \
         patch("app.main.set_manifest"), \
         patch("app.main.start_scheduler"), \
         patch("app.main.stop_scheduler"), \
         patch("app.core.redis_client.redis_client", mock_redis), \
         patch("app.core.database.AsyncSessionLocal", mock_session_local):
        yield


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
