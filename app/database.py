from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
from loguru import logger


def _build_engine():
    url = settings.database_url
    is_sqlite = url.startswith("sqlite")

    # Ensure async scheme:
    #   postgresql://  -> postgresql+asyncpg://
    #   sqlite:///     -> sqlite+aiosqlite:///
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite:///") and "+" not in url:
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    kwargs = dict(echo=settings.debug)
    if not is_sqlite:
        # pool_size / max_overflow are not supported by aiosqlite
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
        kwargs["pool_pre_ping"] = True

    return create_async_engine(url, **kwargs)


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"DB session error: {e}")
            raise
        finally:
            await session.close()
