"""Сервис для работы с очередями задач."""

import json
import logging
import time
from typing import Any, Dict, Optional
from datetime import datetime

import redis
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from redis.exceptions import RedisError

from base.config import get_settings
from base.exceptions import TaskQueueError

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskQueueService:
    """Сервис для работы с очередями задач."""

    def __init__(self):
        """Инициализация сервиса."""
        self.redis_client = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self._setup_connections()

    def _setup_connections(self) -> None:
        """Настройка подключений к Redis и RabbitMQ."""
        try:
            # Redis для очередей задач
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {settings.redis_host}:{settings.redis_port}")

            # RabbitMQ для результатов
            credentials = pika.PlainCredentials(
                settings.rabbitmq_user,
                settings.rabbitmq_pass
            )
            parameters = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5
            )
            self.rabbitmq_connection = pika.BlockingConnection(parameters)
            self.rabbitmq_channel = self.rabbitmq_connection.channel()

            # Объявляем exchange и очереди
            self._setup_rabbitmq_topology()
            logger.info(f"Connected to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")

        except (RedisError, AMQPConnectionError) as e:
            logger.error(f"Failed to setup connections: {e}")
            raise TaskQueueError(f"Failed to setup queue connections: {str(e)}")

    def _setup_rabbitmq_topology(self) -> None:
        """Настройка топологии RabbitMQ."""
        try:
            # Основной exchange для результатов
            self.rabbitmq_channel.exchange_declare(
                exchange="pricing_results",
                exchange_type="direct",
                durable=True
            )

            # Очередь для результатов
            self.rabbitmq_channel.queue_declare(
                queue="pricing_results",
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 часа
                    "x-max-length": 10000,
                    "x-overflow": "reject-publish"
                }
            )

            # Привязка очереди к exchange
            self.rabbitmq_channel.queue_bind(
                exchange="pricing_results",
                queue="pricing_results",
                routing_key="prediction"
            )

            # Dead Letter Exchange для неудачных задач
            self.rabbitmq_channel.exchange_declare(
                exchange="pricing_dlx",
                exchange_type="direct",
                durable=True
            )

            # Dead Letter Queue
            self.rabbitmq_channel.queue_declare(
                queue="pricing_failed",
                durable=True,
                arguments={
                    "x-message-ttl": 604800000,  # 7 дней
                    "x-max-length": 1000,
                    "x-overflow": "reject-publish"
                }
            )

            self.rabbitmq_channel.queue_bind(
                exchange="pricing_dlx",
                queue="pricing_failed",
                routing_key="failed"
            )

        except AMQPChannelError as e:
            logger.error(f"Failed to setup RabbitMQ topology: {e}")
            raise TaskQueueError(f"Failed to setup RabbitMQ topology: {str(e)}")

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
                "attempts": 0
            }

            # Добавляем в Redis
            self.redis_client.rpush(
                "pricing_tasks",
                json.dumps(task_data)
            )
            logger.info(f"Task {task_id} added to queue")

        except Exception as e:
            logger.error(f"Failed to add task {task_id}: {e}")
            raise TaskQueueError(f"Failed to add task: {str(e)}")

    async def get_result(self, task_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Получение результата задачи."""
        try:
            self._ensure_connections()

            start_time = time.time()
            while time.time() - start_time < timeout:
                # Проверяем результат в Redis
                result = self.redis_client.get(f"result:{task_id}")
                if result:
                    self.redis_client.delete(f"result:{task_id}")
                    return json.loads(result)

                # Проверяем ошибки
                error = self.redis_client.get(f"error:{task_id}")
                if error:
                    self.redis_client.delete(f"error:{task_id}")
                    raise TaskQueueError(f"Task failed: {error}")

                time.sleep(0.5)

            return None

        except Exception as e:
            logger.error(f"Failed to get result for task {task_id}: {e}")
            raise TaskQueueError(f"Failed to get task result: {str(e)}")

    async def cleanup(self) -> None:
        """Очистка старых задач и результатов."""
        try:
            self._ensure_connections()

            # Очищаем старые результаты (старше 24 часов)
            keys = self.redis_client.keys("result:*")
            for key in keys:
                if self.redis_client.ttl(key) < 0:
                    self.redis_client.delete(key)

            # Очищаем старые ошибки (старше 7 дней)
            keys = self.redis_client.keys("error:*")
            for key in keys:
                if self.redis_client.ttl(key) < 0:
                    self.redis_client.delete(key)

            logger.info("Queue cleanup completed")

        except Exception as e:
            logger.error(f"Failed to cleanup queues: {e}")
            raise TaskQueueError(f"Failed to cleanup queues: {str(e)}")

    def __del__(self):
        """Закрытие соединений при удалении объекта."""
        try:
            if self.redis_client:
                self.redis_client.close()

            if self.rabbitmq_channel and not self.rabbitmq_channel.is_closed:
                self.rabbitmq_channel.close()

            if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                self.rabbitmq_connection.close()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
