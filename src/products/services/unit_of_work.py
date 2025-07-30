"""Модуль для единицы работы (Unit of Work) товаров."""

import abc

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from products.adapters.repositories import (
    ProductAbstractDatabaseRepository,
    ProductSqlAlchemyDatabaseRepository,
)


class ProductAbstractUnitOfWork(abc.ABC):
    """Абстракция над атомарной операцией (единицей работы)."""

    @property
    @abc.abstractmethod
    def products(self) -> ProductAbstractDatabaseRepository:
        """Репозиторий для работы с товарами."""

    async def __aenter__(self) -> "ProductAbstractUnitOfWork":
        """Инициализация UoW через менеджер контекста."""
        return self

    async def __aexit__(self, *args):
        """Откат транзакции из-за исключения."""
        await self.rollback()

    @abc.abstractmethod
    async def commit(self):
        """Фиксация транзакции."""

    @abc.abstractmethod
    async def rollback(self):
        """Откат транзакции."""


class PostgreSQLProductUnitOfWork(ProductAbstractUnitOfWork):
    """UoW для PostgreSQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    @property
    def products(self) -> ProductAbstractDatabaseRepository:
        return ProductSqlAlchemyDatabaseRepository(self._session)

    async def __aenter__(self) -> "PostgreSQLProductUnitOfWork":
        """Инициализация UoW через менеджер контекста."""
        self._session: AsyncSession = self.session_factory()
        return self

    async def __aexit__(self, *args) -> None:
        """Откат транзакции в случае исключения."""
        await super().__aexit__(*args)
        await self._session.close()

    async def commit(self) -> None:
        """Фиксация транзакции."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Откат транзакции."""
        await self._session.rollback()


# Alias for backward compatibility
ProductSqlAlchemyUnitOfWork = PostgreSQLProductUnitOfWork
