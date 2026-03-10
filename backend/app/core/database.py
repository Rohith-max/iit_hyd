import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    _connect_args = {}
    _engine_kwargs = {"echo": False}
    if settings.DATABASE_URL.startswith("sqlite"):
        _connect_args = {"check_same_thread": False}
    else:
        _engine_kwargs.update({"pool_size": 20, "max_overflow": 10})
    engine = create_async_engine(settings.DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except Exception as e:
    logger.warning(f"Database engine creation failed (running without DB): {e}")
    engine = None
    AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    if engine is None:
        logger.warning("Skipping DB init — no engine available")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
