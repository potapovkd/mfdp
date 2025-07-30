"""Реализации репозиториев для работы с пользователями."""

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from users.adapters.orm import UserORM
from users.domain.models import User, UserCredentials

from .repositories import IUserRepository


class InMemoryUserRepository(IUserRepository):
    """In-memory репозиторий пользователей для тестов."""

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
            created_at=datetime.now(timezone.utc),
            balance=Decimal("0.00"),
        )

        self.users[user_id] = new_user
        self.users_by_email[user.email] = new_user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        return self.users_by_email.get(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        return self.users.get(user_id)

    async def update_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """Обновление баланса пользователя."""
        if user_id in self.users:
            self.users[user_id].balance = new_balance
            return True
        return False


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
            balance=0.00,
        )
        self.session.add(user_orm)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        result = await self.session.execute(select(UserORM).filter_by(email=email))
        user_orm = result.scalars().first()

        if user_orm:
            return User(
                id=user_orm.id,
                email=user_orm.email,
                password=user_orm.password_hash,  # Возвращаем хеш пароля для проверки
                created_at=user_orm.created_at,
                balance=Decimal(str(user_orm.balance)),
            )
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        result = await self.session.execute(select(UserORM).filter_by(id=user_id))
        user_orm = result.scalars().first()

        if user_orm:
            return User(
                id=user_orm.id,
                email=user_orm.email,
                password=user_orm.password_hash,  # Возвращаем хеш пароля для проверки
                created_at=user_orm.created_at,
                balance=Decimal(str(user_orm.balance)),
            )
        return None

    async def update_balance(self, user_id: int, new_balance: Decimal) -> bool:
        """Обновление баланса пользователя."""
        try:
            result = await self.session.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(balance=float(new_balance))
            )
            return bool(result.rowcount > 0)
        except Exception:
            return False
