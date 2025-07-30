"""Конфигурация для тестов."""

import os
import pytest
import warnings
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timedelta
from datetime import timezone

# Устанавливаем тестовые переменные окружения
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("SECRET_KEY", "test_secret_key_very_long_and_secure")
os.environ.setdefault("ACCESS_TOKEN_EXPIRES_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRES_HOURS", "24")
os.environ.setdefault("REQUEST_PRICE", "1.0")
os.environ.setdefault("CONFIDENCE_THRESHOLD", "0.8")
os.environ.setdefault("MIN_PRICE_LIMIT", "0.01")
os.environ.setdefault("MAX_PRICE_LIMIT", "10000.0")
os.environ.setdefault("DISABLE_AUTH_FOR_TESTS", "1")
os.environ.setdefault("MODEL_PATH", "pricing/catboost_model.pkl")
os.environ.setdefault("PREPROCESSING_PATH", "pricing/preprocessing.pkl")

from base.config import TaskStatus
from base.orm import Base
from base.data_structures import JWTPayloadDTO
from products.domain.models import Task
from users.adapters.orm import UserORM

# Подавление warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn.*")

DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def session():
    """Создает тестовую сессию базы данных."""
    engine = create_engine(DATABASE_URL, echo=False)

    # В SQLite внешние ключи отключены по умолчанию, включим их
    if DATABASE_URL.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def user(session: Session):
    """Создаёт и возвращает пользователя для тестов базы данных."""
    user = UserORM(
        id=1,
        email="user@example.com",
        username="testuser",
        password_hash="hashed_testpass",
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def mock_database():
    """Мок базы данных для изоляции тестов."""
    return AsyncMock()


@pytest.fixture
def mock_token():
    """Создает мок JWT токена."""
    return JWTPayloadDTO(
        id=1,
        exp=datetime.now(timezone.utc) + timedelta(minutes=30),
        type="access"
    )


@pytest.fixture
def isolated_client():
    """Изолированный тестовый клиент с полностью замоканными зависимостями."""
    from main import app
    
    # Мокаем все потенциально проблемные зависимости
    with pytest.MonkeyPatch().context() as mp:
        # Мокаем базу данных
        mock_db = AsyncMock()
        mp.setattr("base.dependencies.get_db", lambda: mock_db)
        
        # Мокаем Redis и RabbitMQ
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mp.setattr("redis.Redis", lambda **kwargs: mock_redis)
        
        mock_rabbitmq = Mock()
        mock_rabbitmq.is_closed = False
        mp.setattr("pika.BlockingConnection", lambda **kwargs: mock_rabbitmq)
        
        yield TestClient(app)
