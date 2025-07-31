"""Зависимости для API продуктов."""

from typing import Annotated

from fastapi import Depends

from base.dependencies import get_db
from products.services.services import ProductService
from products.services.unit_of_work import PostgreSQLProductUnitOfWork


async def get_product_service(db=Depends(get_db)) -> ProductService:
    """Получение сервиса для работы с товарами."""
    uow = PostgreSQLProductUnitOfWork(lambda: db)
    return ProductService(uow)


ProductServiceDependency = Annotated[ProductService, Depends(get_product_service)]
