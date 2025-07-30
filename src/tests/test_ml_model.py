"""Тесты для ML модели и системы версионирования."""

import json
import warnings
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from pricing.model_trainer import ModelMetrics, PricingModelTrainer


class TestModelMetrics:
    """Тесты для класса ModelMetrics."""

    def test_initialization(self):
        """Тест инициализации метрик."""
        metrics = ModelMetrics()
        assert metrics.metrics["train"]["rmse"] == 0.0
        assert metrics.metrics["train"]["mae"] == 0.0
        assert metrics.metrics["train"]["r2"] == 0.0
        assert metrics.metrics["test"]["rmse"] == 0.0
        assert metrics.metrics["test"]["mae"] == 0.0
        assert metrics.metrics["test"]["r2"] == 0.0
        assert metrics.model_version is None
        assert isinstance(metrics.dataset_stats, dict)
        assert isinstance(metrics.feature_importance, dict)

    def test_to_dict(self):
        """Тест преобразования метрик в словарь."""
        metrics = ModelMetrics()
        metrics.metrics["train"]["rmse"] = 1.0
        metrics.metrics["test"]["rmse"] = 1.5
        metrics.model_version = "test_version"

        metrics_dict = metrics.to_dict()
        assert metrics_dict["metrics"]["train"]["rmse"] == 1.0
        assert metrics_dict["metrics"]["test"]["rmse"] == 1.5
        assert metrics_dict["model_version"] == "test_version"

    def test_save_to_file(self, tmp_path):
        """Тест сохранения метрик в файл."""
        metrics = ModelMetrics()
        metrics.metrics["train"]["rmse"] = 1.0
        metrics.metrics["test"]["rmse"] = 1.5
        metrics.model_version = "test_version"

        metrics_file = tmp_path / "metrics.json"
        metrics.save(metrics_file)

        assert metrics_file.exists()
        with open(metrics_file) as f:
            loaded_metrics = json.load(f)
            assert loaded_metrics["metrics"]["train"]["rmse"] == 1.0
            assert loaded_metrics["metrics"]["test"]["rmse"] == 1.5


class TestModelTrainer:
    """Тесты для класса PricingModelTrainer."""

    @pytest.fixture
    def trainer(self, tmp_path):
        """Фикстура для создания тренера модели."""
        return PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version="test_version"
        )

    def test_model_versioning(self, tmp_path):
        """Тест системы версионирования моделей."""
        version1 = "20240101_120000"
        version2 = "20240101_130000"
        trainer1 = PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version=version1
        )
        trainer2 = PricingModelTrainer(
            model_dir=str(tmp_path), model_name="test_model", version=version2
        )

        assert trainer1.version_dir.exists()
        assert trainer2.version_dir.exists()
        assert (tmp_path / version1).exists()
        assert (tmp_path / version2).exists()

    def test_model_training_and_saving(self, trainer):
        """Тест обучения и сохранения модели."""
        # Создаем тестовый датасет с достаточным количеством данных
        df = pd.DataFrame(
            {
                "price": [100, 200, 300, 150, 250],
                "name": [
                    "Product 1",
                    "Product 2",
                    "Product 3",
                    "Product 4",
                    "Product 5",
                ],
                "category_name": ["Electronics"] * 5,
                "brand_name": ["Apple", "Samsung", "Apple", "Google", "Samsung"],
                "item_description": ["Test"] * 5,
                "item_condition_id": [1, 2, 1, 3, 2],
                "shipping": [0, 1, 0, 1, 0],
            }
        )

        # Мокаем CatBoost
        with patch("catboost.CatBoostRegressor") as mock_catboost:
            mock_model = Mock()
            mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2])
            mock_model.predict = Mock(return_value=np.array([10.0, 15.0, 12.0]))
            mock_catboost.return_value = mock_model

            # Подавляем предупреждения о R^2 score
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                # Обучаем модель
                trainer.train_model(df)

            # Проверяем что файлы созданы
            assert trainer.model_path.exists()
            assert trainer.metrics_path.exists()

    def test_dataset_statistics(self, trainer):
        """Тест сбора статистик датасета."""
        # Создаем тестовый датасет
        df = pd.DataFrame(
            {
                "price": [100, 200, 300, 400, 500],
                "name": [
                    "Product 1",
                    "Product 2",
                    "Product 3",
                    "Product 4",
                    "Product 5",
                ],
                "category_name": ["Electronics"] * 3 + ["Books"] * 2,
                "brand_name": ["Apple", "Samsung", "Apple", "Unknown", "Unknown"],
                "item_description": ["Test"] * 5,
                "item_condition_id": [1, 2, 1, 3, 2],
                "shipping": [0, 1, 0, 1, 0],
            }
        )

        # Запускаем предобработку
        df = trainer.preprocess_data(df)

        # Проверяем статистики
        assert "category_counts" in trainer.metrics.dataset_stats
        assert "brand_counts" in trainer.metrics.dataset_stats
        assert "condition_counts" in trainer.metrics.dataset_stats
        assert "shipping_counts" in trainer.metrics.dataset_stats
        assert "price_stats" in trainer.metrics.dataset_stats

        # Проверяем конкретные значения
        assert trainer.metrics.dataset_stats["category_counts"]["Electronics"] == 3
        assert trainer.metrics.dataset_stats["category_counts"]["Books"] == 2
        assert trainer.metrics.dataset_stats["brand_counts"]["Apple"] == 2
        assert trainer.metrics.dataset_stats["brand_counts"]["Unknown"] == 2
