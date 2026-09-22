from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    # Railway injects postgresql:// — asyncpg needs postgresql+asyncpg://
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("://", "+asyncpg://", 1)
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        echo=settings.environment == "development",
    )


engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
