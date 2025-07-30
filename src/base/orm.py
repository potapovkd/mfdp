"""Базовые классы и функции для работы с ORM."""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from base.config import get_settings

settings = get_settings()

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем асинхронный движок
engine = create_async_engine(
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@"
    f"{settings.db_host}:{settings.db_port}/{settings.db_name}",
    echo=False,
    future=True
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def get_session_factory():
    """Получение фабрики сессий."""
    return async_session


async def init_db():
    """Инициализация базы данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
