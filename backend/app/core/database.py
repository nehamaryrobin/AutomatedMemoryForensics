from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Async engine for FastAPI route handlers
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Synchronous engine for background analysis tasks
sync_engine = create_engine(
    settings.SYNC_SQLALCHEMY_DATABASE_URI,
    echo=False,
    connect_args={"check_same_thread": False}
)

SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
