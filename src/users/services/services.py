"""Сервисы для работы с пользователями."""

import hashlib
from typing import Optional

from users.domain.models import User, UserCredentials
from .unit_of_work import IUserUnitOfWork


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, uow: IUserUnitOfWork) -> None:
        """Инициализация сервиса."""
        self.uow = uow

    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        async with self.uow:
            await self.uow.users.add_user(user)
            await self.uow.commit()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        async with self.uow:
            return await self.uow.users.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        async with self.uow:
            return await self.uow.users.get_user_by_id(user_id)

    async def verify_credentials(
        self, email: str, password: str
    ) -> Optional[User]:
        """Проверка учетных данных пользователя."""
        async with self.uow:
            user = await self.uow.users.get_user_by_email(email)
            if user:
                # Простая проверка пароля (в реальности нужно использовать bcrypt)
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash == user.password:
                    return user
            return None
