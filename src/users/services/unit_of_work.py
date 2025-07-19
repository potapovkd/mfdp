"""Unit of Work для работы с пользователями."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from users.adapters.repositories import IUserRepository
else:
    from users.adapters.repositories import IUserRepository


class IUserUnitOfWork(ABC):
    """Интерфейс Unit of Work для пользователей."""

    users: IUserRepository

    @abstractmethod
    async def commit(self) -> None:
        """Фиксация изменений."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Откат изменений."""
        raise NotImplementedError

    async def __aenter__(self):
        """Вход в контекст."""
        return self

    async def __aexit__(self, *args):
        """Выход из контекста."""
        pass


class InMemoryUserUnitOfWork(IUserUnitOfWork):
    """In-memory Unit of Work для пользователей."""

    def __init__(self):
        """Инициализация."""
        from users.adapters.repository_impl import InMemoryUserRepository
        self.users = InMemoryUserRepository()

    async def commit(self):
        """Фиксация изменений."""
        pass

    async def rollback(self):
        """Откат изменений."""
        pass


from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from users.adapters.repository_impl import PostgreSQLUserRepository


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
