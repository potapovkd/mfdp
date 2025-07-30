"""Зависимости для API пользователей."""

from typing import Annotated

from fastapi import Depends

from base.dependencies import get_db
from users.services.services import UserService
from users.services.unit_of_work import PostgreSQLUserUnitOfWork


async def get_user_service(db=Depends(get_db)) -> UserService:
    """Получение сервиса для работы с пользователями."""
    uow = PostgreSQLUserUnitOfWork(lambda: db)
    return UserService(uow)


UserServiceDependency = Annotated[UserService, Depends(get_user_service)] 