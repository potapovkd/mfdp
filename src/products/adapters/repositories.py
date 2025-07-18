"""Репозитории для работы с товарами и задачами."""

from abc import ABC, abstractmethod


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from base.exceptions import DoesntExistException
from .orm import ProductORM
from products.domain.models import Product, ProductData


class ProductAbstractDatabaseRepository(ABC):
    """Абстракция репозитория для товаров."""

    @abstractmethod
    async def get(self, product_id: int) -> Product:
        """Получение товара по ID."""

    @abstractmethod
    async def add(self, user_id: int, product_data: ProductData) -> Product:
        """Добавление товара."""

    @abstractmethod
    async def delete(self, product_id: int, user_id: int) -> None:
        """Удаление товара."""

    @abstractmethod
    async def get_user_products(self, user_id: int) -> list[Product]:
        """Получение товаров пользователя."""


class ProductSqlAlchemyDatabaseRepository(ProductAbstractDatabaseRepository):
    """Репозиторий SQLAlchemy для товаров."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, product_id: int) -> Product:
        """Получение товара по ID."""
        stmt = select(ProductORM).filter_by(id=product_id)
        result = await self.session.execute(stmt)
        product_orm = result.scalar_one_or_none()

        if not product_orm:
            raise DoesntExistException("Product not found")

        return Product(
            id=product_orm.id,
            user_id=product_orm.user_id,
            name=product_orm.name,
            category_name=product_orm.category_name,
            brand_name=product_orm.brand_name,
            item_description=product_orm.item_description,
            item_condition_id=product_orm.item_condition_id,
            shipping=product_orm.shipping,
            created_at=product_orm.created_at
        )

    async def add(self, user_id: int, product_data: ProductData) -> Product:
        """Добавление товара."""
        product_orm = ProductORM(
            user_id=user_id,
            name=product_data.name,  # Храним имя в type
            category_name=product_data.category_name,
            brand_name=product_data.brand_name,
            item_description=product_data.item_description,
            item_condition_id=product_data.item_condition_id,
            shipping=product_data.shipping,
        )

        self.session.add(product_orm)
        await self.session.flush()

        return Product(
            id=product_orm.id,
            user_id=user_id,
            name=product_data.name,
            category_name=product_data.category_name,
            brand_name=product_data.brand_name,
            item_description=product_data.item_description,
            item_condition_id=product_data.item_condition_id,
            shipping=product_data.shipping,
            created_at=product_orm.created_at
        )

    async def delete(self, product_id: int, user_id: int) -> None:
        """Удаление товара."""
        stmt = select(ProductORM).filter_by(id=product_id, user_id=user_id)
        result = await self.session.execute(stmt)
        product_orm = result.scalar_one_or_none()

        if not product_orm:
            raise DoesntExistException("Product not found")

        await self.session.delete(product_orm)

    async def get_user_products(self, user_id: int) -> list[Product]:
        """Получение товаров пользователя."""
        stmt = select(ProductORM).filter_by(user_id=user_id)
        result = await self.session.execute(stmt)
        products_orm = result.scalars().all()

        return [
            Product(
                id=p.id,
                user_id=p.user_id,
                name=p.name,
                category_name=p.category_name,
                brand_name=p.brand_name,
                item_description=p.item_description,
                item_condition_id=p.item_condition_id,
                shipping=p.shipping,
                created_at=p.created_at
            )
            for p in products_orm
        ]


# All deprecated repository classes removed after migration
