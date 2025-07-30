"""Модуль для обучения модели ценообразования."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from catboost import CatBoostRegressor

logger = logging.getLogger(__name__)


class ModelMetrics:
    """Класс для хранения и отслеживания метрик модели."""

    def __init__(self):
        """Инициализация метрик."""
        self.metrics = {
            "train": {
                "rmse": 0.0,
                "mae": 0.0,
                "r2": 0.0
            },
            "test": {
                "rmse": 0.0,
                "mae": 0.0,
                "r2": 0.0
            }
        }
        self.timestamp = datetime.now().isoformat()
        self.model_version = None
        self.dataset_stats = {}
        self.feature_importance = {}

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование метрик в словарь."""
        return {
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "dataset_stats": self.dataset_stats,
            "feature_importance": self.feature_importance
        }

    def save(self, path: Path) -> None:
        """Сохранение метрик в файл."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class PricingModelTrainer:
    """Класс для обучения модели ценообразования."""

    def __init__(
        self,
        model_dir: str,
        model_name: str = "catboost_pricing_model",
        version: str = None
    ):
        """Инициализация тренера."""
        self.model_dir = Path(model_dir)
        self.model_name = model_name
        self.version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.version_dir = self.model_dir / self.version
        self.version_dir.mkdir(parents=True, exist_ok=True)

        self.model_path = self.version_dir / f"{model_name}.cbm"
        self.metrics_path = self.version_dir / "metrics.json"

        self.model = None
        self.metrics = ModelMetrics()
        self.metrics.model_version = self.version

        # Создаем symbolic link на последнюю версию
        latest_link = self.model_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(self.version_dir)

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Предобработка данных."""
        logger.info("Начинаем предобработку данных...")

        # Очистка данных
        df = df.copy()
        df = df.dropna(subset=["price", "name", "category_name"])
        df = df.fillna({
            "brand_name": "Unknown",
            "item_description": "",
            "shipping": 0
        })

        logger.info(f"Размер датасета после очистки: {df.shape}")

        logger.info("Создание новых признаков...")
        # Длина названия и описания
        df["name_len"] = df["name"].str.len()
        df["desc_len"] = df["item_description"].str.len()

        # Категориальные признаки
        df["condition_text"] = df["item_condition_id"].map({
            1: "Новый",
            2: "Отличное",
            3: "Хорошее",
            4: "Удовлетворительное",
            5: "Плохое"
        })

        # Собираем статистики
        self.metrics.dataset_stats = {
            "category_counts": df["category_name"].value_counts().to_dict(),
            "brand_counts": df["brand_name"].value_counts().to_dict(),
            "condition_counts": df["condition_text"].value_counts().to_dict(),
            "shipping_counts": df["shipping"].value_counts().to_dict(),
            "price_stats": {
                "min": float(df["price"].min()),
                "max": float(df["price"].max()),
                "mean": float(df["price"].mean()),
                "median": float(df["price"].median())
            }
        }

        return df

    def train_model(self, df: pd.DataFrame) -> None:
        """Обучение модели."""
        # Предобработка данных
        df = self.preprocess_data(df)

        # Разделение на признаки и целевую переменную
        X = df.drop(["price", "name", "item_description"], axis=1)
        y = df["price"]

        # Разделение на обучающую и тестовую выборки
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Определяем категориальные признаки
        cat_features = [
            "category_name",
            "brand_name",
            "condition_text"
        ]

        # Обучение модели
        self.model = CatBoostRegressor(
            iterations=1000,
            learning_rate=0.1,
            depth=6,
            loss_function="RMSE",
            random_seed=42,
            verbose=False,
            cat_features=cat_features
        )

        self.model.fit(X_train, y_train)

        # Сохраняем важность признаков
        feature_importance = dict(zip(
            X_train.columns,
            self.model.feature_importances_
        ))
        self.metrics.feature_importance = feature_importance

        # Считаем метрики
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)

        self.metrics.metrics["train"]["rmse"] = float(
            np.sqrt(mean_squared_error(y_train, y_train_pred))
        )
        self.metrics.metrics["train"]["mae"] = float(
            mean_absolute_error(y_train, y_train_pred)
        )
        self.metrics.metrics["train"]["r2"] = float(
            r2_score(y_train, y_train_pred)
        )

        self.metrics.metrics["test"]["rmse"] = float(
            np.sqrt(mean_squared_error(y_test, y_test_pred))
        )
        self.metrics.metrics["test"]["mae"] = float(
            mean_absolute_error(y_test, y_test_pred)
        )
        self.metrics.metrics["test"]["r2"] = float(
            r2_score(y_test, y_test_pred)
        )

        # Сохраняем модель и метрики
        self.save_model()

    def save_model(self) -> None:
        """Сохранение модели и метрик."""
        self.model.save_model(self.model_path)
        self.metrics.save(self.metrics_path)
