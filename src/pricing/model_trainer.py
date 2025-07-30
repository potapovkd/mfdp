"""Модуль для обучения модели ценообразования."""

import pandas as pd
import numpy as np
import pickle
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings("ignore")

try:
    from catboost import CatBoostRegressor
    catboost_available = True
except ImportError:
    print("CatBoost не установлен. Установите: pip install catboost")
    catboost_available = False


class ModelMetrics:
    """Класс для хранения и отслеживания метрик модели."""

    def __init__(self):
        """Инициализация метрик."""
        self.train_rmse = 0.0
        self.test_rmse = 0.0
        self.train_mae = 0.0
        self.test_mae = 0.0
        self.train_r2 = 0.0
        self.test_r2 = 0.0
        self.timestamp = datetime.now().isoformat()
        self.model_version = None
        self.dataset_stats = {}
        self.feature_importance = {}

    def to_dict(self) -> Dict[str, Any]:
        """Конвертация метрик в словарь."""
        return {
            "model_version": self.model_version,
            "timestamp": self.timestamp,
            "metrics": {
                "train": {
                    "rmse": float(self.train_rmse),
                    "mae": float(self.train_mae),
                    "r2": float(self.train_r2)
                },
                "test": {
                    "rmse": float(self.test_rmse),
                    "mae": float(self.test_mae),
                    "r2": float(self.test_r2)
                }
            },
            "dataset_stats": self.dataset_stats,
            "feature_importance": {k: float(v) for k, v in self.feature_importance.items()}
        }

    def save(self, path: Path) -> None:
        """Сохранение метрик в JSON файл."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class PricingModelTrainer:
    """Класс для обучения модели ценообразования."""

    def __init__(
        self,
        model_dir: str = "models",
        model_name: str = "catboost_pricing_model",
        version: str = None
    ):
        """Инициализация тренера моделей."""
        self.model_dir = Path(model_dir)
        self.model_name = model_name
        self.version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Создаем директорию для версии модели
        self.version_dir = self.model_dir / self.version
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        # Пути к файлам модели
        self.model_path = self.version_dir / f"{model_name}.cbm"
        self.preprocessing_path = self.version_dir / "preprocessing_pipeline.pkl"
        self.metrics_path = self.version_dir / "metrics.json"
        
        # Инициализация
        self.model = None
        self.preprocessing_pipeline = {}
        self.metrics = ModelMetrics()
        self.metrics.model_version = self.version
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.version_dir / "training.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def preprocess_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        """Предобработка данных."""
        self.logger.info("Начинаем предобработку данных...")

        # Расширенная очистка данных
        df = df.copy()
        df["category_name"] = df["category_name"].fillna("Other")
        df["brand_name"] = df["brand_name"].fillna("Unknown")
        df["item_description"] = df["item_description"].replace("No description yet", "")
        df["item_description"] = df["item_description"].fillna("")
        df = df[df["price"] > 0]
        
        # Сохраняем статистики датасета
        self.metrics.dataset_stats = {
            "total_samples": len(df),
            "categories": df["category_name"].nunique(),
            "brands": df["brand_name"].nunique(),
            "price_stats": {
                "min": float(df["price"].min()),
                "max": float(df["price"].max()),
                "mean": float(df["price"].mean()),
                "median": float(df["price"].median())
            }
        }

        # Убираем выбросы
        df = df[df["price"] <= df["price"].quantile(0.995)]
        df = df.reset_index(drop=True)

        self.logger.info(f"Размер датасета после очистки: {df.shape}")

        # Feature Engineering
        self.logger.info("Создание новых признаков...")

        # Базовые числовые признаки
        df["desc_len"] = df["item_description"].str.len()
        df["name_len"] = df["name"].str.len()
        df["has_brand"] = (df["brand_name"] != "Unknown").astype(int)
        df["has_description"] = (df["item_description"] != "").astype(int)

        # Разбиение категории на уровни
        df["cat_main"] = df["category_name"].apply(lambda x: x.split("/")[0] if "/" in x else x)
        df["cat_sub"] = df["category_name"].apply(lambda x: x.split("/")[1] if "/" in x and len(x.split("/"))>1 else "None")
        df["cat_detail"] = df["category_name"].apply(lambda x: x.split("/")[2] if "/" in x and len(x.split("/"))>2 else "None")

        # Текстовые признаки
        df["desc_words"] = df["item_description"].apply(lambda x: len(re.findall(r"\w+", x)))
        df["name_words"] = df["name"].apply(lambda x: len(re.findall(r"\w+", x)))
        df["desc_unique_words"] = df["item_description"].apply(lambda x: len(set(re.findall(r"\w+", x.lower()))))
        df["name_unique_words"] = df["name"].apply(lambda x: len(set(re.findall(r"\w+", x.lower()))))

        # Признаки взаимодействия
        df["brand_cat_main"] = df["brand_name"] + "_" + df["cat_main"]
        df["condition_shipping"] = df["item_condition_id"].astype(str) + "_" + df["shipping"].astype(str)

        # TF-IDF векторизация
        self.logger.info("Создание TF-IDF признаков...")

        tfidf_name = TfidfVectorizer(max_features=30, stop_words="english", lowercase=True)
        tfidf_desc = TfidfVectorizer(max_features=20, stop_words="english", lowercase=True)

        tfidf_name_features = tfidf_name.fit_transform(df["name"]).toarray()
        tfidf_desc_features = tfidf_desc.fit_transform(df["item_description"]).toarray()

        tfidf_name_df = pd.DataFrame(tfidf_name_features, columns=[f"name_tfidf_{i}" for i in range(30)])
        tfidf_desc_df = pd.DataFrame(tfidf_desc_features, columns=[f"desc_tfidf_{i}" for i in range(20)])

        # Кодирование категориальных признаков
        self.logger.info("Кодирование категориальных признаков...")

        le_brand = LabelEncoder()
        le_cat_main = LabelEncoder()
        le_cat_sub = LabelEncoder()
        le_cat_detail = LabelEncoder()
        le_brand_cat = LabelEncoder()
        le_cond_ship = LabelEncoder()

        df["brand_enc"] = le_brand.fit_transform(df["brand_name"])
        df["cat_main_enc"] = le_cat_main.fit_transform(df["cat_main"])
        df["cat_sub_enc"] = le_cat_sub.fit_transform(df["cat_sub"])
        df["cat_detail_enc"] = le_cat_detail.fit_transform(df["cat_detail"])
        df["brand_cat_enc"] = le_brand_cat.fit_transform(df["brand_cat_main"])
        df["cond_ship_enc"] = le_cond_ship.fit_transform(df["condition_shipping"])

        # Сохраняем preprocessors
        self.preprocessing_pipeline = {
            "tfidf_name": tfidf_name,
            "tfidf_desc": tfidf_desc,
            "le_brand": le_brand,
            "le_cat_main": le_cat_main,
            "le_cat_sub": le_cat_sub,
            "le_cat_detail": le_cat_detail,
            "le_brand_cat": le_brand_cat,
            "le_cond_ship": le_cond_ship,
            "feature_columns": [
                "item_condition_id", "shipping", "brand_enc", "cat_main_enc", "cat_sub_enc",
                "cat_detail_enc", "brand_cat_enc", "cond_ship_enc",
                "desc_len", "name_len", "has_brand", "has_description",
                "desc_words", "name_words", "desc_unique_words", "name_unique_words"
            ] + [f"name_tfidf_{i}" for i in range(30)] + [f"desc_tfidf_{i}" for i in range(20)]
        }

        # Финальный набор признаков
        feature_cols = [
            "item_condition_id", "shipping", "brand_enc", "cat_main_enc", "cat_sub_enc",
            "cat_detail_enc", "brand_cat_enc", "cond_ship_enc",
            "desc_len", "name_len", "has_brand", "has_description",
            "desc_words", "name_words", "desc_unique_words", "name_unique_words"
        ]

        X_base = df[feature_cols].reset_index(drop=True)
        X = pd.concat([X_base, tfidf_name_df, tfidf_desc_df], axis=1)
        y = np.log1p(df["price"])  # Логарифмируем цены

        self.logger.info(f"Итоговый размер матрицы признаков: {X.shape}")
        self.logger.info(f"Целевая переменная (log): min={y.min():.3f}, max={y.max():.3f}, mean={y.mean():.3f}")

        return X, y

    def train_model(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Обучение CatBoost модели."""
        if not catboost_available:
            raise ImportError("CatBoost недоступен для обучения")

        self.logger.info("Обучение CatBoost модели...")

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Создаем модель с оптимизированными параметрами
        self.model = CatBoostRegressor(
            iterations=1000,
            depth=6,
            learning_rate=0.1,
            l2_leaf_reg=3,
            random_state=42,
            verbose=100
        )

        # Обучаем модель
        self.model.fit(
            X_train, y_train,
            eval_set=(X_test, y_test),
            use_best_model=True,
            early_stopping_rounds=50
        )

        # Получаем предсказания
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        # Переводим обратно из log-scale
        train_pred_exp = np.expm1(train_pred)
        test_pred_exp = np.expm1(test_pred)
        y_train_exp = np.expm1(y_train)
        y_test_exp = np.expm1(y_test)

        # Сохраняем метрики
        self.metrics.train_rmse = np.sqrt(mean_squared_error(y_train_exp, train_pred_exp))
        self.metrics.test_rmse = np.sqrt(mean_squared_error(y_test_exp, test_pred_exp))
        self.metrics.train_mae = mean_absolute_error(y_train_exp, train_pred_exp)
        self.metrics.test_mae = mean_absolute_error(y_test_exp, test_pred_exp)
        self.metrics.train_r2 = r2_score(y_train_exp, train_pred_exp)
        self.metrics.test_r2 = r2_score(y_test_exp, test_pred_exp)

        # Сохраняем важность признаков
        feature_importance = self.model.feature_importances_
        feature_names = X.columns
        self.metrics.feature_importance = dict(zip(feature_names, feature_importance))

        self.logger.info("\n=== РЕЗУЛЬТАТЫ ОБУЧЕНИЯ ===")
        self.logger.info(f"Train RMSE: {self.metrics.train_rmse:.4f}")
        self.logger.info(f"Test RMSE: {self.metrics.test_rmse:.4f}")
        self.logger.info(f"Train MAE: {self.metrics.train_mae:.4f}")
        self.logger.info(f"Test MAE: {self.metrics.test_mae:.4f}")
        self.logger.info(f"Train R²: {self.metrics.train_r2:.4f}")
        self.logger.info(f"Test R²: {self.metrics.test_r2:.4f}")

    def save_model(self) -> None:
        """Сохранение обученной модели и всех артефактов."""
        if self.model is None:
            raise ValueError("Модель не обучена. Сначала вызовите train_model()")

        # Сохраняем модель
        self.model.save_model(str(self.model_path))
        self.logger.info(f"Модель сохранена в {self.model_path}")

        # Сохраняем preprocessing pipeline
        with open(self.preprocessing_path, "wb") as f:
            pickle.dump(self.preprocessing_pipeline, f)
        self.logger.info(f"Pipeline предобработки сохранен в {self.preprocessing_path}")

        # Сохраняем метрики
        self.metrics.save(self.metrics_path)
        self.logger.info(f"Метрики сохранены в {self.metrics_path}")

        # Создаем symbolic link на последнюю версию
        latest_link = self.model_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(self.version_dir.name)
        self.logger.info(f"Создан symbolic link на последнюю версию: {latest_link}")

    def load_and_train(self, data_path: str = "data/train.tsv", sample_size: int = None) -> None:
        """Полный цикл: загрузка данных, предобработка, обучение, сохранение."""
        self.logger.info(f"Загрузка данных из {data_path}...")

        # Проверяем наличие файла данных
        if not Path(data_path).exists():
            raise FileNotFoundError(f"Файл данных не найден: {data_path}")

        # Загружаем данные
        df = pd.read_csv(data_path, sep="\t")

        # Берем подвыборку для быстрого обучения
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
            self.logger.info(f"Используем выборку размером {sample_size} записей")

        self.logger.info(f"Загружено {len(df)} записей")

        # Предобработка
        X, y = self.preprocess_data(df)

        # Обучение
        self.train_model(X, y)

        # Сохранение
        self.save_model()

        self.logger.info("\n✅ Модель успешно обучена и сохранена!")


if __name__ == "__main__":
    # Настройка корневого логгера
    logging.basicConfig(level=logging.INFO)

    # Инициализируем trainer
    trainer = PricingModelTrainer()

    # Обучаем модель
    try:
        trainer.load_and_train()
    except Exception as e:
        logging.error(f"❌ Ошибка при обучении модели: {e}")
        logging.info("Убедитесь что:")
        logging.info("1. Установлен CatBoost: pip install catboost")
        logging.info("2. Файл данных существует: data/train.tsv")
        logging.info("3. Папка models/ создана и доступна для записи")
