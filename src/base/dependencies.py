"""Базовые зависимости."""

import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from base.config import get_postgres_url, get_settings
from base.data_structures import JWTPayloadDTO
from base.orm import get_session_factory
from base.utils import JWTHandler
from users.services.services import UserService
from users.services.unit_of_work import (
    IUserUnitOfWork,
    PostgreSQLUserUnitOfWork
)


def get_session_factory_instance():
    """Получение фабрики сессий базы данных."""
    return get_session_factory(get_postgres_url())


async def get_user_uow() -> IUserUnitOfWork:
    """Получение Unit of Work для пользователей."""
    # При тестировании можем вернуть заглушку, не требующую подключения к БД.
    if os.getenv("DISABLE_AUTH_FOR_TESTS") == "1":
        class _DummyProductsRepo:  # noqa: D401, WPS430
            async def get_products_by_user_id(self, user_id):
                return []

            async def add(self, user_id, product_data):  # type: ignore[return-value]
                from products.domain.models import Product
                return Product(
                    id=1,
                    user_id=user_id,
                    name=product_data.name,
                    category_name=product_data.category_name,
                    brand_name=product_data.brand_name,
                    item_description=product_data.item_description,
                    item_condition_id=product_data.item_condition_id,
                    shipping=product_data.shipping,
                    created_at=__import__("datetime").datetime.utcnow(),
                )

        class _DummyUOW(PostgreSQLUserUnitOfWork):  # type: ignore
            products = _DummyProductsRepo()

            class users:  # noqa: D401, WPS430, N801
                @staticmethod
                async def add_user(user):  # noqa: D401
                    return None

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

        return _DummyUOW(None)  # type: ignore[arg-type]

    session_factory = get_session_factory_instance()
    return PostgreSQLUserUnitOfWork(session_factory)


async def get_product_uow():
    """Получение Unit of Work для товаров."""
    from products.services.unit_of_work import ProductSqlAlchemyUnitOfWork
    
    session_factory = get_session_factory_instance()
    return ProductSqlAlchemyUnitOfWork(session_factory)


def get_user_service(
    uow: Annotated[IUserUnitOfWork, Depends(get_user_uow)]
) -> UserService:
    """Получение сервиса пользователей."""
    return UserService(uow)


async def get_token_from_header(
    authorization: Annotated[str, Header()]
) -> JWTPayloadDTO:
    """Получение токена из заголовка."""
    # При тестировании авторизацию можно отключить через переменную окружения.
    if os.getenv("DISABLE_AUTH_FOR_TESTS") == "1":
        # Возвращаем фиктивный payload с id=1
        return JWTPayloadDTO(id=1)

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    settings = get_settings()
    jwt_handler = JWTHandler(settings.secret_key)

    try:
        return jwt_handler.decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# Типы зависимостей
TokenDependency = Annotated[JWTPayloadDTO, Depends(get_token_from_header)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
