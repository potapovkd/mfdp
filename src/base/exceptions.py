"""Исключения."""

from fastapi import HTTPException


class EntityNotFoundException(HTTPException):
    """Исключение о том, что сущность не найдена."""

    def __init__(self, detail: str = "Entity not found") -> None:
        """Инициализация исключения."""
        super().__init__(status_code=404, detail=detail)


class AlreadyExistsException(HTTPException):
    """Исключение о том, что сущность уже существует."""

    def __init__(self, detail: str = "Entity already exists") -> None:
        """Инициализация исключения."""
        super().__init__(status_code=400, detail=detail)


class AuthException(HTTPException):
    """Исключение авторизации."""

    def __init__(self, detail: str = "Authentication required") -> None:
        """Инициализация исключения."""
        super().__init__(status_code=401, detail=detail)


class InvalidTokenException(Exception):
    """Исключение о том, что токен недействителен."""

    def __init__(self, detail: str) -> None:
        """Инициализация исключения."""
        super().__init__(detail)
        self.detail = detail


class InvalidCredentialsException(HTTPException):
    """Исключение о том, что учетные данные недействительны."""

    def __init__(self, detail: str = "Invalid credentials") -> None:
        """Инициализация исключения."""
        super().__init__(status_code=400, detail=detail)


class DoesntExistException(Exception):
    """Исключение о том, что сущность не существует."""

    def __init__(self, detail: str = "Entity doesn't exist") -> None:
        """Инициализация исключения."""
        super().__init__(detail)
        self.detail = detail
