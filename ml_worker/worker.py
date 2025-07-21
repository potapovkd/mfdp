#!/usr/bin/env python3
"""ML Worker для масштабируемого прогнозирования цен.
Использует Redis для очередей задач и RabbitMQ для результатов.
"""

import os
import json
import pickle
import signal
import sys
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import redis
import pika
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from loguru import logger


@dataclass
class PricingTask:
    """Задача прогнозирования цены."""

    task_id: str
    product_data: Dict[str, Any]
    callback_queue: Optional[str] = None


@dataclass
class PricingResult:
    """Результат прогнозирования цены."""

    task_id: str
    predicted_price: float
    confidence_score: float
    price_range: Dict[str, float]
    category_analysis: Dict[str, str]
    processing_time: float
    worker_id: str


class ScalableMLWorker:
    """Масштабируемый ML воркер для прогнозирования цен."""

    def __init__(self):
        self.worker_id = f"worker_{os.getpid()}_{int(time.time())}"
        self.model = None
        self.preprocessing_pipeline = None
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.is_running = True
        self.executor = ThreadPoolExecutor(max_workers=int(os.getenv("WORKER_THREADS", "4")))

        # Настройка логирования
        logger.add(
            f"logs/worker_{self.worker_id}.log",
            rotation="100 MB",
            retention="7 days",
            level="INFO"
        )

        self._setup_connections()
        self._load_model()
        self._register_signal_handlers()

        logger.info(f"ML Worker {self.worker_id} initialized successfully")

    def _setup_connections(self):
        """Настройка подключений к Redis и RabbitMQ с retry."""
        import time
        max_retries = 10
        for attempt in range(1, max_retries + 1):
            try:
                # Redis для очередей задач
                redis_host = os.getenv("REDIS_HOST", "redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                redis_db = int(os.getenv("REDIS_DB", "0"))

                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10
                )

                # Тест соединения
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")

                # RabbitMQ для результатов
                rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
                rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
                rabbitmq_user = os.getenv("RABBITMQ_USER", "pricing")
                rabbitmq_pass = os.getenv("RABBITMQ_PASS", "pricing123")

                credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
                self.rabbitmq_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=rabbitmq_host,
                        port=rabbitmq_port,
                        credentials=credentials,
                        heartbeat=600,
                        blocked_connection_timeout=300
                    )
                )
                self.rabbitmq_channel = self.rabbitmq_connection.channel()

                # Объявляем exchange для результатов
                self.rabbitmq_channel.exchange_declare(
                    exchange="pricing_results",
                    exchange_type="direct",
                    durable=True
                )

                logger.info(f"Connected to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
                return  # успех, выходим из retry-цикла

            except Exception as e:
                logger.error(f"Failed to setup connections (attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    raise
                time.sleep(5)  # подождать 5 секунд и попробовать снова

    def _load_model(self):
        """Загрузка ML модели и pipeline."""
        try:
            model_path = os.getenv("MODEL_PATH", "/app/models/catboost_pricing_model.cbm")
            pipeline_path = os.getenv("PREPROCESSING_PATH", "/app/models/preprocessing_pipeline.pkl")

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            if not os.path.exists(pipeline_path):
                raise FileNotFoundError(f"Pipeline file not found: {pipeline_path}")

            # Загрузка CatBoost модели
            self.model = CatBoostRegressor()
            self.model.load_model(model_path)

            # Загрузка preprocessing pipeline
            with open(pipeline_path, "rb") as f:
                self.preprocessing_pipeline = pickle.load(f)

            logger.info(f"Model loaded successfully from {model_path}")
            logger.info(f"Pipeline loaded successfully from {pipeline_path}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _register_signal_handlers(self):
        """Регистрация обработчиков сигналов для graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, starting graceful shutdown...")
            self.is_running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _preprocess_product_data(self, product_data: Dict[str, Any]) -> np.ndarray:
        """Предобработка данных товара для прогнозирования."""
        try:
            # Создаем DataFrame из данных товара
            df = pd.DataFrame([product_data])

            # Применяем сохраненный pipeline
            features = self.preprocessing_pipeline.transform(df)
            return features

        except Exception as e:
            logger.error(f"Error in preprocessing: {e}")
            raise

    def _predict_price(self, task: PricingTask) -> PricingResult:
        """Прогнозирование цены для задачи."""
        start_time = time.time()

        try:
            # Предобработка данных
            features = self._preprocess_product_data(task.product_data)

            # Прогнозирование
            predicted_price = float(self.model.predict(features)[0])

            # Вычисление доверительного интервала (упрощенно)
            confidence_score = min(1.0, max(0.1, 1.0 - abs(predicted_price - 50) / 100))

            # Ценовой диапазон (±20% от прогноза)
            price_range = {
                "min": round(predicted_price * 0.8, 2),
                "max": round(predicted_price * 1.2, 2)
            }

            # Анализ по категории
            category_analysis = {
                "category": task.product_data.get("category_name", "Unknown"),
                "brand": task.product_data.get("brand_name", "Unknown"),
                "condition_impact": self._analyze_condition(task.product_data.get("item_condition_id", 1)),
                "shipping_impact": "Included" if task.product_data.get("shipping", 0) == 1 else "Extra cost"
            }

            processing_time = time.time() - start_time

            result = PricingResult(
                task_id=task.task_id,
                predicted_price=round(predicted_price, 2),
                confidence_score=round(confidence_score, 3),
                price_range=price_range,
                category_analysis=category_analysis,
                processing_time=round(processing_time, 3),
                worker_id=self.worker_id
            )

            logger.info(f"Task {task.task_id} completed in {processing_time:.3f}s: ${predicted_price:.2f}")
            return result

        except Exception as e:
            logger.error(f"Error predicting price for task {task.task_id}: {e}")
            raise

    def _analyze_condition(self, condition_id: int) -> str:
        """Анализ влияния состояния товара на цену."""
        condition_map = {
            1: "New - Premium pricing",
            2: "Like New - High pricing",
            3: "Good - Standard pricing",
            4: "Fair - Reduced pricing",
            5: "Poor - Significant discount"
        }
        return condition_map.get(condition_id, "Unknown condition")

    def _send_result(self, result: PricingResult):
        """Отправка результата через RabbitMQ."""
        try:
            message = {
                "task_id": result.task_id,
                "predicted_price": result.predicted_price,
                "confidence_score": result.confidence_score,
                "price_range": result.price_range,
                "category_analysis": result.category_analysis,
                "processing_time": result.processing_time,
                "worker_id": result.worker_id,
                "timestamp": time.time()
            }

            self.rabbitmq_channel.basic_publish(
                exchange="pricing_results",
                routing_key="prediction",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    timestamp=int(time.time())
                )
            )

            logger.info(f"Result sent for task {result.task_id}")

        except Exception as e:
            logger.error(f"Failed to send result for task {result.task_id}: {e}")
            raise

    def _process_task(self, task_data: str) -> None:
        """Обработка одной задачи."""
        try:
            task_info = json.loads(task_data)
            task = PricingTask(
                task_id=task_info["task_id"],
                product_data=task_info["product_data"],
                callback_queue=task_info.get("callback_queue")
            )

            # Прогнозирование
            result = self._predict_price(task)

            # Отправка результата
            self._send_result(result)

        except Exception as e:
            logger.error(f"Error processing task: {e}")

    def run(self):
        """Основной цикл воркера."""
        logger.info(f"Starting ML Worker {self.worker_id}")

        task_queue = os.getenv("TASK_QUEUE", "pricing_tasks")
        batch_size = int(os.getenv("BATCH_SIZE", "10"))
        poll_timeout = int(os.getenv("POLL_TIMEOUT", "1"))

        while self.is_running:
            try:
                # Получаем задачи из Redis
                tasks = self.redis_client.lpop(task_queue, count=batch_size)

                if not tasks:
                    time.sleep(poll_timeout)
                    continue

                # Ensure tasks is a list
                if isinstance(tasks, str):
                    tasks = [tasks]

                logger.info(f"Processing {len(tasks)} tasks")

                # Обрабатываем задачи параллельно
                futures = []
                for task_data in tasks:
                    future = self.executor.submit(self._process_task, task_data)
                    futures.append(future)

                # Ждем завершения всех задач
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Task processing failed: {e}")

            except redis.RedisError as e:
                logger.error(f"Redis error: {e}")
                time.sleep(5)  # Ждем перед повторной попыткой

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(1)

        self._cleanup()
        logger.info(f"ML Worker {self.worker_id} stopped")

    def _cleanup(self):
        """Очистка ресурсов."""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)

            if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                self.rabbitmq_connection.close()

            if self.redis_client:
                self.redis_client.close()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Запуск ML воркера."""
    logger.info("Starting ML Worker...")

    try:
        worker = ScalableMLWorker()
        worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
