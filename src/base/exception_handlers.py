"""Обработчики исключений для FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    InsufficientFundsError,
    MLServiceError,
    PermissionDeniedError,
    ProductNotFoundError,
    TaskQueueError,
    ValidationError,
)


def add_exception_handlers(app: FastAPI) -> None:
    """Добавление обработчиков исключений в приложение."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Базовый обработчик исключений приложения."""
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": "app_error"}
        )

    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        """Обработчик ошибок аутентификации."""
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "type": "authentication_error"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        """Обработчик ошибок авторизации."""
        return JSONResponse(
            status_code=403, content={"detail": str(exc), "type": "authorization_error"}
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Обработчик ошибок валидации."""
        return JSONResponse(
            status_code=400, content={"detail": str(exc), "type": "validation_error"}
        )

    @app.exception_handler(DatabaseError)
    async def db_exception_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        """Обработчик ошибок базы данных."""
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": "database_error"}
        )

    @app.exception_handler(ProductNotFoundError)
    async def not_found_exception_handler(
        request: Request, exc: ProductNotFoundError
    ) -> JSONResponse:
        """Обработчик ошибок отсутствия товара."""
        return JSONResponse(
            status_code=404, content={"detail": str(exc), "type": "not_found_error"}
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_exception_handler(
        request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        """Обработчик ошибок доступа."""
        return JSONResponse(
            status_code=403, content={"detail": str(exc), "type": "permission_denied"}
        )

    @app.exception_handler(InsufficientFundsError)
    async def funds_exception_handler(
        request: Request, exc: InsufficientFundsError
    ) -> JSONResponse:
        """Обработчик ошибок недостатка средств."""
        return JSONResponse(
            status_code=402, content={"detail": str(exc), "type": "insufficient_funds"}
        )

    @app.exception_handler(MLServiceError)
    async def ml_exception_handler(
        request: Request, exc: MLServiceError
    ) -> JSONResponse:
        """Обработчик ошибок ML сервиса."""
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": "ml_service_error"}
        )

    @app.exception_handler(TaskQueueError)
    async def queue_exception_handler(
        request: Request, exc: TaskQueueError
    ) -> JSONResponse:
        """Обработчик ошибок очереди задач."""
        return JSONResponse(
            status_code=500, content={"detail": str(exc), "type": "task_queue_error"}
        )
