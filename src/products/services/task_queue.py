"""Сервис для работы с очередью задач."""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pika
import redis
from pika.exceptions import AMQPConnectionError

from base.config import get_settings
from base.exceptions import TaskQueueError

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskQueueService:
    """Сервис для работы с очередью задач."""

    def __init__(self):
        """Инициализация сервиса."""
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self._setup_connections()

    def _setup_connections(self) -> None:
        """Настройка подключений к Redis и RabbitMQ."""
        try:
            # Подключение к Redis
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info(
                f"Connected to Redis at {settings.redis_host}:{settings.redis_port}"
            )

            # Подключение к RabbitMQ
            credentials = pika.PlainCredentials(
                settings.rabbitmq_user, settings.rabbitmq_pass
            )
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.rabbitmq_connection = pika.BlockingConnection(parameters)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            logger.info(
                f"Connected to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}"
            )

            # Настройка топологии RabbitMQ
            self._setup_rabbitmq_topology()

        except (redis.ConnectionError, AMQPConnectionError) as e:
            logger.error(f"Failed to setup connections: {e}")
            raise TaskQueueError(f"Connection setup failed: {str(e)}")

    def _setup_rabbitmq_topology(self) -> None:
        """Настройка топологии RabbitMQ."""
        # Основная очередь для результатов
        self.rabbitmq_channel.exchange_declare(
            exchange="pricing_results", exchange_type="direct", durable=True
        )
        self.rabbitmq_channel.queue_declare(
            queue="pricing_results",
            durable=True,
            arguments={
                "x-message-ttl": 86400000,  # 24 часа
                "x-max-length": 10000,
                "x-overflow": "reject-publish",
            },
        )

        # Dead Letter Exchange и очередь
        self.rabbitmq_channel.exchange_declare(
            exchange="pricing_dlx", exchange_type="direct", durable=True
        )
        self.rabbitmq_channel.queue_declare(
            queue="pricing_failed",
            durable=True,
            arguments={
                "x-message-ttl": 604800000,  # 7 дней
                "x-max-length": 1000,
                "x-overflow": "reject-publish",
            },
        )

    def _ensure_connections(self) -> None:
        """Проверка и восстановление подключений."""
        try:
            # Проверяем Redis
            if not self.redis_client or not self.redis_client.ping():
                logger.warning("Redis connection lost, reconnecting...")
                self._setup_connections()
                return

            # Проверяем RabbitMQ
            if not self.rabbitmq_connection or self.rabbitmq_connection.is_closed:
                logger.warning("RabbitMQ connection lost, reconnecting...")
                self._setup_connections()
                return

            if not self.rabbitmq_channel or self.rabbitmq_channel.is_closed:
                logger.warning("RabbitMQ channel closed, reopening...")
                self.rabbitmq_channel = self.rabbitmq_connection.channel()
                self._setup_rabbitmq_topology()

        except Exception as e:
            logger.error(f"Failed to ensure connections: {e}")
            raise TaskQueueError(f"Connection check failed: {str(e)}")

    async def add_task(self, task_id: str, product_data: Dict[str, Any]) -> None:
        """Добавление задачи в очередь."""
        try:
            self._ensure_connections()
            task_data = {
                "task_id": task_id,
                "product_data": product_data,
                "created_at": datetime.now().isoformat(),
                "attempts": 0,
            }
            self.redis_client.rpush("pricing_tasks", json.dumps(task_data))
            logger.info(f"Task {task_id} added to queue")
        except Exception as e:
            logger.error(f"Failed to add task {task_id}: {e}")
            raise TaskQueueError(f"Failed to add task: {str(e)}")

    async def get_result(
        self, task_id: str, timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Получение результата задачи."""
        try:
            self._ensure_connections()
            start_time = time.time()

            while time.time() - start_time < timeout:
                # Проверяем результат
                result = self.redis_client.get(f"result:{task_id}")
                if result:
                    self.redis_client.delete(f"result:{task_id}")
                    return json.loads(result)

                # Проверяем ошибку
                error = self.redis_client.get(f"error:{task_id}")
                if error:
                    self.redis_client.delete(f"error:{task_id}")
                    raise TaskQueueError(error.decode())

                time.sleep(0.5)

            return None

        except TaskQueueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get result for task {task_id}: {e}")
            raise TaskQueueError(f"Failed to get result: {str(e)}")

    async def cleanup(self) -> None:
        """Очистка старых задач."""
        try:
            self._ensure_connections()

            # Получаем все ключи результатов и ошибок
            result_keys = self.redis_client.keys("result:*")
            error_keys = self.redis_client.keys("error:*")

            # Удаляем старые ключи (TTL < 0)
            for key in result_keys + error_keys:
                if self.redis_client.ttl(key) < 0:
                    self.redis_client.delete(key)

            logger.info("Queue cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Закрытие соединений при удалении объекта."""
        try:
            if hasattr(self, "rabbitmq_channel"):
                self.rabbitmq_channel.close()
            if hasattr(self, "rabbitmq_connection"):
                self.rabbitmq_connection.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
