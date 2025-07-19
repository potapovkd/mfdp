"""Конфигурация приложения."""

from decimal import Decimal
from enum import Enum
from typing import List


from pydantic_settings import BaseSettings


class TaskStatus(Enum):
    """Статусы выполнения ML задачи."""

    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Settings(BaseSettings):
    """Настройки приложения."""

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pricing_optimization"
    db_user: str = "pricing_user"
    db_password: str = "pricing_password"

    # Security
    secret_key: str = "super-secret-key-for-pricing-optimization-2024"
    allowed_hosts: str = "*"
    access_token_expires_minutes: int = 60
    refresh_token_expires_hours: int = 24

    # API
    api_prefix: str = "/api/v1"

    # ML Model
    model_path: str = "models/catboost_pricing_model.cbm"
    preprocessing_path: str = "models/preprocessing_pipeline.pkl"
    confidence_threshold: float = 0.7
    max_price_limit: float = 10000.0
    min_price_limit: float = 0.1

    # Pricing
    request_price: float = 5.0

    # Billing and Tariffs
    single_item_price: Decimal = Decimal("5.00")
    bulk_discount_threshold: int = 10
    bulk_discount_percent: int = 20
    max_items_per_request: int = 100

    # ML Workers
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "pricing"
    rabbitmq_pass: str = "pricing123"
    task_queue: str = "pricing_tasks"
    use_ml_workers: bool = True
    ml_worker_timeout: int = 30



    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


_settings = Settings()


def get_settings() -> Settings:
    """Получение настроек."""
    return _settings


def get_db_url() -> str:
    """Получение URL базы данных."""
    return f"postgresql+asyncpg://{_settings.db_user}:{_settings.db_password}@{_settings.db_host}:{_settings.db_port}/{_settings.db_name}"


def get_allowed_hosts() -> List[str]:
    """Получение разрешенных хостов."""
    if _settings.allowed_hosts == "*":
        return ["*"]
    return [host.strip() for host in _settings.allowed_hosts.split(",")]


def get_api_prefix() -> str:
    """Получение префикса API."""
    return _settings.api_prefix


def get_model_path() -> str:
    """Получение пути к модели."""
    return _settings.model_path


def get_preprocessing_path() -> str:
    """Получение пути к pipeline предобработки."""
    return _settings.preprocessing_path


def get_confidence_threshold() -> float:
    """Получение порога уверенности."""
    return _settings.confidence_threshold


def get_max_price_limit() -> float:
    """Получение максимального лимита цены."""
    return _settings.max_price_limit


def get_min_price_limit() -> float:
    """Получение минимального лимита цены."""
    return _settings.min_price_limit


def get_request_price() -> float:
    """Получение стоимости запроса."""
    return _settings.request_price


def get_single_item_price() -> Decimal:
    """Получение стоимости одного товара."""
    return _settings.single_item_price


def get_bulk_discount_threshold() -> int:
    """Получение порога для скидки на bulk запросы."""
    return _settings.bulk_discount_threshold


def get_bulk_discount_percent() -> int:
    """Получение процента скидки для bulk запросов."""
    return _settings.bulk_discount_percent


def get_max_items_per_request() -> int:
    """Получение максимального количества товаров в запросе."""
    return _settings.max_items_per_request


def get_redis_host() -> str:
    """Получение хоста Redis."""
    return _settings.redis_host


def get_redis_port() -> int:
    """Получение порта Redis."""
    return _settings.redis_port


def get_redis_db() -> int:
    """Получение базы данных Redis."""
    return _settings.redis_db


def get_rabbitmq_host() -> str:
    """Получение хоста RabbitMQ."""
    return _settings.rabbitmq_host


def get_rabbitmq_port() -> int:
    """Получение порта RabbitMQ."""
    return _settings.rabbitmq_port


def get_rabbitmq_user() -> str:
    """Получение пользователя RabbitMQ."""
    return _settings.rabbitmq_user


def get_rabbitmq_pass() -> str:
    """Получение пароля RabbitMQ."""
    return _settings.rabbitmq_pass


def get_task_queue() -> str:
    """Получение имени очереди задач."""
    return _settings.task_queue


def get_use_ml_workers() -> bool:
    """Получение флага использования ML воркеров."""
    return _settings.use_ml_workers


def get_ml_worker_timeout() -> int:
    """Получение таймаута ML воркера."""
    return _settings.ml_worker_timeout
