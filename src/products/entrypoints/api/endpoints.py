"""API эндпойнты для работы с товарами и ценообразованием."""

import logging
from fastapi import APIRouter, HTTPException

# NOTE: Use direct dependency function instead of precomputed TokenDependency
from base.dependencies import get_token_from_header
from typing import Annotated
from fastapi import Depends
from products.domain.models import (
    Product, ProductData, PricingRequest, PricingResponse
)
from products.entrypoints.api.dependencies import ProductServiceDependency
from products.services.services import MLPricingService
from base.data_structures import JWTPayloadDTO

logger = logging.getLogger(__name__)

router = APIRouter()

# Инициализируем ML сервис
ml_service = MLPricingService()


@router.get("/", response_model=list[Product], status_code=200)
async def get_product_list(
    service: ProductServiceDependency,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
):
    """Получение списка товаров пользователя."""
    return await service.get_user_products(data_from_token.id)


@router.post("/", response_model=Product, status_code=201)
async def create_product(
    service: ProductServiceDependency,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
    product_data: ProductData,
) -> Product:
    """Создание товара."""
    return await service.add_product(data_from_token.id, product_data)


@router.get("/{product_id}/", response_model=Product, status_code=200)
async def get_product(
    product_id: int,
    service: ProductServiceDependency,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
):
    """Получение информации о товаре."""
    return await service.get_product(product_id)


@router.post("/pricing/predict/", response_model=PricingResponse)
async def predict_price_direct(
    pricing_request: PricingRequest,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
):
    """Прямое прогнозирование цены товара."""
    try:
        # Получаем прогноз цены без проверки баланса и списания средств
        pricing_response = await ml_service.get_price_prediction(
            pricing_request.product_data
        )
        return pricing_response

    except Exception as e:
        logger.error(f"Unexpected error in price prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing/info/", response_model=dict)
async def get_pricing_info():
    """Получение информации о сервисе ценообразования."""
    return ml_service.get_service_info()


@router.post("/pricing/analyze/", response_model=dict)
async def analyze_product_pricing(
    pricing_request: PricingRequest,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
):
    """Анализ ценовых характеристик товара без ML прогноза."""
    try:
        return await ml_service.get_only_price_info(pricing_request.product_data)
    except Exception as e:
        logger.error(f"Error in product analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
