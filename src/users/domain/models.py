"""Модели пользователей для системы ценовой оптимизации."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCredentials(BaseModel):
    """Модель учетных данных пользователя."""

    email: EmailStr
    password: str


class UserMetadata(BaseModel):
    """Модель метаданных пользователя."""

    id: int
    created_at: datetime
    balance: Decimal = Decimal("0.00")


class User(UserCredentials, UserMetadata):
    """Модель пользователя."""


class BillingRequest(BaseModel):
    """Модель запроса на списание средств."""
    
    user_id: int
    amount: Decimal
    description: str
    items_count: int = 1


class BillingResponse(BaseModel):
    """Модель ответа на списание средств."""
    
    success: bool
    new_balance: Decimal
    charged_amount: Decimal
    message: str


class PricingTariff(BaseModel):
    """Модель тарифа для прогнозирования цен."""
    
    single_item_price: Decimal = Decimal("5.00")
    bulk_discount_threshold: int = 10  # Скидка при количестве товаров >= 10
    bulk_discount_percent: int = 20    # 20% скидка для bulk запросов
    max_items_per_request: int = 100   # Максимум товаров в одном запросе
