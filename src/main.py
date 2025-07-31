"""Основной модуль FastAPI приложения."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from base.config import get_settings
from base.exceptions import (
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
from base.orm import init_db
from products.entrypoints.api.endpoints import router as products_router
from users.entrypoints.api.endpoints import router as users_router

settings = get_settings()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Создаем FastAPI приложение
app = FastAPI(
    title="Pricing Optimization API",
    description="API для оптимизации цен на маркетплейсах",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Регистрация обработчиков исключений
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request, exc):
    """Обработчик ошибок аутентификации."""
    return JSONResponse(
        status_code=401, content={"detail": str(exc), "type": "authentication_error"}
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request, exc):
    """Обработчик ошибок авторизации."""
    return JSONResponse(
        status_code=403, content={"detail": str(exc), "type": "authorization_error"}
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """Обработчик ошибок валидации."""
    return JSONResponse(
        status_code=422, content={"detail": str(exc), "type": "validation_error"}
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request, exc):
    """Обработчик ошибок базы данных."""
    return JSONResponse(
        status_code=500, content={"detail": str(exc), "type": "database_error"}
    )


@app.exception_handler(ProductNotFoundError)
async def not_found_error_handler(request, exc):
    """Обработчик ошибок отсутствия товара."""
    return JSONResponse(
        status_code=404, content={"detail": str(exc), "type": "not_found_error"}
    )


@app.exception_handler(PermissionDeniedError)
async def permission_error_handler(request, exc):
    """Обработчик ошибок доступа."""
    return JSONResponse(
        status_code=403, content={"detail": str(exc), "type": "permission_error"}
    )


@app.exception_handler(InsufficientFundsError)
async def funds_error_handler(request, exc):
    """Обработчик ошибок недостатка средств."""
    return JSONResponse(
        status_code=402,
        content={"detail": str(exc), "type": "insufficient_funds_error"},
    )


@app.exception_handler(MLServiceError)
async def ml_error_handler(request, exc):
    """Обработчик ошибок ML сервиса."""
    return JSONResponse(
        status_code=500, content={"detail": str(exc), "type": "ml_service_error"}
    )


@app.exception_handler(TaskQueueError)
async def queue_error_handler(request, exc):
    """Обработчик ошибок очереди задач."""
    return JSONResponse(
        status_code=500, content={"detail": str(exc), "type": "task_queue_error"}
    )


# Регистрация роутеров
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(products_router, prefix="/api/v1/products", tags=["products"])


@app.get("/")
async def health_check():
    """Проверка работоспособности API."""
    return {"message": "API is running"}
