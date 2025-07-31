"""Unit тесты для всех компонентов проекта."""

import os
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from base.data_structures import JWTPayloadDTO
from base.exception_handlers import add_exception_handlers
from base.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    InsufficientFundsError,
    InvalidTokenException,
    MLServiceError,
    PermissionDeniedError,
    ProductNotFoundError,
    TaskQueueError,
    ValidationError,
)
from base.utils import JWTHandler
from users.domain.models import BillingRequest, BillingResponse, PricingTariff, User, UserCredentials
from users.services.services import UserService


# =============================================================================
# EXCEPTION HANDLERS TESTS
# =============================================================================

class TestExceptionHandlers:
    """Unit тесты для обработчиков исключений."""

    @pytest.fixture
    def app_with_handlers(self):
        """Фикстура для создания FastAPI приложения с обработчиками исключений."""
        app = FastAPI()
        add_exception_handlers(app)

        # Добавляем эндпоинты для тестирования каждого типа исключения
        @app.get("/test/app-exception")
        async def test_app_exception():
            raise AppException("Test app exception")

        @app.get("/test/auth-exception")
        async def test_auth_exception():
            raise AuthenticationError("Test authentication error")

        @app.get("/test/authorization-exception")
        async def test_authorization_exception():
            raise AuthorizationError("Test authorization error")

        @app.get("/test/validation-exception")
        async def test_validation_exception():
            raise ValidationError("Test validation error")

        @app.get("/test/database-exception")
        async def test_database_exception():
            raise DatabaseError("Test database error")

        @app.get("/test/not-found-exception")
        async def test_not_found_exception():
            raise ProductNotFoundError("Test product not found")

        @app.get("/test/permission-exception")
        async def test_permission_exception():
            raise PermissionDeniedError("Test permission denied")

        @app.get("/test/funds-exception")
        async def test_funds_exception():
            raise InsufficientFundsError("Test insufficient funds")

        @app.get("/test/ml-exception")
        async def test_ml_exception():
            raise MLServiceError("Test ML service error")

        @app.get("/test/queue-exception")
        async def test_queue_exception():
            raise TaskQueueError("Test task queue error")

        return app

    @pytest.fixture
    def client(self, app_with_handlers):
        """Фикстура для создания тестового клиента."""
        return TestClient(app_with_handlers)

    def test_app_exception_handler(self, client):
        """Тест обработчика AppException."""
        response = client.get("/test/app-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Test app exception"
        assert data["type"] == "app_error"

    def test_authentication_exception_handler(self, client):
        """Тест обработчика AuthenticationError."""
        response = client.get("/test/auth-exception")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Test authentication error"
        assert data["type"] == "authentication_error"

    def test_authorization_exception_handler(self, client):
        """Тест обработчика AuthorizationError."""
        response = client.get("/test/authorization-exception")
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Test authorization error"
        assert data["type"] == "authorization_error"

    def test_validation_exception_handler(self, client):
        """Тест обработчика ValidationError."""
        response = client.get("/test/validation-exception")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Test validation error"
        assert data["type"] == "validation_error"

    def test_database_exception_handler(self, client):
        """Тест обработчика DatabaseError."""
        response = client.get("/test/database-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Test database error"
        assert data["type"] == "database_error"

    def test_not_found_exception_handler(self, client):
        """Тест обработчика ProductNotFoundError."""
        response = client.get("/test/not-found-exception")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Test product not found"
        assert data["type"] == "not_found_error"

    def test_permission_exception_handler(self, client):
        """Тест обработчика PermissionDeniedError."""
        response = client.get("/test/permission-exception")
        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Test permission denied"
        assert data["type"] == "permission_denied"

    def test_funds_exception_handler(self, client):
        """Тест обработчика InsufficientFundsError."""
        response = client.get("/test/funds-exception")
        assert response.status_code == 402
        data = response.json()
        assert data["detail"] == "Test insufficient funds"
        assert data["type"] == "insufficient_funds"

    def test_ml_exception_handler(self, client):
        """Тест обработчика MLServiceError."""
        response = client.get("/test/ml-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Test ML service error"
        assert data["type"] == "ml_service_error"

    def test_queue_exception_handler(self, client):
        """Тест обработчика TaskQueueError."""
        response = client.get("/test/queue-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Test task queue error"
        assert data["type"] == "task_queue_error"


# =============================================================================
# JWT UTILS TESTS
# =============================================================================

class TestJWTHandler:
    """Unit тесты для JWTHandler."""

    @pytest.fixture
    def jwt_handler(self):
        """Фикстура для создания JWTHandler."""
        return JWTHandler("test_secret_key_very_long_and_secure")

    @pytest.fixture
    def user_id(self):
        """Фикстура с тестовым ID пользователя."""
        return 123

    def test_init(self):
        """Тест инициализации JWTHandler."""
        secret = "test_secret"
        handler = JWTHandler(secret)
        assert handler.secret_key == secret

    def test_create_access_token_default_expiry(self, jwt_handler, user_id):
        """Тест создания access токена с дефолтным временем истечения."""
        with patch("base.utils.settings.access_token_expires_minutes", 30):
            token = jwt_handler.create_access_token(user_id)
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Декодируем токен для проверки содержимого
            payload = jwt.decode(token, jwt_handler.secret_key, algorithms=["HS256"])
            assert payload["id"] == user_id
            assert payload["type"] == "access"
            assert "exp" in payload

    def test_create_access_token_custom_expiry(self, jwt_handler, user_id):
        """Тест создания access токена с пользовательским временем истечения."""
        custom_delta = timedelta(minutes=60)
        token = jwt_handler.create_access_token(user_id, custom_delta)
        
        payload = jwt.decode(token, jwt_handler.secret_key, algorithms=["HS256"])
        assert payload["id"] == user_id
        assert payload["type"] == "access"

    def test_create_access_token_jwt_error(self, user_id):
        """Тест обработки ошибки при создании токена."""
        # Мокаем jwt.encode чтобы он бросал исключение
        with patch("jwt.encode", side_effect=Exception("JWT encoding failed")):
            handler = JWTHandler("test_key")
            with pytest.raises(AuthenticationError) as excinfo:
                handler.create_access_token(user_id)
            assert "Failed to create token" in str(excinfo.value)

    def test_decode_token_valid(self, jwt_handler, user_id):
        """Тест декодирования валидного токена."""
        token = jwt_handler.create_access_token(user_id)
        decoded = jwt_handler.decode_token(token)
        
        assert isinstance(decoded, JWTPayloadDTO)
        assert decoded.id == user_id
        assert decoded.type == "access"

    def test_decode_token_expired(self, jwt_handler, user_id):
        """Тест декодирования истекшего токена."""
        # Создаем токен с истекшим временем
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expire_timestamp = int(past_time.timestamp())
        
        payload = {"id": user_id, "exp": expire_timestamp, "type": "access"}
        expired_token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.decode_token(expired_token)
        assert "Token has expired" in str(excinfo.value)

    def test_decode_token_invalid(self, jwt_handler):
        """Тест декодирования невалидного токена."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.decode_token(invalid_token)
        assert "Invalid token" in str(excinfo.value)

    def test_decode_token_wrong_secret(self, user_id):
        """Тест декодирования токена с неправильным секретом."""
        handler1 = JWTHandler("secret1")
        handler2 = JWTHandler("secret2")
        
        token = handler1.create_access_token(user_id)
        
        with pytest.raises(InvalidTokenException) as excinfo:
            handler2.decode_token(token)
        assert "Invalid token" in str(excinfo.value)

    def test_create_refresh_token(self, jwt_handler, user_id):
        """Тест создания refresh токена."""
        with patch("base.utils.settings.refresh_token_expires_hours", 24):
            token = jwt_handler.create_refresh_token(user_id)
            
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Декодируем токен для проверки содержимого
            payload = jwt.decode(token, jwt_handler.secret_key, algorithms=["HS256"])
            assert payload["id"] == user_id
            assert payload["type"] == "refresh"
            assert "exp" in payload

    def test_create_refresh_token_jwt_error(self, user_id):
        """Тест обработки ошибки при создании refresh токена."""
        # Мокаем jwt.encode чтобы он бросал исключение
        with patch("jwt.encode", side_effect=Exception("JWT encoding failed")):
            handler = JWTHandler("test_key")
            with pytest.raises(AuthenticationError) as excinfo:
                handler.create_refresh_token(user_id)
            assert "Failed to create refresh token" in str(excinfo.value)

    def test_verify_refresh_token_valid(self, jwt_handler, user_id):
        """Тест верификации валидного refresh токена."""
        refresh_token = jwt_handler.create_refresh_token(user_id)
        verified_user_id = jwt_handler.verify_refresh_token(refresh_token)
        
        assert verified_user_id == user_id

    def test_verify_refresh_token_not_refresh_type(self, jwt_handler, user_id):
        """Тест верификации access токена как refresh (должно упасть)."""
        access_token = jwt_handler.create_access_token(user_id)
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.verify_refresh_token(access_token)
        assert "Not a refresh token" in str(excinfo.value)

    def test_verify_refresh_token_no_user_id(self, jwt_handler):
        """Тест верификации refresh токена без user ID."""
        # Создаем токен без ID
        payload = {"exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()), "type": "refresh"}
        token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.verify_refresh_token(token)
        assert "Token does not contain user ID" in str(excinfo.value)

    def test_verify_refresh_token_expired(self, jwt_handler, user_id):
        """Тест верификации истекшего refresh токена."""
        # Создаем токен с истекшим временем
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expire_timestamp = int(past_time.timestamp())
        
        payload = {"id": user_id, "exp": expire_timestamp, "type": "refresh"}
        expired_token = jwt.encode(payload, jwt_handler.secret_key, algorithm="HS256")
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.verify_refresh_token(expired_token)
        assert "Refresh token has expired" in str(excinfo.value)

    def test_verify_refresh_token_invalid(self, jwt_handler):
        """Тест верификации невалидного refresh токена."""
        invalid_token = "invalid.refresh.token"
        
        with pytest.raises(InvalidTokenException) as excinfo:
            jwt_handler.verify_refresh_token(invalid_token)
        assert "Invalid refresh token" in str(excinfo.value)

    def test_decode_token_general_exception(self, jwt_handler):
        """Тест обработки общих исключений при декодировании токена."""
        with patch("jwt.decode", side_effect=Exception("Unexpected error")):
            with pytest.raises(InvalidTokenException) as excinfo:
                jwt_handler.decode_token("any_token")
            assert "Token decode error" in str(excinfo.value)

    def test_verify_refresh_token_general_exception(self, jwt_handler):
        """Тест обработки общих исключений при верификации refresh токена."""
        with patch("jwt.decode", side_effect=Exception("Unexpected error")):
            with pytest.raises(InvalidTokenException) as excinfo:
                jwt_handler.verify_refresh_token("any_token")
            assert "Refresh token verify error" in str(excinfo.value)


# =============================================================================
# USER SERVICES TESTS
# =============================================================================

class TestUserService:
    """Unit тесты для UserService."""

    @pytest.fixture
    def mock_uow(self):
        """Мок Unit of Work."""
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_uow):
        """Фикстура UserService с мокированным UoW."""
        return UserService(uow=mock_uow)

    @pytest.fixture
    def user_credentials(self):
        """Учетные данные пользователя."""
        return UserCredentials(
            email="test@example.com",
            password="password123"
        )

    @pytest.fixture
    def billing_request(self):
        """Запрос на списание средств."""
        return BillingRequest(
            user_id=1,
            amount=Decimal("50.00"),
            description="Test charge"
        )

    @pytest.fixture
    def mock_user(self):
        """Мок пользователя."""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        # Хеш пароля "hello" - 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        user.password = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        user.balance = Decimal("100.00")
        return user

    @pytest.mark.asyncio
    async def test_add_user_success(self, user_service, mock_uow, user_credentials):
        """Тест успешного добавления пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        
        await user_service.add_user(user_credentials)
        
        mock_uow.users.add_user.assert_called_once_with(user_credentials)
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_uow, mock_user):
        """Тест успешного получения пользователя по email."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_email.return_value = mock_user
        
        result = await user_service.get_user_by_email("test@example.com")
        
        assert result == mock_user
        mock_uow.users.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service, mock_uow):
        """Тест получения несуществующего пользователя по email."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_email.return_value = None
        
        result = await user_service.get_user_by_email("notfound@example.com")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_uow, mock_user):
        """Тест успешного получения пользователя по ID."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = mock_user
        
        result = await user_service.get_user_by_id(1)
        
        assert result == mock_user
        mock_uow.users.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_verify_credentials_success(self, user_service, mock_uow):
        """Тест успешной проверки учетных данных."""
        # Создаем реальный объект User вместо Mock
        from users.domain.models import User
        from datetime import datetime, timezone
        
        user = User(
            id=1,
            email="test@example.com",
            password="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",  # sha256("hello")
            created_at=datetime.now(timezone.utc),
            balance=Decimal("100.00")
        )
        
        # Настраиваем mock_uow.users
        mock_uow.users = AsyncMock()
        mock_uow.users.get_user_by_email.return_value = user
        
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        
        result = await user_service.verify_credentials("test@example.com", "hello")
        
        assert result == user
        mock_uow.users.get_user_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_verify_credentials_wrong_password(self, user_service, mock_uow):
        """Тест проверки с неправильным паролем."""
        # Создаем реальный объект User
        from users.domain.models import User
        from datetime import datetime, timezone
        
        user = User(
            id=1,
            email="test@example.com",
            password="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",  # sha256("hello")
            created_at=datetime.now(timezone.utc),
            balance=Decimal("100.00")
        )
        
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_email.return_value = user
        
        result = await user_service.verify_credentials("test@example.com", "wrongpassword")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service, user_credentials):
        """Тест успешной аутентификации пользователя."""
        with patch.object(user_service, 'verify_credentials') as mock_verify:
            mock_user = Mock()
            mock_user.id = 1
            mock_verify.return_value = mock_user
            
            with patch("base.utils.JWTHandler") as mock_jwt_class:
                mock_jwt_handler = Mock()
                mock_jwt_handler.create_access_token.return_value = "access_token"
                mock_jwt_class.return_value = mock_jwt_handler
                
                with patch("base.config.get_settings") as mock_settings:
                    mock_settings.return_value.secret_key = "test_secret"
                    
                    result = await user_service.authenticate_user(user_credentials)
                    
                    assert result == "access_token"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, user_service, user_credentials):
        """Тест аутентификации с неверными учетными данными."""
        with patch.object(user_service, 'verify_credentials') as mock_verify:
            mock_verify.return_value = None
            
            with pytest.raises(AuthenticationError) as excinfo:
                await user_service.authenticate_user(user_credentials)
            
            assert "Неверные учетные данные" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_user_balance_success(self, user_service, mock_uow, mock_user):
        """Тест успешного получения баланса пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = mock_user
        
        result = await user_service.get_user_balance(1)
        
        assert result == Decimal("100.00")
        mock_uow.users.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_balance_user_not_found(self, user_service, mock_uow):
        """Тест получения баланса несуществующего пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = None
        
        result = await user_service.get_user_balance(999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_user_balance_success(self, user_service, mock_uow):
        """Тест успешного обновления баланса пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.update_balance.return_value = True
        
        result = await user_service.update_user_balance(1, Decimal("150.00"))
        
        assert result is True
        mock_uow.users.update_balance.assert_called_once_with(1, Decimal("150.00"))
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_balance_failed(self, user_service, mock_uow):
        """Тест неудачного обновления баланса."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.update_balance.return_value = False
        
        result = await user_service.update_user_balance(1, Decimal("150.00"))
        
        assert result is False
        mock_uow.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_charge_user_success(self, user_service, mock_uow, mock_user, billing_request):
        """Тест успешного списания средств с пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = mock_user
        mock_uow.users.update_balance.return_value = True
        
        result = await user_service.charge_user(billing_request)
        
        assert result.success is True
        assert result.new_balance == Decimal("50.00")  # 100 - 50
        assert result.charged_amount == Decimal("50.00")
        mock_uow.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_charge_user_not_found(self, user_service, mock_uow, billing_request):
        """Тест списания средств у несуществующего пользователя."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = None
        
        result = await user_service.charge_user(billing_request)
        
        assert result.success is False
        assert result.message == "Пользователь не найден"

    @pytest.mark.asyncio
    async def test_charge_user_insufficient_funds(self, user_service, mock_uow, mock_user):
        """Тест списания при недостатке средств."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = mock_user
        
        # Запрос на сумму больше баланса
        billing_request = BillingRequest(
            user_id=1,
            amount=Decimal("150.00"),
            description="Large charge"
        )
        
        result = await user_service.charge_user(billing_request)
        
        assert result.success is False
        assert "Недостаточно средств" in result.message

    @pytest.mark.asyncio
    async def test_charge_user_update_failed(self, user_service, mock_uow, mock_user, billing_request):
        """Тест ошибки при обновлении баланса."""
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None
        mock_uow.users.get_user_by_id.return_value = mock_user
        mock_uow.users.update_balance.return_value = False
        
        result = await user_service.charge_user(billing_request)
        
        assert result.success is False
        assert result.message == "Ошибка при списании средств"

    def test_calculate_pricing_cost_single_item(self, user_service):
        """Тест расчета стоимости для одного товара."""
        result = user_service.calculate_pricing_cost(1)
        
        expected = Decimal("5.00")  # PricingTariff.single_item_price по умолчанию
        assert result == expected

    def test_calculate_pricing_cost_multiple_items(self, user_service):
        """Тест расчета стоимости для нескольких товаров."""
        result = user_service.calculate_pricing_cost(5)
        
        expected = Decimal("25.00")  # 5 * 5.00
        assert result == expected

    def test_calculate_pricing_cost_bulk_discount(self, user_service):
        """Тест расчета стоимости с bulk скидкой."""
        # Устанавливаем параметры тарифа для тестирования скидки
        user_service.tariff.bulk_discount_threshold = 10
        user_service.tariff.bulk_discount_percent = 10.0
        
        result = user_service.calculate_pricing_cost(10)
        
        base_cost = Decimal("50.00")  # 10 * 5.00
        discount = base_cost * Decimal("0.10")  # 10% скидка
        expected = base_cost - discount
        assert result == expected

    def test_calculate_pricing_cost_zero_items(self, user_service):
        """Тест расчета стоимости для нуля товаров."""
        result = user_service.calculate_pricing_cost(0)
        
        assert result == Decimal("0.00")

    def test_calculate_pricing_cost_exceeds_limit(self, user_service):
        """Тест превышения лимита товаров."""
        with pytest.raises(ValueError) as excinfo:
            user_service.calculate_pricing_cost(1001)  # По умолчанию лимит 1000
        
        assert "Превышен лимит товаров в запросе" in str(excinfo.value)

    def test_get_tariff_info(self, user_service):
        """Тест получения информации о тарифах."""
        result = user_service.get_tariff_info()
        
        assert isinstance(result, PricingTariff)
        assert result == user_service.tariff


# =============================================================================
# ML MODEL TESTS
# =============================================================================

class TestModelMetrics:
    """Unit тесты для класса ModelMetrics."""

    def test_initialization(self):
        """Тест инициализации метрик."""
        from pricing.model_trainer import ModelMetrics
        
        metrics = ModelMetrics()
        assert metrics.metrics["train"]["rmse"] == 0.0
        assert metrics.metrics["train"]["mae"] == 0.0
        assert metrics.metrics["train"]["r2"] == 0.0
        assert metrics.metrics["test"]["rmse"] == 0.0
        assert metrics.metrics["test"]["mae"] == 0.0
        assert metrics.metrics["test"]["r2"] == 0.0
        assert metrics.model_version == ""
        assert isinstance(metrics.dataset_stats, dict)
        assert isinstance(metrics.feature_importance, dict)

    def test_to_dict(self):
        """Тест преобразования метрик в словарь."""
        from pricing.model_trainer import ModelMetrics
        
        metrics = ModelMetrics()
        metrics.metrics["train"]["rmse"] = 1.0
        metrics.metrics["test"]["rmse"] = 1.5
        metrics.model_version = "test_version"

        metrics_dict = metrics.to_dict()
        assert metrics_dict["metrics"]["train"]["rmse"] == 1.0
        assert metrics_dict["metrics"]["test"]["rmse"] == 1.5
        assert metrics_dict["model_version"] == "test_version"

    def test_save_to_file(self, tmp_path):
        """Тест сохранения метрик в файл."""
        import json
        from pricing.model_trainer import ModelMetrics
        
        metrics = ModelMetrics()
        metrics.metrics["train"]["rmse"] = 1.0
        metrics.metrics["test"]["rmse"] = 1.5
        metrics.model_version = "test_version"

        metrics_file = tmp_path / "metrics.json"
        metrics.save(metrics_file)

        assert metrics_file.exists()
        with open(metrics_file) as f:
            loaded_metrics = json.load(f)
            assert loaded_metrics["metrics"]["train"]["rmse"] == 1.0
            assert loaded_metrics["metrics"]["test"]["rmse"] == 1.5


class TestModelTrainer:
    """Unit тесты для класса PricingModelTrainer."""

    @pytest.fixture
    def trainer(self, tmp_path):
        """Фикстура для создания тренера модели."""
        from pricing.model_trainer import PricingModelTrainer
        
        return PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version="test_version"
        )

    def test_model_versioning(self, tmp_path):
        """Тест системы версионирования моделей."""
        from pricing.model_trainer import PricingModelTrainer
        
        version1 = "20240101_120000"
        version2 = "20240101_130000"
        trainer1 = PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version=version1
        )
        trainer2 = PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version=version2
        )

        assert trainer1.version_dir.exists()
        assert trainer2.version_dir.exists()
        assert (tmp_path / version1).exists()
        assert (tmp_path / version2).exists()

    def test_model_training_and_saving(self, trainer):
        """Тест обучения и сохранения модели."""
        import pandas as pd
        import numpy as np
        import warnings
        
        # Создаем тестовый датасет с достаточным количеством данных
        df = pd.DataFrame(
            {
                "price": [100, 200, 300, 150, 250],
                "name": [
                    "Product 1",
                    "Product 2",
                    "Product 3",
                    "Product 4",
                    "Product 5",
                ],
                "category_name": ["Electronics"] * 5,
                "brand_name": ["Apple", "Samsung", "Apple", "Google", "Samsung"],
                "item_description": ["Test"] * 5,
                "item_condition_id": [1, 2, 1, 3, 2],
                "shipping": [0, 1, 0, 1, 0],
            }
        )

        # Мокаем весь модуль catboost
        with patch("pricing.model_trainer.CatBoostRegressor") as mock_catboost_class:
            mock_model = Mock()
            mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2])

            # Мокаем predict чтобы возвращал правильное количество предсказаний
            def mock_predict(X):
                return np.array([10.0, 15.0, 12.0, 13.0, 14.0][: len(X)])

            mock_model.predict = Mock(side_effect=mock_predict)
            mock_model.fit = Mock()
            mock_model.save_model = Mock()
            mock_catboost_class.return_value = mock_model

            # Подавляем предупреждения о R^2 score
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                # Обучаем модель
                trainer.train_model(df)

            # Проверяем что методы были вызваны
            mock_model.fit.assert_called_once()
            mock_model.save_model.assert_called_once()

            # Проверяем что метрики были созданы
            assert hasattr(trainer.metrics, "metrics")
            assert "train" in trainer.metrics.metrics
            assert "test" in trainer.metrics.metrics
            assert hasattr(trainer.metrics, "feature_importance")

    def test_dataset_statistics(self, trainer):
        """Тест сбора статистик датасета."""
        import pandas as pd
        
        # Создаем тестовый датасет
        df = pd.DataFrame(
            {
                "price": [100, 200, 300, 400, 500],
                "name": [
                    "Product 1",
                    "Product 2",
                    "Product 3",
                    "Product 4",
                    "Product 5",
                ],
                "category_name": ["Electronics"] * 3 + ["Books"] * 2,
                "brand_name": ["Apple", "Samsung", "Apple", "Unknown", "Unknown"],
                "item_description": ["Test"] * 5,
                "item_condition_id": [1, 2, 1, 3, 2],
                "shipping": [0, 1, 0, 1, 0],
            }
        )

        # Запускаем предобработку
        df = trainer.preprocess_data(df)

        # Проверяем статистики
        assert "category_counts" in trainer.metrics.dataset_stats
        assert "brand_counts" in trainer.metrics.dataset_stats
        assert "condition_counts" in trainer.metrics.dataset_stats
        assert "shipping_counts" in trainer.metrics.dataset_stats
        assert "price_stats" in trainer.metrics.dataset_stats

        # Проверяем конкретные значения
        assert trainer.metrics.dataset_stats["category_counts"]["Electronics"] == 3
        assert trainer.metrics.dataset_stats["category_counts"]["Books"] == 2
        assert trainer.metrics.dataset_stats["brand_counts"]["Apple"] == 2
        assert trainer.metrics.dataset_stats["brand_counts"]["Unknown"] == 2


# =============================================================================
# DATABASE TESTS  
# =============================================================================

class TestDatabaseModels:
    """Unit тесты для ORM моделей базы данных."""

    def test_create_user(self, session):
        """Тест создания пользователя."""
        from users.adapters.orm import UserORM
        
        user = UserORM(
            email="test@example.com", username="testuser", password_hash="hashed_password"
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        db_user = session.query(UserORM).filter_by(id=user.id).first()
        assert db_user is not None
        assert db_user.email == "test@example.com"
        assert db_user.username == "testuser"

    def test_create_product(self, session, user):
        """Тест создания продукта."""
        from products.adapters.orm import ProductORM
        
        product = ProductORM(
            user_id=user.id,
            name="Test Product",
            category_name="Electronics",
            brand_name="TestBrand",
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        db_product = session.query(ProductORM).filter_by(id=product.id).first()
        assert db_product is not None
        assert db_product.user_id == user.id
        assert db_product.name == "Test Product"

    def test_create_task(self, session, user):
        """Тест создания задачи ценообразования."""
        from products.adapters.orm import ProductORM, TaskORM
        
        # Сначала создаем продукт
        product = ProductORM(
            user_id=user.id, name="Test Product", category_name="Electronics"
        )
        session.add(product)
        session.commit()
        session.refresh(product)

        # Затем создаем задачу
        task = TaskORM(
            product_id=product.id, type="pricing", input_data='{"product": "test"}'
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        db_task = session.query(TaskORM).filter_by(id=task.id).first()
        assert db_task is not None
        assert db_task.product_id == product.id
        assert db_task.type == "pricing"

    def test_fail_create_task_without_product(self, session):
        """Тест создания задачи без продукта."""
        from products.adapters.orm import TaskORM
        
        task = TaskORM(product_id=999, type="pricing")
        with pytest.raises(Exception):
            session.add(task)
            session.commit() 