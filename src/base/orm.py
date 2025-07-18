"""Модуль для работы с базой данных."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовая модель для всех ORM классов."""

    pass


def get_session_factory(database_url: str) -> async_sessionmaker:
    """Создание фабрики сессий для асинхронной работы с БД."""
    engine = create_async_engine(database_url, echo=False)
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def create_database_tables():
    """Создание таблиц базы данных (синхронная версия для обратной совместимости)."""
    import asyncio
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        asyncio.run(create_database_tables_async())
    except Exception as e:
        logger.error(f"Could not create database tables: {e}")


async def create_database_tables_async():
    """Создание таблиц базы данных (асинхронная версия)."""
    import logging
    from base.config import get_postgres_url
    
    logger = logging.getLogger(__name__)
    
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from users.adapters.orm import UserORM
        from products.adapters.orm import ProductORM, PricePredictionORM, TaskORM
        
        logger.info("Creating database tables...")
        engine = create_async_engine(get_postgres_url())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Could not create database tables: {e}")
        raise
