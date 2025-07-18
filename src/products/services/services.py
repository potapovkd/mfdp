"""Сервисы для управления товарами и ценового прогнозирования."""

from base.config import TaskStatus
from products.domain.models import Product, ProductData, Task, PricingResponse
from products.services.unit_of_work import ProductAbstractUnitOfWork
from pricing.pricing_service import PricingService


class ProductService:
    """Сервис для работы с товарами и прогнозами цен."""

    def __init__(self, uow: ProductAbstractUnitOfWork):
        """Инициализация сервиса."""
        self._uow = uow

    async def get_product(self, product_id: int) -> Product:
        """Получение товара."""
        async with self._uow as uow:
            return await uow.products.get(product_id)

    async def add_product(self, user_id: int, product_data: ProductData) -> Product:
        """Создание товара."""
        async with self._uow as uow:
            product = await uow.products.add(user_id, product_data)
            await uow.commit()
            return product

    async def delete_product(self, product_id: int, user_id: int) -> None:
        """Удаление товара."""
        async with self._uow as uow:
            await uow.products.delete(product_id, user_id)
            await uow.commit()

    async def create_pricing_task(
        self,
        product_id: int,
        product_data: ProductData,
        user_id: int,
    ) -> tuple[Product, Task]:
        """Создание задачи прогнозирования цены для товара."""
        async with self._uow as uow:
            product, task = await uow.products.add_pricing_task(
                product_id,
                product_data,
                user_id,
            )
            await uow.commit()
            return product, task

    async def get_user_products(self, user_id: int) -> list[Product]:
        """Получение списка товаров пользователя."""
        async with self._uow as uow:
            return await uow.products.get_user_products(user_id)

    async def update_task(
        self, task_id: int, new_status: TaskStatus | None = None,
        result: str | None = None
    ) -> None:
        """Обновление статуса задачи."""
        async with self._uow as uow:
            await uow.products.update_task_status(task_id, new_status, result)
            await uow.commit()

    async def get_task(self, task_id: int) -> Task:
        """Получение задачи по ID."""
        async with self._uow as uow:
            return await uow.products.get_task(task_id)

    async def get_all_tasks(self) -> list[Task]:
        """Получение всех задач."""
        async with self._uow as uow:
            return await uow.products.get_all_tasks()


# All deprecated service classes removed after migration


class MLPricingService:
    """Сервис для работы с машинным обучением и прогнозированием цен."""

    def __init__(self):
        """Инициализация сервиса."""
        self.pricing_service = PricingService()

    async def get_price_prediction(
        self,
        product_data: ProductData,
    ) -> PricingResponse:
        """Получить прогноз цены для товара."""
        # Конвертируем ProductData в словарь для pricing_service
        product_dict = {
            "name": product_data.name,
            "item_description": product_data.item_description,
            "category_name": product_data.category_name,
            "brand_name": product_data.brand_name,
            "item_condition_id": product_data.item_condition_id,
            "shipping": product_data.shipping
        }

        # Получаем предсказание
        prediction_result = await self.pricing_service.predict_price(product_dict)

        # Конвертируем результат в PricingResponse
        return PricingResponse(
            predicted_price=prediction_result.get("predicted_price", 0.0),
            confidence_score=prediction_result.get("confidence_score", 0.0),
            price_range=prediction_result.get("price_range", {"min": 0.0, "max": 0.0}),
            category_analysis=prediction_result.get("category_analysis", {})
        )

    async def get_only_price_info(
        self,
        product_data: ProductData,
    ) -> dict:
        """Получить только информацию о ценовых характеристиках товара."""
        # Базовая информация без ML предсказания
        category = (
            product_data.category_name.split("/")[0]
            if "/" in product_data.category_name
            else product_data.category_name
        )

        base_info = {
            "category": category,
            "has_brand": product_data.brand_name != "Unknown",
            "has_description": len(product_data.item_description) > 0,
            "condition": product_data.item_condition_id,
            "shipping_type": "seller_pays" if product_data.shipping == 1 else "buyer_pays"
        }

        return base_info

    def get_service_info(self) -> dict:
        """Получение информации о сервисе ML."""
        return self.pricing_service.get_model_info()


# All deprecated service classes removed after migration
