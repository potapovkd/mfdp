"""Unit of Work для пользователей."""

import abc

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from users.adapters.repositories import IUserRepository, PostgreSQLUserRepository


class IUserUnitOfWork(abc.ABC):
    """Интерфейс Unit of Work для пользователей."""

    users: IUserRepository

    async def __aenter__(self):
        """Вход в контекст."""
        return self

    async def __aexit__(self, *args):
        """Выход из контекста."""
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        """Фиксация изменений."""
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        """Откат изменений."""
        raise NotImplementedError


class PostgreSQLUserUnitOfWork(IUserUnitOfWork):
    """PostgreSQL Unit of Work для пользователей."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """Инициализация."""
        self.session_factory = session_factory

    async def __aenter__(self):
        """Вход в контекст."""
        self.session = self.session_factory()
        self.users = PostgreSQLUserRepository(self.session)
        return await super().__aenter__()

    async def __aexit__(self, *args):
        """Выход из контекста."""
        await super().__aexit__(*args)
        await self.session.close()

    async def commit(self):
        """Фиксация изменений."""
        await self.session.commit()

    async def rollback(self):
        """Откат изменений."""
        await self.session.rollback()
