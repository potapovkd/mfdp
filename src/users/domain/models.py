"""Модели пользователей для системы ценовой оптимизации."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCredentials(BaseModel):
    """Модель учетных данных пользователя."""

    email: EmailStr
    password: str


class UserMetadata(BaseModel):
    """Модель метаданных пользователя."""

    id: int
    created_at: datetime


class User(UserCredentials, UserMetadata):
    """Модель пользователя."""
