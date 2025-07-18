"""Модуль для обучения модели ценообразования на основе данных Mercari.
Основан на лучшем решении из mfdp/Mercari_Pricing_Improved.ipynb
"""

import pandas as pd
import numpy as np
import pickle
import re
from pathlib import Path
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


class PricingModelTrainer:
    """Класс для обучения модели ценообразования."""

    def __init__(self, model_path: str = "models/catboost_pricing_model.cbm",
                 preprocessing_path: str = "models/preprocessing_pipeline.pkl"):
        self.model_path = Path(model_path)
        self.preprocessing_path = Path(preprocessing_path)
        self.model = None
        self.preprocessing_pipeline = {}

    def preprocess_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        """Предобработка данных по алгоритму из лучшего ноутбука."""
        print("Начинаем предобработку данных...")

        # Расширенная очистка данных
        df = df.copy()
        df["category_name"] = df["category_name"].fillna("Other")
        df["brand_name"] = df["brand_name"].fillna("Unknown")
        df["item_description"] = df["item_description"].replace("No description yet", "")
        df["item_description"] = df["item_description"].fillna("")
        df = df[df["price"] > 0]
        # Убираем только крайние выбросы (99.5 перцентиль)
        df = df[df["price"] <= df["price"].quantile(0.995)]
        df = df.reset_index(drop=True)

        print(f"Размер датасета после очистки: {df.shape}")

        # Расширенный Feature Engineering
        print("Создание новых признаков...")

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

        # TF-IDF векторизация текстовых полей
        print("Создание TF-IDF признаков...")

        tfidf_name = TfidfVectorizer(max_features=30, stop_words="english", lowercase=True)
        tfidf_desc = TfidfVectorizer(max_features=20, stop_words="english", lowercase=True)

        tfidf_name_features = tfidf_name.fit_transform(df["name"]).toarray()
        tfidf_desc_features = tfidf_desc.fit_transform(df["item_description"]).toarray()

        tfidf_name_df = pd.DataFrame(tfidf_name_features, columns=[f"name_tfidf_{i}" for i in range(30)])
        tfidf_desc_df = pd.DataFrame(tfidf_desc_features, columns=[f"desc_tfidf_{i}" for i in range(20)])

        # Кодирование категориальных признаков
        print("Кодирование категориальных признаков...")

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

        # Сохраняем preprocessors для будущих предсказаний
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

        print(f"Итоговый размер матрицы признаков: {X.shape}")
        print(f"Целевая переменная (log): min={y.min():.3f}, max={y.max():.3f}, mean={y.mean():.3f}")

        return X, y

    def train_model(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Обучение CatBoost модели с лучшими параметрами."""
        if not catboost_available:
            raise ImportError("CatBoost недоступен для обучения")

        print("Обучение CatBoost модели с улучшенными параметрами...")

        # Разделение на train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Создаем модель с лучшими параметрами из ноутбука
        self.model = CatBoostRegressor(
            iterations=100,  # Увеличиваем для лучшего качества
            depth=5,
            learning_rate=0.15,
            l2_leaf_reg=3,
            random_state=42,
            verbose=20  # Показываем прогресс
        )

        # Обучаем модель
        self.model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)

        # Оценка качества
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        # Переводим обратно из log-scale
        train_pred_exp = np.expm1(train_pred)
        test_pred_exp = np.expm1(test_pred)
        y_train_exp = np.expm1(y_train)
        y_test_exp = np.expm1(y_test)

        # Рассчитываем метрики
        train_rmse = np.sqrt(mean_squared_error(y_train_exp, train_pred_exp))
        test_rmse = np.sqrt(mean_squared_error(y_test_exp, test_pred_exp))
        train_mae = mean_absolute_error(y_train_exp, train_pred_exp)
        test_mae = mean_absolute_error(y_test_exp, test_pred_exp)
        train_r2 = r2_score(y_train_exp, train_pred_exp)
        test_r2 = r2_score(y_test_exp, test_pred_exp)

        print("\n=== РЕЗУЛЬТАТЫ ОБУЧЕНИЯ ===")
        print(f"Train RMSE: {train_rmse:.4f}")
        print(f"Test RMSE: {test_rmse:.4f}")
        print(f"Train MAE: {train_mae:.4f}")
        print(f"Test MAE: {test_mae:.4f}")
        print(f"Train R²: {train_r2:.4f}")
        print(f"Test R²: {test_r2:.4f}")

        print("\nМодель готова к сохранению!")

    def save_model(self) -> None:
        """Сохранение обученной модели и pipeline предобработки."""
        if self.model is None:
            raise ValueError("Модель не обучена. Сначала вызовите train_model()")

        # Создаем директории если их нет
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.preprocessing_path.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем модель
        self.model.save_model(str(self.model_path))
        print(f"Модель сохранена в {self.model_path}")

        # Сохраняем preprocessing pipeline
        with open(self.preprocessing_path, "wb") as f:
            pickle.dump(self.preprocessing_pipeline, f)
        print(f"Pipeline предобработки сохранен в {self.preprocessing_path}")

    def load_and_train(self, data_path: str = "data/train.tsv", sample_size: int = 100000) -> None:
        """Полный цикл: загрузка данных, предобработка, обучение, сохранение."""
        print(f"Загрузка данных из {data_path}...")

        # Проверяем наличие файла данных
        if not Path(data_path).exists():
            raise FileNotFoundError(f"Файл данных не найден: {data_path}")

        # Загружаем данные
        df = pd.read_csv(data_path, sep="\t")

        # Берем подвыборку для быстрого обучения
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
            print(f"Используем выборку размером {sample_size} записей")

        print(f"Загружено {len(df)} записей")

        # Предобработка
        X, y = self.preprocess_data(df)

        # Обучение
        self.train_model(X, y)

        # Сохранение
        self.save_model()

        print("\n✅ Модель успешно обучена и сохранена!")


if __name__ == "__main__":
    # Инициализируем trainer
    trainer = PricingModelTrainer()

    # Обучаем модель
    try:
        trainer.load_and_train()
    except Exception as e:
        print(f"❌ Ошибка при обучении модели: {e}")
        print("Убедитесь что:")
        print("1. Установлен CatBoost: pip install catboost")
        print("2. Файл данных существует: mfdp/data/train.tsv")
        print("3. Папка models/ создана и доступна для записи")
