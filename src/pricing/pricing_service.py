"""Сервис для работы с прогнозированием цен товаров.
Заменяет LLMService из оригинальной архитектуры.
"""

import pickle
import re
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

try:
    from catboost import CatBoostRegressor

    catboost_available = True
except ImportError:
    catboost_available = False

from base.config import (
    get_confidence_threshold,
    get_max_price_limit,
    get_min_price_limit,
    get_model_path,
    get_preprocessing_path,
)


class PricingService:
    """Сервис для прогнозирования цен товаров."""

    def __init__(self):
        """Инициализация сервиса."""
        self.model_path = Path(get_model_path())
        self.preprocessing_path = Path(get_preprocessing_path())
        self.confidence_threshold = get_confidence_threshold()
        self.max_price = get_max_price_limit()
        self.min_price = get_min_price_limit()

        self.model = None
        self.preprocessing_pipeline = None
        self._load_model_and_pipeline()

    def _load_model_and_pipeline(self) -> None:
        """Загрузка обученной модели и pipeline предобработки."""
        # Загружаем модель
        if self.model_path.exists() and catboost_available:
            try:
                self.model = CatBoostRegressor()
                self.model.load_model(str(self.model_path))
                print(f"✅ Модель загружена из {self.model_path}")
            except Exception as e:
                print(f"❌ Ошибка загрузки модели: {e}")
                self.model = None
        else:
            print(
                f"❌ Модель не найдена по пути {self.model_path} или CatBoost недоступен"
            )
            self.model = None

        # Загружаем pipeline предобработки
        if self.preprocessing_path.exists():
            try:
                with open(self.preprocessing_path, "rb") as f:
                    self.preprocessing_pipeline = pickle.load(f)  # nosec B301
                print(f"✅ Pipeline предобработки загружен из {self.preprocessing_path}")
            except Exception as e:
                print(f"❌ Ошибка загрузки pipeline: {e}")
                self.preprocessing_pipeline = None
        else:
            print(f"❌ Pipeline не найден по пути {self.preprocessing_path}")
            self.preprocessing_pipeline = None

    def _preprocess_single_item(
        self, product_data: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """Предобработка одного товара для предсказания."""
        if self.preprocessing_pipeline is None:
            raise ValueError("Pipeline предобработки не загружен")

        try:
            # Создаем DataFrame с одной записью
            df = pd.DataFrame([product_data])

            # Заполняем пропуски как в обучении
            df["category_name"] = df["category_name"].fillna("Other")
            df["brand_name"] = df["brand_name"].fillna("Unknown")
            df["item_description"] = df["item_description"].fillna("")

            # Создаем те же признаки что и при обучении
            df["desc_len"] = df["item_description"].str.len()
            df["name_len"] = df["name"].str.len()
            df["has_brand"] = (df["brand_name"] != "Unknown").astype(int)
            df["has_description"] = (df["item_description"] != "").astype(int)

            # Разбиение категории на уровни (упрощенное)
            df["cat_main"] = df["category_name"].apply(
                lambda x: x.split("/")[0] if "/" in x else x
            )
            df["cat_sub"] = df["category_name"].apply(
                lambda x: x.split("/")[1]
                if "/" in x and len(x.split("/")) > 1
                else "None"
            )

            # Текстовые признаки
            df["desc_words"] = df["item_description"].apply(
                lambda x: len(re.findall(r"\w+", x))
            )
            df["name_words"] = df["name"].apply(lambda x: len(re.findall(r"\w+", x)))

            # TF-IDF преобразования (упрощенные - 10 признаков)
            tfidf_name_features = (
                self.preprocessing_pipeline["tfidf_name"]
                .transform(df["name"])
                .toarray()
            )
            tfidf_desc_features = (
                self.preprocessing_pipeline["tfidf_desc"]
                .transform(df["item_description"])
                .toarray()
            )

            tfidf_name_df = pd.DataFrame(
                tfidf_name_features, columns=[f"name_tfidf_{i}" for i in range(10)]
            )
            tfidf_desc_df = pd.DataFrame(
                tfidf_desc_features, columns=[f"desc_tfidf_{i}" for i in range(10)]
            )

            # Кодирование категориальных признаков
            df["brand_enc"] = self._safe_transform(
                self.preprocessing_pipeline["le_brand"], df["brand_name"]
            )
            df["cat_main_enc"] = self._safe_transform(
                self.preprocessing_pipeline["le_cat_main"], df["cat_main"]
            )
            df["cat_sub_enc"] = self._safe_transform(
                self.preprocessing_pipeline["le_cat_sub"], df["cat_sub"]
            )

            # Собираем финальные признаки (упрощенные)
            feature_cols = [
                "item_condition_id",
                "shipping",
                "brand_enc",
                "cat_main_enc",
                "cat_sub_enc",
                "desc_len",
                "name_len",
                "has_brand",
                "has_description",
                "desc_words",
                "name_words",
            ]

            X_base = df[feature_cols].reset_index(drop=True)
            X = pd.concat([X_base, tfidf_name_df, tfidf_desc_df], axis=1)

            return X

        except Exception as e:
            print(f"Ошибка предобработки товара: {e}")
            return None

    def _safe_transform(self, encoder: LabelEncoder, values: pd.Series) -> pd.Series:
        """Безопасное преобразование с обработкой неизвестных категорий."""
        try:
            return encoder.transform(values)
        except ValueError:
            # Если встретили неизвестную категорию, заменяем на наиболее частую
            known_classes = set(encoder.classes_)
            values_safe = values.apply(
                lambda x: x if x in known_classes else encoder.classes_[0]
            )
            return encoder.transform(values_safe)

    def _calculate_confidence_score(
        self, prediction: float, features: pd.DataFrame
    ) -> float:
        """Расчет оценки уверенности модели в предсказании."""
        # Простая эвристика уверенности на основе:
        # 1. Наличия бренда
        # 2. Полноты описания
        # 3. Детальности категории

        confidence = 0.5  # базовая уверенность

        # Бонус за наличие бренда
        if features["has_brand"].iloc[0] == 1:
            confidence += 0.15

        # Бонус за наличие описания
        if features["has_description"].iloc[0] == 1:
            confidence += 0.1

        # Бонус за длину описания
        desc_len = features["desc_len"].iloc[0]
        if desc_len > 50:
            confidence += 0.1
        elif desc_len > 20:
            confidence += 0.05

        # Штраф за экстремальные предсказания
        if prediction < 5 or prediction > 1000:
            confidence -= 0.2

        return max(0.1, min(1.0, confidence))

    def _get_category_analysis(
        self, product_data: Dict[str, Any], prediction: float
    ) -> Dict[str, str]:
        """Анализ категории товара для предоставления рекомендаций."""
        category = product_data.get("category_name", "Unknown")
        main_cat = category.split("/")[0] if "/" in category else category

        analysis = {"category": main_cat, "recommendation": "", "market_position": ""}

        # Простая логика анализа по категориям (можно расширить)
        if prediction < 10:
            analysis["market_position"] = "Низкий ценовой сегмент"
            analysis[
                "recommendation"
            ] = "Рассмотрите возможность повышения качества описания"
        elif prediction < 50:
            analysis["market_position"] = "Средний ценовой сегмент"
            analysis["recommendation"] = "Хорошее соотношение цена-качество"
        else:
            analysis["market_position"] = "Премиум сегмент"
            analysis[
                "recommendation"
            ] = "Убедитесь в высоком качестве товара и детальном описании"

        # Специфичные рекомендации по категориям
        if "Electronics" in main_cat:
            analysis[
                "recommendation"
            ] += ". Для электроники важно указать точную модель и состояние"
        elif "Beauty" in main_cat:
            analysis[
                "recommendation"
            ] += ". В косметике важны срок годности и подлинность бренда"

        return analysis

    async def predict_price(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Главный метод для прогнозирования цены товара."""
        if self.model is None:
            return {
                "error": "Модель не загружена",
                "predicted_price": 0.0,
                "confidence_score": 0.0,
                "price_range": {"min": 0.0, "max": 0.0},
                "category_analysis": {"error": "Модель недоступна"},
            }

        try:
            # Предобработка данных
            X = self._preprocess_single_item(product_data)
            if X is None:
                raise ValueError("Ошибка предобработки данных")

            # Предсказание (модель обучена на log-scale)
            log_prediction = self.model.predict(X)[0]
            prediction = float(np.expm1(log_prediction))  # Обратное логарифмирование

            # Ограничиваем предсказание разумными рамками
            prediction = max(self.min_price, min(prediction, self.max_price))

            # Расчет уверенности
            confidence_score = self._calculate_confidence_score(prediction, X)

            # Расчет диапазона цен (± 30% от предсказания)
            price_range = {
                "min": max(self.min_price, prediction * 0.7),
                "max": min(self.max_price, prediction * 1.3),
            }

            # Анализ категории
            category_analysis = self._get_category_analysis(product_data, prediction)

            return {
                "predicted_price": round(prediction, 2),
                "confidence_score": round(confidence_score, 3),
                "price_range": {
                    "min": round(price_range["min"], 2),
                    "max": round(price_range["max"], 2),
                },
                "category_analysis": category_analysis,
            }

        except Exception as e:
            print(f"Ошибка предсказания цены: {e}")
            return {
                "error": str(e),
                "predicted_price": 0.0,
                "confidence_score": 0.0,
                "price_range": {"min": 0.0, "max": 0.0},
                "category_analysis": {"error": "Ошибка обработки"},
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о загруженной модели."""
        return {
            "model_loaded": self.model is not None,
            "preprocessing_loaded": self.preprocessing_pipeline is not None,
            "model_path": str(self.model_path),
            "preprocessing_path": str(self.preprocessing_path),
            "catboost_available": catboost_available,
            "confidence_threshold": self.confidence_threshold,
            "price_limits": {"min": self.min_price, "max": self.max_price},
        }
