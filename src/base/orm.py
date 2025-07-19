"""ORM конфигурация и базовые модели."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from base.config import get_db_url


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""


# Создаем движок базы данных
engine = create_async_engine(get_db_url(), echo=False)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_session_factory():
    """Получение фабрики сессий."""
    return async_session_maker


async def create_database_tables():
    """Создание таблиц базы данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_database_tables_async():
    """Асинхронное создание таблиц базы данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
