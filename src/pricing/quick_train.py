"""Быстрое обучение модели для демонстрации.
"""

import pickle
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

try:
    from catboost import CatBoostRegressor

    catboost_available = True
except ImportError:
    print("CatBoost не установлен")
    catboost_available = False


def quick_train_model():
    """Быстрое обучение модели на малой выборке."""
    print("🚀 Быстрое обучение модели ценообразования...")

    # Проверяем наличие данных
    data_path = "data/train.tsv"
    if not Path(data_path).exists():
        print(f"❌ Файл данных не найден: {data_path}")
        return False

    # Загружаем маленькую выборку
    print("📊 Загрузка данных...")
    df = pd.read_csv(data_path, sep="\t", nrows=5000)  # Только 5000 записей

    # Быстрая очистка
    df = df[df["price"] > 0].copy()
    df["category_name"] = df["category_name"].fillna("Other")
    df["brand_name"] = df["brand_name"].fillna("Unknown")
    df["item_description"] = df["item_description"].fillna("")

    print(f"✅ Загружено {len(df)} записей")

    # Создаем простые признаки
    print("🔧 Создание признаков...")
    df["desc_len"] = df["item_description"].str.len()
    df["name_len"] = df["name"].str.len()
    df["has_brand"] = (df["brand_name"] != "Unknown").astype(int)
    df["has_description"] = (df["item_description"] != "").astype(int)

    # Разбиение категории
    df["cat_main"] = df["category_name"].apply(
        lambda x: x.split("/")[0] if "/" in x else x
    )
    df["cat_sub"] = df["category_name"].apply(
        lambda x: x.split("/")[1] if "/" in x and len(x.split("/")) > 1 else "None"
    )

    # Текстовые признаки
    df["desc_words"] = df["item_description"].apply(
        lambda x: len(re.findall(r"\w+", x))
    )
    df["name_words"] = df["name"].apply(lambda x: len(re.findall(r"\w+", x)))

    # TF-IDF (упрощенный)
    tfidf_name = TfidfVectorizer(max_features=10, stop_words="english", lowercase=True)
    tfidf_desc = TfidfVectorizer(max_features=10, stop_words="english", lowercase=True)

    tfidf_name_features = tfidf_name.fit_transform(df["name"]).toarray()
    tfidf_desc_features = tfidf_desc.fit_transform(df["item_description"]).toarray()

    # Label encoding
    le_brand = LabelEncoder()
    le_cat_main = LabelEncoder()
    le_cat_sub = LabelEncoder()

    df["brand_enc"] = le_brand.fit_transform(df["brand_name"])
    df["cat_main_enc"] = le_cat_main.fit_transform(df["cat_main"])
    df["cat_sub_enc"] = le_cat_sub.fit_transform(df["cat_sub"])

    # Собираем признаки
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

    X_base = df[feature_cols]

    # Добавляем TF-IDF
    tfidf_name_df = pd.DataFrame(
        tfidf_name_features, columns=[f"name_tfidf_{i}" for i in range(10)]
    )
    tfidf_desc_df = pd.DataFrame(
        tfidf_desc_features, columns=[f"desc_tfidf_{i}" for i in range(10)]
    )

    X = pd.concat([X_base.reset_index(drop=True), tfidf_name_df, tfidf_desc_df], axis=1)
    y = np.log1p(df["price"])

    print(f"📈 Размер матрицы признаков: {X.shape}")

    # Обучение модели
    if not catboost_available:
        print("❌ CatBoost недоступен")
        return False

    print("🤖 Обучение CatBoost...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Быстрая модель
    model = CatBoostRegressor(
        iterations=50, depth=4, learning_rate=0.2, random_state=42, verbose=10
    )

    model.fit(X_train, y_train, eval_set=(X_test, y_test))

    # Проверка качества
    test_pred = model.predict(X_test)
    test_pred_exp = np.expm1(test_pred)
    y_test_exp = np.expm1(y_test)

    rmse = np.sqrt(mean_squared_error(y_test_exp, test_pred_exp))
    print(f"📊 Test RMSE: {rmse:.2f}")

    # Сохранение
    print("💾 Сохранение модели...")

    # Создаем директории
    Path("models").mkdir(exist_ok=True)

    # Сохраняем модель
    model.save_model("models/catboost_pricing_model.cbm")

    # Сохраняем pipeline
    preprocessing_pipeline = {
        "tfidf_name": tfidf_name,
        "tfidf_desc": tfidf_desc,
        "le_brand": le_brand,
        "le_cat_main": le_cat_main,
        "le_cat_sub": le_cat_sub,
        "feature_columns": feature_cols
        + [f"name_tfidf_{i}" for i in range(10)]
        + [f"desc_tfidf_{i}" for i in range(10)],
    }

    with open("models/preprocessing_pipeline.pkl", "wb") as f:
        pickle.dump(preprocessing_pipeline, f)

    print("✅ Модель успешно обучена и сохранена!")
    print("📁 Модель: models/catboost_pricing_model.cbm")
    print("📁 Pipeline: models/preprocessing_pipeline.pkl")

    return True


if __name__ == "__main__":
    success = quick_train_model()
    if success:
        print("\n🎉 Готово! Модель готова к использованию.")
    else:
        print("\n❌ Обучение модели не удалось.")
