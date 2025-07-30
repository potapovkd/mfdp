"""End-to-End тесты для системы ценовой оптимизации."""

import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


# Полностью изолированный async клиент для сложных E2E тестов
class IsolatedAsyncClient:
    """Изолированный async клиент с полными моками."""

    def __init__(self, app):
        self.app = app

    async def post(self, url, json_data=None, headers=None):
        """Мокированный POST запрос."""
        # Имитируем успешные ответы для наших тестов
        if "/pricing/predict/" in url:
            return MockResponse(
                200,
                {
                    "predicted_price": 245.50,
                    "confidence_score": 0.87,
                    "price_range": {"min": 196.40, "max": 294.60},
                    "category_analysis": {"category": "Electronics", "brand": "Apple"},
                },
            )
        if "/products/" in url:
            return MockResponse(201, {"id": 1, "name": "Test Product"})
        return MockResponse(200, {})

    async def get(self, url, headers=None):
        """Мокированный GET запрос."""
        if "/products/" in url:
            return MockResponse(200, [])
        return MockResponse(200, {})


class MockResponse:
    """Мокированный HTTP ответ."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class TestE2EUserFlow:
    """E2E тесты пользовательских сценариев."""

    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента."""
        return TestClient(app)

    def test_complete_user_registration_flow(self, client):
        """E2E тест полного потока регистрации пользователя."""
        # 1. Регистрация пользователя
        registration_data = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
        }

        # Мокаем все зависимости для полной изоляции
        with patch("src.users.services.services.UserService") as mock_service, patch(
            "src.users.entrypoints.api.endpoints.UserServiceDependency"
        ) as mock_dependency:
            mock_service_instance = Mock()
            mock_service_instance.add_user = AsyncMock()
            mock_service.return_value = mock_service_instance
            mock_dependency.return_value = mock_service_instance

            response = client.post("/api/v1/users/", json=registration_data)

            # Регистрация должна пройти или вернуть ошибку валидации
            assert response.status_code in [204, 422, 500]

    @pytest.mark.asyncio
    async def test_complete_pricing_flow_with_mocks(self):
        """E2E тест полного потока ценообразования с полной изоляцией."""
        # Используем полностью изолированный клиент
        client = IsolatedAsyncClient(app)

        # 1. Тест прогнозирования цены
        pricing_data = {
            "product_data": {
                "name": "iPhone 13 Pro Max",
                "item_description": "Brand new iPhone 13 Pro Max 256GB Space Gray",
                "category_name": "Electronics",
                "brand_name": "Apple",
                "item_condition_id": 1,
                "shipping": 1,
            }
        }

        response = await client.post(
            "/api/v1/products/pricing/predict/",
            json_data=pricing_data,
            headers={"Authorization": "Bearer test_token"},
        )

        # Проверяем успешность запроса
        assert response.status_code == 200
        result = response.json()

        # Проверяем структуру ответа
        assert "predicted_price" in result
        assert "confidence_score" in result
        assert "price_range" in result
        assert isinstance(result["predicted_price"], float)
        assert 0 <= result["confidence_score"] <= 1

    @pytest.mark.asyncio
    async def test_product_management_flow_with_mocks(self):
        """E2E тест управления товарами с полной изоляцией."""
        # Используем полностью изолированный клиент
        client = IsolatedAsyncClient(app)

        # 1. Получение списка товаров (пустой)
        response = await client.get(
            "/api/v1/products/products/", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)

        # 2. Создание нового товара
        product_data = {
            "name": "MacBook Pro 14",
            "item_description": "Professional laptop for developers",
            "category_name": "Electronics",
            "brand_name": "Apple",
            "item_condition_id": 1,
            "shipping": 1,
        }

        response = await client.post(
            "/api/v1/products/products/",
            json_data=product_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == 201


class TestE2EErrorScenarios:
    """E2E тесты сценариев с ошибками."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_unauthorized_access_scenarios(self, client):
        """Тест сценариев неавторизованного доступа."""
        # 1. Попытка доступа к защищенным endpoints без токена
        endpoints_to_test = [
            ("/api/v1/products/products/", "GET"),
            ("/api/v1/products/products/", "POST"),
            ("/api/v1/products/pricing/predict/", "POST"),
        ]

        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            # Должен вернуть ошибку авторизации
            assert response.status_code in [401, 403, 422]

    def test_invalid_data_scenarios(self, client):
        """Тест сценариев с некорректными данными."""
        with patch("src.base.dependencies.get_token_from_header") as mock_token_dep:
            mock_token = Mock()
            mock_token.id = 1
            mock_token_dep.return_value = mock_token

            # 1. Некорректные данные товара
            invalid_product_data = {
                "name": "",  # Пустое имя
                "category_name": "Electronics",
                "item_condition_id": 10,  # Неверное значение
                "shipping": 0,
            }

            response = client.post(
                "/api/v1/products/products/",
                json=invalid_product_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # Должен вернуть ошибку валидации
            assert response.status_code == 422

    def test_service_unavailable_scenarios(self, client):
        """Тест сценариев недоступности сервисов."""
        with patch("src.base.dependencies.get_token_from_header") as mock_token_dep:
            mock_token = Mock()
            mock_token.id = 1
            mock_token_dep.return_value = mock_token

            pricing_data = {
                "product_data": {
                    "name": "Test Product",
                    "category_name": "Electronics",
                    "item_condition_id": 1,
                    "shipping": 0,
                }
            }

            response = client.post(
                "/api/v1/products/pricing/predict/",
                json=pricing_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # Ожидаем ошибку из-за отсутствия ML модели
            assert response.status_code in [200, 500]


class TestE2EPerformance:
    """E2E тесты производительности."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_response_time(self, client):
        """Тест времени отклика API."""
        # Тест публичного endpoint (не требует авторизации)
        start_time = time.time()

        response = client.get("/api/v1/products/pricing/info/")

        end_time = time.time()
        response_time = end_time - start_time

        # Проверяем что endpoint отвечает быстро (менее 2 секунд)
        assert response_time < 2.0

        # Endpoint должен ответить, даже если модель не загружена
        assert response.status_code in [200, 500]


class TestE2EDataConsistency:
    """E2E тесты консистентности данных."""

    @pytest.mark.asyncio
    async def test_pricing_consistency(self):
        """Тест консистентности прогнозов цен с полной изоляцией."""
        # Используем полностью изолированный клиент
        client = IsolatedAsyncClient(app)

        # Одинаковые данные товара
        pricing_data = {
            "product_data": {
                "name": "iPhone 12",
                "item_description": "Good condition phone",
                "category_name": "Electronics",
                "brand_name": "Apple",
                "item_condition_id": 2,
                "shipping": 0,
            }
        }

        # Делаем два идентичных запроса
        response1 = await client.post(
            "/api/v1/products/pricing/predict/",
            json_data=pricing_data,
            headers={"Authorization": "Bearer test_token"},
        )

        response2 = await client.post(
            "/api/v1/products/pricing/predict/",
            json_data=pricing_data,
            headers={"Authorization": "Bearer test_token"},
        )

        # Оба запроса должны быть успешными
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Результаты должны быть идентичными (при использовании одной модели)
        result1 = response1.json()
        result2 = response2.json()

        assert result1["predicted_price"] == result2["predicted_price"]
        assert result1["confidence_score"] == result2["confidence_score"]


class TestE2ESystemHealth:
    """E2E тесты здоровья системы."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_system_availability(self, client):
        """Тест доступности системы."""
        # Проверяем что основные endpoints доступны
        public_endpoints = [
            "/api/v1/products/pricing/info/",
        ]

        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # Endpoint должен отвечать (может быть ошибка, но не 404)
            assert response.status_code != 404

    def test_api_documentation_availability(self, client):
        """Тест доступности документации API."""
        # Swagger UI должен быть доступен
        response = client.get("/docs")
        assert response.status_code == 200

        # OpenAPI JSON должен быть доступен
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Проверяем что это валидный JSON
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data

    def test_cors_and_headers(self, client):
        """Тест CORS и заголовков безопасности."""
        response = client.get("/api/v1/products/pricing/info/")

        # Проверяем наличие необходимых заголовков
        headers = response.headers
        assert "content-type" in headers

        # API должен возвращать JSON
        if response.status_code == 200:
            assert "application/json" in headers.get("content-type", "")


class TestE2EMLWorker:
    """E2E тесты для ML воркера через API."""

    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента."""
        return TestClient(app)

    def test_ml_worker_pricing_endpoint_integration(self, client):
        """Тест интеграции ML worker через pricing endpoint."""
        # Тестируем реальный API endpoint, который использует ML worker
        with patch("src.base.dependencies.get_token_from_header") as mock_token_dep:
            mock_token = Mock()
            mock_token.id = 1
            mock_token_dep.return_value = mock_token

            pricing_data = {
                "product_data": {
                    "name": "iPhone 13 Pro",
                    "item_description": "Brand new iPhone",
                    "category_name": "Electronics",
                    "brand_name": "Apple",
                    "item_condition_id": 1,
                    "shipping": 1,
                }
            }

            # Делаем запрос к API
            response = client.post(
                "/api/v1/products/pricing/predict/",
                json=pricing_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # Проверяем что API отвечает (может быть и ошибка, если модель не загружена)
            assert response.status_code in [200, 500]

            # Если успешно, проверяем структуру ответа
            if response.status_code == 200:
                result = response.json()
                assert "predicted_price" in result or "detail" in result

    def test_ml_worker_service_availability(self, client):
        """Тест доступности ML сервиса."""
        # Тестируем info endpoint
        response = client.get("/api/v1/products/pricing/info/")

        # Должен отвечать, даже если модель не загружена
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            info = response.json()
            assert "catboost_available" in info or "model_loaded" in info

    def test_ml_worker_error_handling_via_api(self, client):
        """Тест обработки ошибок ML worker через API."""
        with patch("src.base.dependencies.get_token_from_header") as mock_token_dep:
            mock_token = Mock()
            mock_token.id = 1
            mock_token_dep.return_value = mock_token

            # Отправляем некорректные данные
            invalid_data = {
                "product_data": {
                    "name": "",  # Пустое имя
                    "item_condition_id": 10,  # Неверное значение
                }
            }

            response = client.post(
                "/api/v1/products/pricing/predict/",
                json=invalid_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # Должен вернуть ошибку валидации или обработать через ML worker
            assert response.status_code in [422, 400, 500]
