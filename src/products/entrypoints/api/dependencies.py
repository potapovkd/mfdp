"""Зависимости для API товаров."""

from typing import Annotated

from fastapi import Depends

from base.dependencies import get_product_uow
from products.services.services import ProductService
from products.services.unit_of_work import ProductAbstractUnitOfWork


def get_product_service(
    uow: Annotated[ProductAbstractUnitOfWork, Depends(get_product_uow)]
) -> ProductService:
    """Получение сервиса для работы с товарами."""
    return ProductService(uow)


ProductServiceDependency = Annotated[ProductService, Depends(get_product_service)]
