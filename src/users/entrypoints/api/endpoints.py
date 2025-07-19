"""API эндпойнты для работы с пользователями."""

from decimal import Decimal
from fastapi import APIRouter, status, HTTPException, UploadFile, File, Depends
from fastapi.responses import Response, FileResponse
from typing import Annotated

from base.config import get_settings
from base.dependencies import (
    UserServiceDependency,
    get_token_from_header,
)
from base.utils import JWTHandler
from base.data_structures import JWTPayloadDTO
from users.domain.models import UserCredentials, BillingRequest, PricingTariff

settings = get_settings()
router = APIRouter()


@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
async def register_user(
    user: UserCredentials, service: UserServiceDependency
) -> Response:
    """Регистрация пользователя."""
    await service.add_user(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/auth/", status_code=status.HTTP_200_OK)
async def login_user(
    user: UserCredentials, service: UserServiceDependency
) -> dict[str, str]:
    """Авторизация пользователя."""
    verified_user = await service.verify_credentials(user.email, user.password)
    if not verified_user:
        return {"error": "Invalid credentials"}

    jwt_handler = JWTHandler(settings.secret_key)
    access_token = jwt_handler.encode_token(
        payload=JWTPayloadDTO(id=verified_user.id),
        expires_minutes=settings.access_token_expires_minutes,
    )

    return {"access_token": access_token.access_token}


@router.get("/balance/", status_code=status.HTTP_200_OK)
async def get_user_balance(
    service: UserServiceDependency,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
) -> dict[str, str]:
    """Получение баланса пользователя."""
    balance = await service.get_user_balance(data_from_token.id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"balance": str(balance)}


@router.post("/balance/add/", status_code=status.HTTP_200_OK)
async def add_balance(
    amount: Decimal,
    service: UserServiceDependency,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
) -> dict[str, str]:
    """Пополнение баланса пользователя."""
    current_balance = await service.get_user_balance(data_from_token.id)
    if current_balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_balance = current_balance + amount
    success = await service.update_user_balance(data_from_token.id, new_balance)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update balance")
    
    return {"balance": str(new_balance), "message": f"Added ${amount} to balance"}


@router.get("/tariffs/", status_code=status.HTTP_200_OK)
async def get_pricing_tariffs(
    service: UserServiceDependency,
) -> PricingTariff:
    """Получение информации о тарифах."""
    return service.get_tariff_info()


@router.post("/calculate-cost/", status_code=status.HTTP_200_OK)
async def calculate_pricing_cost(
    items_count: int,
    service: UserServiceDependency,
) -> dict[str, str]:
    """Расчет стоимости прогнозирования для указанного количества товаров."""
    try:
        cost = service.calculate_pricing_cost(items_count)
        return {
            "items_count": str(items_count),
            "cost": str(cost),
            "cost_per_item": str(cost / items_count) if items_count > 0 else "0.00"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/products/template/", status_code=status.HTTP_200_OK)
async def get_products_template() -> FileResponse:
    """Получение шаблона Excel файла для загрузки товаров."""
    # Создаем шаблон Excel файла
    import pandas as pd
    import io
    
    # Создаем DataFrame с примером данных
    template_data = {
        "name": ["iPhone 13 Pro 128GB", "Nike Air Max 270"],
        "item_description": ["Отличное состояние, полный комплект", "Новые кроссовки, размер 42"],
        "category_name": ["Electronics", "Fashion"],
        "brand_name": ["Apple", "Nike"],
        "item_condition_id": [2, 1],
        "shipping": [1, 0]
    }
    
    df = pd.DataFrame(template_data)
    
    # Создаем Excel файл в памяти
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        
        # Добавляем лист с инструкциями
        instructions = pd.DataFrame({
            "Поле": ["name", "item_description", "category_name", "brand_name", "item_condition_id", "shipping"],
            "Описание": [
                "Название товара (обязательно)",
                "Описание товара (необязательно)",
                "Категория товара (обязательно)",
                "Бренд товара (необязательно, по умолчанию 'Unknown')",
                "Состояние товара: 1=новый, 2=отличное, 3=хорошее, 4=удовлетворительное, 5=плохое",
                "Доставка: 0=покупатель платит, 1=продавец платит"
            ],
            "Пример": [
                "iPhone 13 Pro 128GB",
                "Отличное состояние, полный комплект",
                "Electronics",
                "Apple",
                "2",
                "1"
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_template.xlsx"}
    )
