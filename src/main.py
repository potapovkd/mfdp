"""Основной модуль FastAPI приложения для системы ценовой оптимизации."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from base.config import get_allowed_hosts, get_api_prefix
from base.exception_handlers import add_exception_handlers
from base.orm import create_database_tables
from products.entrypoints.api.endpoints import (
    router as products_router,
)
from users.entrypoints.api.endpoints import router as users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title="Pricing Optimization API",
    description="API для системы ценовой оптимизации товаров",
    version="1.0.0",
)

# Добавление обработчиков исключений
add_exception_handlers(app)

# Инициализация таблиц базы данных будет выполнена при старте приложения

# Подключение маршрутизаторов
app.include_router(users_router, prefix=f"{get_api_prefix()}/users")
app.include_router(
    products_router,
    prefix=f"{get_api_prefix()}/products",
    tags=["products"]
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_hosts(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Инициализация метрик Prometheus
Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения."""
    logger.info("Starting database initialization...")
    try:
        from base.orm import create_database_tables_async
        await create_database_tables_async()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # В продакшене здесь можно добавить retry логику или graceful shutdown


@app.get("/")
async def root():
    """Корневой эндпойнт."""
    return {"message": "Pricing Optimization API"}


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса."""
    return {"status": "healthy"}
