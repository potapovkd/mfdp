"""Сервис для управления очередью задач ML воркеров.
Интегрирует основное приложение с масштабируемыми ML воркерами.
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional

import redis.asyncio as redis
import pika
from loguru import logger

from base.config import get_config
from products.domain.models import ProductData, PricingResponse


class TaskQueueService:
    """Сервис для управления очередями задач ML воркеров."""

    def __init__(self):
        self.config = get_config()
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

    async def _get_redis_client(self) -> redis.Redis:
        """Получение асинхронного Redis клиента."""
        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=self.config.redis_host or "redis",
                port=self.config.redis_port or 6379,
                db=self.config.redis_db or 0,
                decode_responses=True
            )
        return self.redis_client

    def _get_rabbitmq_channel(self):
        """Получение канала RabbitMQ для прослушивания результатов."""
        if not self.rabbitmq_connection or self.rabbitmq_connection.is_closed:
            self.rabbitmq_connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config.rabbitmq_host or "rabbitmq",
                    port=self.config.rabbitmq_port or 5672
                )
            )
            self.rabbitmq_channel = self.rabbitmq_connection.channel()

            # Объявляем exchange и очередь для результатов
            self.rabbitmq_channel.exchange_declare(
                exchange="pricing_results",
                exchange_type="direct",
                durable=True
            )

        return self.rabbitmq_channel

    async def submit_pricing_task(
        self,
        task_id: str,
        product_data: ProductData
    ) -> bool:
        """Отправка задачи на прогнозирование цены в очередь."""
        try:
            redis_client = await self._get_redis_client()

            task_data = {
                "task_id": task_id,
                "product_data": product_data.model_dump(),
                "timestamp": time.time()
            }

            task_queue = self.config.task_queue or "pricing_tasks"

            # Отправляем задачу в Redis очередь
            await redis_client.rpush(task_queue, json.dumps(task_data))

            logger.info(f"Task {task_id} submitted to queue {task_queue}")
            return True

        except Exception as e:
            logger.error(f"Failed to submit task {task_id}: {e}")
            return False

    async def get_task_result(
        self,
        task_id: str,
        timeout: int = 30
    ) -> Optional[PricingResponse]:
        """Получение результата задачи с таймаутом."""
        try:
            # Создаем временную очередь для результата
            result_queue = f"result_{task_id}"

            channel = self._get_rabbitmq_channel()

            # Объявляем временную очередь
            channel.queue_declare(
                queue=result_queue,
                exclusive=True,
                auto_delete=True
            )

            # Привязываем к exchange
            channel.queue_bind(
                exchange="pricing_results",
                queue=result_queue,
                routing_key="prediction"
            )

            received_result = None

            def callback(ch, method, properties, body):
                nonlocal received_result
                try:
                    message = json.loads(body)
                    if message.get("task_id") == task_id:
                        received_result = message
                        ch.stop_consuming()
                except Exception as e:
                    logger.error(f"Error processing result: {e}")

            # Настраиваем консьюмер
            channel.basic_consume(
                queue=result_queue,
                on_message_callback=callback,
                auto_ack=True
            )

            # Ждем результат с таймаутом
            start_time = time.time()
            while time.time() - start_time < timeout and not received_result:
                channel.connection.process_data_events(time_limit=1)
                await asyncio.sleep(0.1)

            if received_result:
                # Конвертируем в PricingResponse
                pricing_response = PricingResponse(
                    predicted_price=received_result["predicted_price"],
                    confidence_score=received_result["confidence_score"],
                    price_range=received_result["price_range"],
                    category_analysis=received_result["category_analysis"]
                )

                logger.info(
                    f"Task {task_id} result received from worker "
                    f"{received_result.get('worker_id', 'unknown')}"
                )
                return pricing_response

            logger.warning(f"Task {task_id} result not received within {timeout}s")
            return None

        except Exception as e:
            logger.error(f"Error getting task result for {task_id}: {e}")
            return None
        finally:
            try:
                if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                    self.rabbitmq_connection.close()
                    self.rabbitmq_connection = None
                    self.rabbitmq_channel = None
            except Exception:
                pass

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Получение статистики очередей."""
        try:
            redis_client = await self._get_redis_client()
            task_queue = self.config.task_queue or "pricing_tasks"

            # Получаем длину очереди
            queue_length = await redis_client.llen(task_queue)

            # Получаем информацию о воркерах (примерно)
            worker_keys = await redis_client.keys("worker:*:heartbeat")
            active_workers = len(worker_keys)

            return {
                "queue_length": queue_length,
                "active_workers": active_workers,
                "queue_name": task_queue,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {
                "queue_length": -1,
                "active_workers": -1,
                "error": str(e)
            }

    async def cleanup(self):
        """Очистка ресурсов."""
        try:
            if self.redis_client:
                await self.redis_client.close()

            if self.rabbitmq_connection and not self.rabbitmq_connection.is_closed:
                self.rabbitmq_connection.close()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Singleton instance
task_queue_service = TaskQueueService()
