"""Unit тесты для сервисов пользователей."""
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from users.domain.models import User, UserCredentials
from users.services.services import UserService


class TestUserService:
    """Unit тесты для UserService."""

    @pytest.mark.asyncio
    async def test_add_user(self):
        """Тест добавления пользователя."""
        # Arrange
        mock_uow = AsyncMock()
        mock_uow.users = AsyncMock()

        service = UserService(mock_uow)
        user_credentials = UserCredentials(
            email="test@example.com", password="password123"
        )

        # Act
        await service.add_user(user_credentials)

        # Assert
        mock_uow.users.add_user.assert_called_once_with(user_credentials)
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_credentials_success(self):
        """Тест успешной верификации учетных данных."""
        # Arrange
        mock_uow = AsyncMock()
        mock_uow.users = AsyncMock()

        # Создаем пользователя с хешированным паролем
        password = "password123"
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        test_user = User(
            id=1,
            email="test@example.com",
            password=password_hash,
            created_at=datetime.now(),
        )

        mock_uow.users.get_user_by_email.return_value = test_user

        service = UserService(mock_uow)

        # Act
        result = await service.verify_credentials("test@example.com", password)

        # Assert
        assert result == test_user
        mock_uow.users.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_verify_credentials_invalid_password(self):
        """Тест неверного пароля."""
        # Arrange
        mock_uow = AsyncMock()
        mock_uow.users = AsyncMock()

        # Создаем пользователя с другим паролем
        correct_password = "correct_password"
        password_hash = hashlib.sha256(correct_password.encode()).hexdigest()

        test_user = User(
            id=1,
            email="test@example.com",
            password=password_hash,
            created_at=datetime.now(),
        )

        mock_uow.users.get_user_by_email.return_value = test_user

        service = UserService(mock_uow)

        # Act
        result = await service.verify_credentials("test@example.com", "wrong_password")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_credentials_user_not_found(self):
        """Тест когда пользователь не найден."""
        # Arrange
        mock_uow = AsyncMock()
        mock_uow.users = AsyncMock()
        mock_uow.users.get_user_by_email.return_value = None

        service = UserService(mock_uow)

        # Act
        result = await service.verify_credentials("nonexistent@example.com", "password")

        # Assert
        assert result is None
