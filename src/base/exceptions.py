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
