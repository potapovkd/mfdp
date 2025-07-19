"""Интерфейсы репозиториев для работы с пользователями."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from users.domain.models import User, UserCredentials


class IUserRepository(ABC):
    """Интерфейс репозитория пользователей."""

    @abstractmethod
    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        raise NotImplementedError

    @abstractmethod
    async def update_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """Обновление баланса пользователя."""
        raise NotImplementedError
