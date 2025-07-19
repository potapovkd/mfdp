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

        # Анализ текстовых признаков
        name_length = len(product_data.name)
        description_length = len(product_data.item_description)
        name_words = len(product_data.name.split())
        description_words = len(product_data.item_description.split()) if product_data.item_description else 0

        # Анализ состояния товара
        condition_map = {
            1: "Новый",
            2: "Отличное состояние", 
            3: "Хорошее состояние",
            4: "Удовлетворительное состояние",
            5: "Плохое состояние"
        }
        condition_text = condition_map.get(product_data.item_condition_id, "Неизвестно")

        # Рекомендации на основе анализа
        recommendations = []
        
        if name_length < 10:
            recommendations.append("Добавьте более подробное название товара")
        elif name_length > 100:
            recommendations.append("Название слишком длинное, сделайте его более лаконичным")
            
        if description_length == 0:
            recommendations.append("Добавьте описание товара для лучшего понимания")
        elif description_length < 50:
            recommendations.append("Расширьте описание товара")
        elif description_length > 500:
            recommendations.append("Описание слишком длинное, сократите его")
            
        if product_data.brand_name == "Unknown":
            recommendations.append("Укажите бренд товара, если это возможно")
            
        if product_data.item_condition_id == 5:
            recommendations.append("Состояние товара может значительно снизить цену")
        elif product_data.item_condition_id == 1:
            recommendations.append("Новое состояние товара - это преимущество для ценообразования")
            
        if product_data.shipping == 0:
            recommendations.append("Бесплатная доставка может повысить привлекательность товара")

        # Анализ категории
        category_analysis = self._analyze_category(category)
        
        return {
            "features": {
                "name_length": name_length,
                "description_length": description_length,
                "name_words": name_words,
                "description_words": description_words,
                "category": category,
                "brand": product_data.brand_name,
                "condition": product_data.item_condition_id,
                "condition_text": condition_text,
                "shipping": product_data.shipping,
                "has_brand": product_data.brand_name != "Unknown",
                "has_description": len(product_data.item_description) > 0
            },
            "recommendations": recommendations,
            "category_analysis": category_analysis
        }

    def _analyze_category(self, category: str) -> dict:
        """Анализ категории товара."""
        category_insights = {
            "Electronics": {
                "price_range": "Широкий диапазон цен",
                "key_factors": ["Модель", "Состояние", "Комплектация"],
                "tips": "Укажите точную модель и состояние техники"
            },
            "Fashion": {
                "price_range": "Средний-высокий диапазон",
                "key_factors": ["Бренд", "Размер", "Сезонность"],
                "tips": "Важны бренд и актуальность сезона"
            },
            "Home & Garden": {
                "price_range": "Средний диапазон цен",
                "key_factors": ["Состояние", "Размер", "Материал"],
                "tips": "Детально опишите состояние и материалы"
            },
            "Books": {
                "price_range": "Низкий-средний диапазон",
                "key_factors": ["Издание", "Состояние", "Редкость"],
                "tips": "Укажите год издания и состояние"
            },
            "Sports & Outdoors": {
                "price_range": "Средний диапазон",
                "key_factors": ["Бренд", "Состояние", "Специализация"],
                "tips": "Важны бренд и специализация"
            },
            "Beauty": {
                "price_range": "Средний диапазон",
                "key_factors": ["Бренд", "Срок годности", "Объем"],
                "tips": "Укажите срок годности и объем"
            },
            "Kids & Baby": {
                "price_range": "Средний диапазон",
                "key_factors": ["Возраст", "Состояние", "Безопасность"],
                "tips": "Важны возрастная группа и безопасность"
            },
            "Automotive": {
                "price_range": "Высокий диапазон цен",
                "key_factors": ["Модель", "Год", "Состояние"],
                "tips": "Детально опишите модель и год выпуска"
            }
        }
        
        return category_insights.get(category, {
            "price_range": "Различный диапазон",
            "key_factors": ["Качество", "Состояние", "Бренд"],
            "tips": "Укажите основные характеристики товара"
        })

    def get_service_info(self) -> dict:
        """Получение информации о сервисе ML."""
        return self.pricing_service.get_model_info()


# All deprecated service classes removed after migration
