from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import settings
from src.database.models import Base


def create_engine():
    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    db_url = settings.database_url
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite+aiosqlite:///./", "")
        full_path = data_dir / db_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite+aiosqlite:///{full_path}"

    engine = create_async_engine(
        db_url,
        echo=settings.log_level == "DEBUG",
        poolclass=NullPool if "sqlite" in db_url else None,
    )
    return engine


engine = create_engine()
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
