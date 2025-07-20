"""API эндпойнты для работы с товарами и ценообразованием."""

import logging
import pandas as pd
import io
import tempfile
import os
from decimal import Decimal
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from typing import Annotated, List

# NOTE: Use direct dependency function instead of precomputed TokenDependency
from base.dependencies import get_token_from_header
from base.data_structures import JWTPayloadDTO
from products.domain.models import (
    Product, ProductData, PricingRequest, PricingResponse
)
from products.entrypoints.api.dependencies import ProductServiceDependency
from products.services.services import MLPricingService
from users.services.services import UserService
from users.services.unit_of_work import PostgreSQLUserUnitOfWork
from base.orm import get_session_factory
from users.domain.models import BillingRequest, BillingResponse

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


@router.post("/upload-excel/", status_code=201)
async def upload_products_excel(
    file: UploadFile,
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
    service: ProductServiceDependency,
):
    """Загрузка товаров из Excel файла."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")
    
    try:
        # Читаем Excel файл
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), sheet_name='Products')
        
        # Проверяем обязательные колонки
        required_columns = ['name', 'category_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Обрабатываем каждую строку
        created_products = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Создаем ProductData из строки
                product_data = ProductData(
                    name=str(row['name']).strip(),
                    item_description=str(row.get('item_description', '')).strip(),
                    category_name=str(row['category_name']).strip(),
                    brand_name=str(row.get('brand_name', 'Unknown')).strip(),
                    item_condition_id=int(row.get('item_condition_id', 1)),
                    shipping=int(row.get('shipping', 0))
                )
                
                # Добавляем товар
                product = await service.add_product(data_from_token.id, product_data)
                created_products.append(product)
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "message": f"Successfully created {len(created_products)} products",
            "created_count": len(created_products),
            "errors": errors,
            "products": [{"id": p.id, "name": p.name} for p in created_products]
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


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


@router.post("/pricing/predict-multiple/", status_code=200)
async def predict_price_multiple(
    product_ids: List[int],
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
    service: ProductServiceDependency,
):
    """Прогнозирование цен для множества товаров пользователя."""
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    
    if len(product_ids) > 100:  # Лимит на количество товаров
        raise HTTPException(status_code=400, detail="Too many products (max 100)")
    
    try:
        # Получаем товары пользователя
        user_products = await service.get_user_products(data_from_token.id)
        user_product_ids = {p.id for p in user_products}
        
        # Проверяем, что все товары принадлежат пользователю
        invalid_ids = [pid for pid in product_ids if pid not in user_product_ids]
        if invalid_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Products not found or not owned by user: {invalid_ids}"
            )
        
        # Проверяем баланс и списываем средства
        session_factory = get_session_factory()
        user_uow = PostgreSQLUserUnitOfWork(session_factory)
        user_service = UserService(user_uow)
        
        cost = user_service.calculate_pricing_cost(len(product_ids))
        current_balance = await user_service.get_user_balance(data_from_token.id)
        
        if current_balance < cost:
            raise HTTPException(
                status_code=402, 
                detail=f"Insufficient balance. Required: ${cost}, Available: ${current_balance}"
            )
        
        # Списываем средства
        billing_request = BillingRequest(
            user_id=data_from_token.id,
            amount=cost,
            description=f"Price prediction for {len(product_ids)} products",
            items_count=len(product_ids)
        )
        
        billing_response = await user_service.charge_user(billing_request)
        if not billing_response.success:
            raise HTTPException(status_code=500, detail=billing_response.message)
        
        # Получаем прогнозы для всех товаров
        results = []
        for product_id in product_ids:
            product = next(p for p in user_products if p.id == product_id)
            
            product_data = ProductData(
                name=product.name,
                item_description=product.item_description,
                category_name=product.category_name,
                brand_name=product.brand_name,
                item_condition_id=product.item_condition_id,
                shipping=product.shipping
            )
            
            prediction = await ml_service.get_price_prediction(product_data)
            results.append({
                "product_id": product_id,
                "product_name": product.name,
                "prediction": prediction
            })
        
        return {
            "message": f"Successfully predicted prices for {len(product_ids)} products",
            "charged_amount": str(cost),
            "new_balance": str(billing_response.new_balance),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multiple price prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing/export-results/", status_code=200)
async def export_pricing_results(
    results: List[dict],
    data_from_token: Annotated[JWTPayloadDTO, Depends(get_token_from_header)],
):
    """Экспорт результатов прогнозирования в Excel файл."""
    try:
        # Создаем DataFrame с результатами
        export_data = []
        for result in results:
            try:
                # Получаем данные из структуры, возвращаемой predict-multiple
                product_id = result.get("product_id", "")
                product_name = result.get("product_name", "")
                prediction = result.get("prediction", {})
                
                # Извлекаем данные из prediction с проверкой типов
                predicted_price = prediction.get("predicted_price", 0)
                if isinstance(predicted_price, str):
                    try:
                        predicted_price = float(predicted_price)
                    except (ValueError, TypeError):
                        predicted_price = 0
                
                confidence_score = prediction.get("confidence_score", 0)
                if isinstance(confidence_score, str):
                    try:
                        confidence_score = float(confidence_score)
                    except (ValueError, TypeError):
                        confidence_score = 0
                
                price_range = prediction.get("price_range", {})
                category_analysis = prediction.get("category_analysis", {})
                
                export_data.append({
                    "Product ID": str(product_id),
                    "Product Name": str(product_name),
                    "Predicted Price": f"${predicted_price:.2f}" if predicted_price else "$0.00",
                    "Confidence Score": f"{confidence_score:.1%}" if confidence_score else "0%",
                    "Price Range Min": f"${price_range.get('min', 0):.2f}" if price_range.get('min') else "$0.00",
                    "Price Range Max": f"${price_range.get('max', 0):.2f}" if price_range.get('max') else "$0.00",
                    "Category Analysis": str(category_analysis.get("recommendation", ""))
                })
            except Exception as e:
                logger.error(f"Error processing result for export: {e}")
                # Добавляем пустую строку в случае ошибки
                export_data.append({
                    "Product ID": "Error",
                    "Product Name": "Error",
                    "Predicted Price": "$0.00",
                    "Confidence Score": "0%",
                    "Price Range Min": "$0.00",
                    "Price Range Max": "$0.00",
                    "Category Analysis": "Error processing data"
                })
        
        df = pd.DataFrame(export_data)
        
        # Создаем Excel файл в памяти
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Price Predictions', index=False)
            
            # Добавляем сводку
            try:
                # Извлекаем числовые значения цен для расчета среднего
                prices = []
                for row in export_data:
                    price_str = row.get("Predicted Price", "$0.00")
                    if price_str.startswith("$"):
                        try:
                            price = float(price_str.replace("$", ""))
                            prices.append(price)
                        except (ValueError, TypeError):
                            continue
                
                avg_price = sum(prices) / len(prices) if prices else 0
                
                summary_data = {
                    "Metric": ["Total Products", "Average Price", "Total Cost"],
                    "Value": [
                        len(results),
                        f"${avg_price:.2f}",
                        f"${len(results) * 5.00:.2f}"  # $5 per prediction
                    ]
                }
            except Exception as e:
                logger.error(f"Error calculating summary: {e}")
                summary_data = {
                    "Metric": ["Total Products", "Average Price", "Total Cost"],
                    "Value": [
                        len(results),
                        "$0.00",
                        f"${len(results) * 5.00:.2f}"
                    ]
                }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(output.getvalue())
            tmp_file_path = tmp_file.name
        
        # Создаем функцию для очистки файла после отправки
        def cleanup_file():
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp file {tmp_file_path}: {e}")
        
        return FileResponse(
            tmp_file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"price_predictions_{data_from_token.id}.xlsx",
            background=cleanup_file
        )
        
    except Exception as e:
        logger.error(f"Error exporting results: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting results: {str(e)}")


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
