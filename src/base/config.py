"""Модуль конфигурации."""

from enum import Enum
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения."""

    secret_key: str = os.getenv("SECRET_KEY", "default_secret")
    access_token_expires_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", "60")
    )
    postgres_user: str = os.getenv("POSTGRES_USER", "test")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "test")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "test_db")


def get_settings() -> Settings:
    """Получение настроек приложения."""
    return Settings()


def get_postgres_url() -> str:
    """Получение URL подключения к базе данных PostgreSQL."""
    # При запуске юниттестов возможно, что PostgreSQL недоступен.
    # Если переменная окружения PYTEST_CURRENT_TEST присутствует (устанавливается pytest),
    # то используем более лёгкую in-memory SQLite базу, совместимую
    # с асинхронным движком ``aiosqlite``.
    if os.getenv("PYTEST_CURRENT_TEST") is not None:
        return "sqlite+aiosqlite:///:memory:"

    return (
        "postgresql+asyncpg://"
        + os.getenv("DB_USER", "pricing_user")
        + ":"
        + os.getenv("DB_PASSWORD", "pricing_password")
        + "@"
        + os.getenv("DB_HOST", "db")
        + ":"
        + os.getenv("DB_PORT", "5432")
        + "/"
        + os.getenv("DB_NAME", "pricing_optimization")
    )


def show_sql_logs() -> bool:
    """Показывать ли логи SQL-запросов."""
    return os.getenv("SHOW_SQL_LOGS") == "True"


def get_secret_key() -> str:
    """Получение секретного ключа."""
    return os.getenv("SECRET_KEY")


def get_allowed_hosts() -> list[str]:
    """Получение допустимых хостов."""
    if not os.getenv("ALLOWED_HOSTS"):
        return ["*"]
    return os.getenv("ALLOWED_HOSTS", "").split(",")


def get_api_prefix() -> str:
    """Получение префикса API."""
    return os.getenv("API_PREFIX") or "/api/v1"


def get_access_token_expires_minutes() -> int:
    """Получение времени жизни access токена в минутах."""
    if os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"):
        return int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"))
    return 60


def get_refresh_token_expires_hours() -> int:
    """Получение времени жизни refresh токена в часах."""
    if os.getenv("REFRESH_TOKEN_EXPIRES_HOURS"):
        return int(os.getenv("REFRESH_TOKEN_EXPIRES_HOURS"))
    return 24


def get_time_for_getting_jwt_from_ws() -> int:
    """Получение времени для предоставления JWT через WebSocket."""
    if os.getenv("TIME_FOR_GETTING_JWT_FROM_WS"):
        return int(os.getenv("TIME_FOR_GETTING_JWT_FROM_WS"))
    return 5


def get_ml_service_url() -> str:
    """Получение пути до микросервиса машинного обучения."""
    ml_host = os.getenv("ML_HOST", "localhost")
    ml_port = os.getenv("ML_PORT", "8001")
    return f"http://{ml_host}:{ml_port}"


def get_model_path() -> str:
    """Получение пути к обученной модели."""
    return os.getenv("MODEL_PATH") or "models/catboost_pricing_model.cbm"


def get_preprocessing_path() -> str:
    """Получение пути к pipeline предобработки."""
    return os.getenv("PREPROCESSING_PATH") or "models/preprocessing_pipeline.pkl"


def get_confidence_threshold() -> float:
    """Получение порога уверенности модели."""
    if os.getenv("CONFIDENCE_THRESHOLD"):
        return float(os.getenv("CONFIDENCE_THRESHOLD"))
    return 0.7


class TaskStatus(Enum):
    """Статусы выполнения ML задачи."""

    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def get_request_price() -> float:
    """Получить цену выполнения запроса на прогнозирование цены."""
    if os.getenv("REQUEST_PRICE"):
        return float(os.getenv("REQUEST_PRICE"))
    return 5.0  # Снижаем цену для ценового прогноза


def get_max_price_limit() -> float:
    """Получить максимальную цену для прогнозирования."""
    if os.getenv("MAX_PRICE_LIMIT"):
        return float(os.getenv("MAX_PRICE_LIMIT"))
    return 10000.0


def get_min_price_limit() -> float:
    """Получить минимальную цену для прогнозирования."""
    if os.getenv("MIN_PRICE_LIMIT"):
        return float(os.getenv("MIN_PRICE_LIMIT"))
    return 0.1
