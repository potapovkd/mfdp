"""Репозитории для работы с пользователями."""

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .orm import UserORM
from users.domain.models import User, UserCredentials


class IUserRepository:
    """Интерфейс репозитория пользователей."""

    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        raise NotImplementedError

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        raise NotImplementedError

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        raise NotImplementedError


class InMemoryUserRepository(IUserRepository):
    """In-memory репозиторий пользователей."""

    def __init__(self) -> None:
        """Инициализация репозитория."""
        self.users: dict[int, User] = {}
        self.users_by_email: dict[str, User] = {}
        self.next_id = 1

    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        user_id = self.next_id
        self.next_id += 1

        new_user = User(
            id=user_id,
            email=user.email,
            password=user.password,
            created_at=datetime.utcnow(),
        )

        self.users[user_id] = new_user
        self.users_by_email[user.email] = new_user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        return self.users_by_email.get(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        return self.users.get(user_id)


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL репозиторий пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория."""
        self.session = session

    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        password_hash = hashlib.sha256(user.password.encode()).hexdigest()
        user_orm = UserORM(
            email=user.email,
            # Используем часть email как username
            username=user.email.split("@")[0],
            password_hash=password_hash,
        )
        self.session.add(user_orm)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        result = await self.session.execute(
            select(UserORM).filter_by(email=email)
        )
        user_orm = result.scalars().first()

        if user_orm:
            return User(
                id=user_orm.id,
                email=user_orm.email,
                password=user_orm.password_hash,  # Возвращаем хеш пароля для проверки
                created_at=user_orm.created_at,
            )
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        result = await self.session.execute(
            select(UserORM).filter_by(id=user_id)
        )
        user_orm = result.scalars().first()

        if user_orm:
            return User(
                id=user_orm.id,
                email=user_orm.email,
                password=user_orm.password_hash,  # Возвращаем хеш пароля для проверки
                created_at=user_orm.created_at,
            )
        return None
