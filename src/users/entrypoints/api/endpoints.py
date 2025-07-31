"""API endpoints для работы с пользователями."""

import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from base.data_structures import JWTPayloadDTO
from base.dependencies import get_token_from_header
from base.exceptions import AuthenticationError, DatabaseError
from users.domain.models import (
    UserCreateDTO,
    UserLoginDTO,
    UserLoginResponse,
)
from users.entrypoints.api.dependencies import UserServiceDependency

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreateDTO, service: UserServiceDependency):
    """Регистрация нового пользователя."""
    try:
        await service.add_user(user)
        return {"message": "Пользователь успешно зарегистрирован"}
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/", status_code=status.HTTP_200_OK)
async def authenticate_user(
    user: UserLoginDTO, service: UserServiceDependency
) -> UserLoginResponse:
    """Аутентификация пользователя."""
    try:
        token = await service.authenticate_user(user)
        return UserLoginResponse(access_token=token, token_type="bearer")
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tariffs/")
async def get_tariffs():
    """Получение информации о тарифе."""
    try:
        # Возвращаем базовый тариф как единый объект
        tariff = {
            "single_item_price": 5.0,
            "bulk_discount_threshold": 10,
            "bulk_discount_percent": 20,
            "max_items_per_request": 100,
            "description": "Тариф для обработки товаров",
        }
        return tariff
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения тарифа: {str(e)}"
        )


@router.post("/calculate-cost/")
async def calculate_cost(
    items_count: int = Query(..., description="Количество товаров")
):
    """Расчет стоимости обработки товаров."""
    try:
        single_price = 5.0
        bulk_threshold = 10
        discount_percent = 20
        max_items = 100

        # Валидация
        if items_count < 0:
            # Возвращаем нулевую стоимость для отрицательных значений
            return {
                "items_count": str(items_count),
                "cost": "0.00",
                "cost_per_item": "0.00",
            }

        if items_count > max_items:
            raise HTTPException(
                status_code=400, detail=f"Превышен лимит товаров: {max_items}"
            )

        # Расчет стоимости
        base_cost = single_price * items_count

        if items_count >= bulk_threshold:
            # Применяем скидку
            discount = base_cost * (discount_percent / 100)
            final_cost = base_cost - discount
        else:
            final_cost = base_cost

        cost_per_item = final_cost / items_count if items_count > 0 else 0

        return {
            "items_count": str(items_count),
            "cost": f"{final_cost:.2f}",
            "cost_per_item": f"{cost_per_item:.2f}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка расчета стоимости: {str(e)}"
        )


@router.get("/calculate-cost/")
async def calculate_cost_get(
    requests_count: int = Query(..., description="Количество запросов"),
    tariff_id: int = Query(1, description="ID тарифа"),
):
    """Расчет стоимости запросов (GET версия для совместимости)."""
    try:
        tariffs = {1: Decimal("0.01"), 2: Decimal("0.005"), 3: Decimal("0.001")}

        price_per_request = tariffs.get(tariff_id, Decimal("0.01"))
        total_cost = price_per_request * requests_count

        return {
            "requests_count": requests_count,
            "tariff_id": tariff_id,
            "price_per_request": float(price_per_request),
            "total_cost": float(total_cost),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка расчета стоимости: {str(e)}"
        )


@router.get("/balance/")
async def get_balance(
    token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
    service: UserServiceDependency,
):
    """Получение баланса пользователя."""
    try:
        balance = await service.get_user_balance(token.id)
        if balance is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return {"balance": float(balance)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения баланса: {str(e)}"
        )


@router.post("/balance/add/")
async def add_balance(
    token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
    service: UserServiceDependency,
    amount: float = Query(..., description="Сумма для пополнения"),
):
    """Пополнение баланса пользователя."""
    try:
        current_balance = await service.get_user_balance(token.id)
        if current_balance is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        new_balance = current_balance + Decimal(str(amount))
        success = await service.update_user_balance(token.id, new_balance)

        if not success:
            raise HTTPException(status_code=500, detail="Не удалось обновить баланс")

        return {
            "message": f"Баланс пополнен на ${amount}",
            "balance": float(new_balance),
            "added": amount,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка пополнения баланса: {str(e)}"
        )


@router.get("/products/template/")
async def get_products_template():
    """Получение шаблона Excel файла для загрузки товаров."""
    try:
        # Создаем DataFrame с примером данных
        template_data = {
            "name": ["iPhone 13 Pro 128GB", "Nike Air Max 270"],
            "item_description": [
                "Отличное состояние, полный комплект",
                "Новые кроссовки, размер 42",
            ],
            "category_name": ["Electronics", "Fashion"],
            "brand_name": ["Apple", "Nike"],
            "item_condition_id": [2, 1],
            "shipping": [1, 0],
        }

        df = pd.DataFrame(template_data)

        # Создаем Excel файл в памяти с подавлением warnings
        output = io.BytesIO()

        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Сначала создаем основной лист с данными
                df.to_excel(writer, sheet_name="Products", index=False)

                # Добавляем лист с инструкциями
                instructions = pd.DataFrame(
                    {
                        "Поле": [
                            "name",
                            "item_description",
                            "category_name",
                            "brand_name",
                            "item_condition_id",
                            "shipping",
                        ],
                        "Описание": [
                            "Название товара (обязательно)",
                            "Описание товара (необязательно)",
                            "Категория товара (обязательно)",
                            "Бренд товара (необязательно, по умолчанию 'Unknown')",
                            "Состояние товара: 1=новый, 2=отличное, 3=хорошее, 4=удовлетворительное, 5=плохое",
                            "Доставка: 0=покупатель платит, 1=продавец платит",
                        ],
                        "Пример": [
                            "iPhone 13 Pro 128GB",
                            "Отличное состояние, полный комплект",
                            "Electronics",
                            "Apple",
                            "2",
                            "1",
                        ],
                    }
                )
                instructions.to_excel(writer, sheet_name="Instructions", index=False)

                # Устанавливаем современные metadata для workbook
                workbook = writer.book
                workbook.properties.created = datetime.now(timezone.utc)
                workbook.properties.modified = datetime.now(timezone.utc)

                # Убеждаемся что хотя бы один лист активен (используем индекс)
                if len(workbook.sheetnames) > 0:
                    workbook.active = 0  # Первый лист

        output.seek(0)

        # Возвращаем файл как StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=products_template.xlsx"
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания шаблона: {str(e)}"
        )
