"""Сервисы для работы с пользователями."""

import hashlib
from decimal import Decimal
from typing import Optional

from users.domain.models import (
    BillingRequest,
    BillingResponse,
    PricingTariff,
    User,
    UserCredentials,
)

from .unit_of_work import IUserUnitOfWork


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, uow: IUserUnitOfWork) -> None:
        """Инициализация сервиса."""
        self.uow = uow
        self.tariff: PricingTariff = PricingTariff()

    async def add_user(self, user: UserCredentials) -> None:
        """Добавление пользователя."""
        async with self.uow:
            await self.uow.users.add_user(user)
            await self.uow.commit()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email."""
        async with self.uow:
            return await self.uow.users.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID."""
        async with self.uow:
            return await self.uow.users.get_user_by_id(user_id)

    async def verify_credentials(self, email: str, password: str) -> Optional[User]:
        """Проверка учетных данных пользователя."""
        async with self.uow:
            user = await self.uow.users.get_user_by_email(email)
            if user:
                # Простая проверка пароля (в реальности нужно использовать bcrypt)
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash == user.password:
                    return user
            return None

    async def get_user_balance(self, user_id: int) -> Optional[Decimal]:
        """Получение баланса пользователя."""
        async with self.uow:
            user = await self.uow.users.get_user_by_id(user_id)
            if user is None:
                return None
            return Decimal(str(user.balance))

    async def update_user_balance(self, user_id: int, amount: Decimal) -> bool:
        """Обновление баланса пользователя."""
        async with self.uow:
            success = await self.uow.users.update_balance(user_id, amount)
            if success:
                await self.uow.commit()
            return bool(success)

    async def charge_user(self, billing_request: BillingRequest) -> BillingResponse:
        """Списание средств с баланса пользователя."""
        async with self.uow:
            user = await self.uow.users.get_user_by_id(billing_request.user_id)
            if not user:
                return BillingResponse(
                    success=False,
                    new_balance=Decimal("0.00"),
                    charged_amount=Decimal("0.00"),
                    message="Пользователь не найден",
                )

            user_balance = Decimal(str(user.balance))
            if user_balance < billing_request.amount:
                return BillingResponse(
                    success=False,
                    new_balance=user_balance,
                    charged_amount=Decimal("0.00"),
                    message=f"Недостаточно средств. Требуется: ${billing_request.amount}, доступно: ${user_balance}",
                )

            new_balance = user_balance - billing_request.amount
            success = await self.uow.users.update_balance(
                billing_request.user_id, new_balance
            )

            if success:
                await self.uow.commit()
                return BillingResponse(
                    success=True,
                    new_balance=new_balance,
                    charged_amount=billing_request.amount,
                    message=f"Списано ${billing_request.amount} за {billing_request.description}",
                )

            return BillingResponse(
                success=False,
                new_balance=user_balance,
                charged_amount=Decimal("0.00"),
                message="Ошибка при списании средств",
            )

    def calculate_pricing_cost(self, items_count: int) -> Decimal:
        """Расчет стоимости прогнозирования для указанного количества товаров."""
        if items_count <= 0:
            return Decimal("0.00")

        if items_count > self.tariff.max_items_per_request:
            raise ValueError(
                f"Превышен лимит товаров в запросе: {items_count} > {self.tariff.max_items_per_request}"
            )

        base_cost = Decimal(str(self.tariff.single_item_price)) * items_count

        # Применяем скидку для bulk запросов
        if items_count >= self.tariff.bulk_discount_threshold:
            discount_percent = Decimal(
                str(self.tariff.bulk_discount_percent)
            ) / Decimal("100")
            discount = base_cost * discount_percent
            return base_cost - discount

        return base_cost

    def get_tariff_info(self) -> PricingTariff:
        """Получение информации о тарифах."""
        return self.tariff
