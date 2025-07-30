"""Кастомные исключения приложения."""


class AppException(Exception):
    """Базовое исключение приложения."""
    pass


class AuthenticationError(AppException):
    """Ошибка аутентификации."""
    pass


class AuthorizationError(AppException):
    """Ошибка авторизации."""
    pass


class ValidationError(AppException):
    """Ошибка валидации данных."""
    pass


class DatabaseError(AppException):
    """Ошибка работы с базой данных."""
    pass


class ProductNotFoundError(AppException):
    """Товар не найден."""
    pass


class PermissionDeniedError(AppException):
    """Отказано в доступе."""
    pass


class InsufficientFundsError(AppException):
    """Недостаточно средств на балансе."""
    pass


class MLServiceError(AppException):
    """Ошибка ML сервиса."""
    pass


class TaskQueueError(AppException):
    """Ошибка очереди задач."""
    pass


class InvalidTokenException(AuthenticationError):
    """Исключение о том, что токен недействителен."""

    def __init__(self, detail: str) -> None:
        """Инициализация исключения."""
        super().__init__(detail)
        self.detail = detail


class DoesntExistException(AppException):
    """Исключение о том, что сущность не существует."""

    def __init__(self, detail: str = "Entity doesn't exist") -> None:
        """Инициализация исключения."""
        super().__init__(detail)
        self.detail = detail
