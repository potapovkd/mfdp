"""Конфигурация тестов."""

import os
# Устанавливаем тестовые переменные окружения перед импортом других модулей
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

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy import event

from base.config import TaskStatus  # noqa: E402
from base.orm import Base  # noqa: E402
from main import app  # noqa: E402
from products.domain.models import Task  # noqa: E402
from users.adapters.orm import UserORM  # noqa: E402

DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def session():

    engine = create_engine(DATABASE_URL, echo=False)

    # В SQLite внешние ключи отключены по умолчанию, включим их, чтобы
    # тесты корректно ловили ошибки нарушения целостности.
    if DATABASE_URL.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: D401, WPS430
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def mock_product_service(mocker):
    service = AsyncMock()
    service.get_user_products.return_value = []
    service.add_product = AsyncMock()
    service.update_task = AsyncMock()
    service.get_all_tasks.return_value = []
    service.get_task.return_value = Task(
        id=1, user_id=1, status=TaskStatus.NEW, type="pricing",
        input_data={}, result=None, created_at=None, updated_at=None
    )
    return service


@pytest.fixture
def mock_user_service(mocker):
    service = AsyncMock()
    service.add_user = AsyncMock()
    service.verify_credentials = AsyncMock()
    service.get_user_by_email = AsyncMock()
    service.get_user_by_id = AsyncMock()
    return service


@pytest.fixture
def mock_token():
    class DummyToken:
        id = 1
    return DummyToken()


@pytest.fixture
def client(
    mocker,
    mock_user_service,
    mock_token
):
    # Мокаем базовые зависимости
    mocker.patch("base.dependencies.TokenDependency", return_value=mock_token)

    # Мокаем get_user_service чтобы он возвращал наш mock_user_service
    mocker.patch("base.dependencies.get_user_service", return_value=mock_user_service)

    with TestClient(app) as c:
        yield c


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
