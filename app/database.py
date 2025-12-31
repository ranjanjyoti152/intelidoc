"""
InteliDoc RAG Pipeline - Database Connection and Session Management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.config import get_settings


settings = get_settings()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async def init_db():
    """Initialize database and verify pgvector extension."""
    async with engine.begin() as conn:
        # Verify pgvector extension is available
        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        if not result.fetchone():
            raise RuntimeError("pgvector extension is not installed in the database")
        
        # Create tables if they don't exist (handled by init.sql, but just in case)
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()


@asynccontextmanager
async def get_db_session():
    """Get database session context manager."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db():
    """Dependency for FastAPI routes."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
