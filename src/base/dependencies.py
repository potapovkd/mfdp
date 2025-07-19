"""Зависимости для FastAPI приложения."""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from base.config import get_settings
from base.orm import get_session_factory
from base.utils import JWTHandler
from base.data_structures import JWTPayloadDTO
from products.services.services import ProductService
from products.services.unit_of_work import PostgreSQLProductUnitOfWork
from users.services.services import UserService
from users.services.unit_of_work import PostgreSQLUserUnitOfWork

security = HTTPBearer()

settings = get_settings()


def get_token_from_header(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> JWTPayloadDTO:
    """Получение и валидация JWT токена из заголовка."""
    logger = logging.getLogger(__name__)
    try:
        token = credentials.credentials
        logger.info(f"Attempting to decode token: {token[:20]}...")
        jwt_handler = JWTHandler(settings.secret_key)
        payload = jwt_handler.decode_token(token)
        logger.info(f"Token decoded successfully for user ID: {payload.id}")
        return payload
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_service() -> UserService:
    """Получение сервиса пользователей."""
    session_factory = get_session_factory()
    uow = PostgreSQLUserUnitOfWork(session_factory)
    return UserService(uow)


def get_product_service() -> ProductService:
    """Получение сервиса товаров."""
    session_factory = get_session_factory()
    uow = PostgreSQLProductUnitOfWork(session_factory)
    return ProductService(uow)


def get_product_uow() -> PostgreSQLProductUnitOfWork:
    """Получение Unit of Work для товаров."""
    session_factory = get_session_factory()
    return PostgreSQLProductUnitOfWork(session_factory)


# Типы для внедрения зависимостей
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
ProductServiceDependency = Annotated[ProductService, Depends(get_product_service)]
