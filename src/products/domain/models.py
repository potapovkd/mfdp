"""Доменные модели для товаров и ценообразования."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from base.config import TaskStatus


class ProductData(BaseModel):
    """Модель данных товара для ценового прогноза."""

    name: str
    item_description: str = ""
    category_name: str
    brand_name: str = "Unknown"
    item_condition_id: int  # 1-5, где 1=новый, 5=плохое состояние
    shipping: int  # 0=покупатель платит, 1=продавец платит

    from pydantic import validator  # noqa: WPS433

    @validator("name")
    def name_must_not_be_empty(cls, v):  # noqa: D401, N805
        if not v.strip():
            raise ValueError("name must not be empty")
        return v

    @validator("item_condition_id")
    def item_condition_in_range(cls, v):  # noqa: D401, N805
        if v not in {1, 2, 3, 4, 5}:
            raise ValueError("item_condition_id must be between 1 and 5")
        return v


class Product(ProductData):
    """Модель товара с метаданными."""

    id: int
    user_id: int
    created_at: datetime
    current_price: Optional[float] = None


class PricePrediction(BaseModel):
    """Модель прогноза цены."""

    id: int
    product_id: int
    predicted_price: float
    confidence_score: float
    price_range: dict[str, float]  # {"min": ..., "max": ...}
    category_analysis: dict[str, str]  # аналитика по категории


class PricingRequest(BaseModel):
    """Запрос на прогнозирование цены."""

    product_data: ProductData


class PricingResponse(BaseModel):
    """Ответ прогнозирования цены."""

    predicted_price: float
    confidence_score: float
    price_range: dict[str, float]
    category_analysis: dict[str, str]


class Task(BaseModel):
    """Модель задачи ML."""

    id: int
    product_id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: str


class TaskCreate(BaseModel):
    """DTO для создания задачи."""

    id: int
    product_id: int
    product_data: ProductData
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: str

    def to_queue_message(self):
        return {
            "task_id": self.id,
            "product_data": self.product_data.model_dump(),
        }


class TaskUpdate(BaseModel):
    """DTO для обновления существующей ML задачи"""

    status: Optional[TaskStatus]
    result: Optional[str]


# All deprecated models removed after migration
