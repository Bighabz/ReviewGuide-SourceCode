"""
Database Connection with Connection Pooling
Async SQLAlchemy setup for PostgreSQL
"""
import sqlalchemy
from app.core.centralized_logger import get_logger
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = get_logger(__name__)

# Create declarative base for models
Base = declarative_base()

# Global engine and session maker
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """Initialize database connection with connection pooling"""
    global engine, AsyncSessionLocal

    try:
        # Create async engine with connection pooling
        # Note: For async engines, SQLAlchemy automatically uses AsyncAdaptedQueuePool
        # We don't specify poolclass explicitly for asyncio compatibility
        # Determine connect_args based on driver (asyncpg vs aiosqlite)
        connect_args = {}
        if "asyncpg" in settings.DATABASE_URL:
            connect_args = {"command_timeout": settings.DB_CONNECT_TIMEOUT}
        elif "aiosqlite" in settings.DATABASE_URL:
            connect_args = {"timeout": settings.DB_CONNECT_TIMEOUT}

        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,  # Disable SQL query logging
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after configured time
            connect_args=connect_args
        )

        # Create session maker
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Test connection
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))

        logger.info("Database connection initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections"""
    global engine

    if engine:
        await engine.dispose()
        logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
