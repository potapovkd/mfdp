# Marketplace Price Optimization System

Система оптимизации цен для маркетплейса на основе машинного обучения с использованием CatBoost модели.

## Архитектура

### Основные компоненты
- **API Gateway**: FastAPI приложение с REST endpoints
- **PostgreSQL**: База данных для хранения товаров и прогнозов
- **ML Model**: CatBoost модель для прогнозирования цен (RMSE ~35$)
- **WebUI**: Streamlit интерфейс для пользователей
- **Масштабируемые ML Воркеры**: Redis + RabbitMQ для обработки задач
- **Мониторинг**: Prometheus + Grafana для метрик

### Domain-Driven Design
- **Domain Layer**: Бизнес-модели (Product, PricePrediction, User)
- **Service Layer**: Сервисы приложения (ProductService, PricingService)
- **Repository Layer**: Доступ к данным (ORM, адаптеры)
- **API Layer**: REST endpoints и зависимости

## Требования системы

### Системные требования
- **Docker**: версия 20.10+
- **Docker Compose**: версия 2.0+
- **Python**: 3.9+ (для локальной разработки)
- **Память**: минимум 4GB RAM
- **Диск**: минимум 2GB свободного места



## Быстрый старт

### 1. Клонирование и подготовка
```bash
# Клонирование репозитория
git clone <repository-url>
cd ml-ops-final

# Проверка структуры проекта
ls -la
```

### 2. Запуск основной системы
```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса сервисов
docker-compose ps

# Доступ к сервисам через nginx:
# - WebUI: http://localhost (основной интерфейс)
# - API: http://localhost/api/v1/
# - API документация: http://localhost/api/docs
# - API ReDoc: http://localhost/api/redoc
# - Health check: http://localhost/health
# - Grafana: http://localhost:3000 (admin/admin)
# - PostgreSQL: localhost:5432
# - RabbitMQ UI: http://localhost:15672 (pricing/pricing123)
# - Prometheus: http://localhost:9090
```

### 3. Масштабирование ML воркеров

#### Запуск с масштабированием
```bash
# Запуск с 5 ML воркерами
docker-compose up --scale ml-worker=5

# Или 10 воркерами для высокой нагрузки
docker-compose up --scale ml-worker=10

# Проверка запущенных воркеров
docker ps | grep ml-worker
```

#### Отдельные ML воркеры
```bash
# Переход в директорию воркеров
cd ml_worker/

# Запуск кластера воркеров
docker-compose -f docker-compose.workers.yaml up --scale ml-worker=8

# Мониторинг очередей
# - Redis: localhost:6379
# - RabbitMQ UI: http://localhost:15672 (pricing/pricing123)
```

#### Проверка масштабирования
```bash
# Просмотр запущенных воркеров
docker ps | grep ml-worker

# Логи воркеров
docker-compose logs ml-worker

# Мониторинг производительности
docker stats

# Статистика очередей
curl http://localhost/api/v1/pricing/info/
```

### 4. Переменные масштабирования

В `docker-compose.yaml`:
```yaml
ml-worker:
  environment:
    WORKER_THREADS: "4"     # Потоки на воркер
    BATCH_SIZE: "5"         # Размер batch'а задач  
    POLL_TIMEOUT: "1"       # Таймаут опроса очереди
  deploy:
    replicas: 2             # Количество реплик
    resources:
      limits:
        cpus: '1.0'         # Лимит CPU
        memory: 1G          # Лимит памяти
```

## Тестирование

### Запуск тестов
```bash
# Переход в директорию с тестами
cd src/

# Установка зависимостей для разработки
pip install -r ../requirements.dev.txt

# Запуск всех тестов
python -m pytest tests/ -v

# Запуск конкретных тестов
python -m pytest tests/test_e2e.py -v
python -m pytest tests/test_integration.py -v
python -m pytest tests/test_user_api.py -v

# Запуск с покрытием
python -m pytest tests/ --cov=src --cov-report=html
```

### Типы тестов
- **Unit тесты**: `test_db.py`, `test_user_api.py`
- **Integration тесты**: `test_integration.py`
- **E2E тесты**: `test_e2e.py`
- **API тесты**: тестирование всех endpoints

### Тестирование в Docker
```bash
# Запуск тестов в контейнере
docker-compose exec api python -m pytest tests/ -v

# Тестирование с новой базой данных
docker-compose down -v
docker-compose up -d
docker-compose exec api python -m pytest tests/ -v
```

## ML Модель

### Характеристики
- **Тип**: CatBoost Regressor  
- **Точность**: RMSE ~35$ на тестовых данных
- **Признаки**: 66 features (TF-IDF + категориальные + текстовые метрики)
- **Время ответа**: <1 секунда на прогноз

### Обучение модели
```bash
# Обучение новой модели
cd src/pricing/
python quick_train.py

# Модель сохраняется в models/
# - catboost_pricing_model.cbm
# - preprocessing_pipeline.pkl
```

### Проверка модели
```bash
# Тестирование модели
cd src/pricing/
python -c "
from model_trainer import PricingModelTrainer
trainer = PricingModelTrainer()
trainer.evaluate_model()
"
```

## Мониторинг и метрики

### Производительность ML воркеров
- **Queue Length**: Длина очереди задач в Redis
- **Active Workers**: Количество активных воркеров
- **Processing Time**: Время обработки задач
- **Throughput**: Задач в секунду

### Мониторинг
```bash
# Prometheus метрики
curl http://localhost:9090/metrics

# Статистика очередей
curl http://localhost/api/v1/pricing/info/

# RabbitMQ Management UI
open http://localhost:15672

# Grafana Dashboard
open http://localhost:3000
```

### Логи и отладка
```bash
# Логи API
docker-compose logs api

# Логи ML воркеров
docker-compose logs ml-worker

# Логи базы данных
docker-compose logs db

# Все логи
docker-compose logs -f
```

## Примеры использования

### API для прогнозирования
```bash
# Регистрация пользователя
curl -X POST "http://localhost/api/v1/users/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Получение токена
curl -X POST "http://localhost/api/v1/users/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

# Пополнение баланса
curl -X POST "http://localhost/api/v1/users/deposit/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.0}'

# Прогноз цены товара
curl -X POST "http://localhost/api/v1/pricing/predict/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_data": {
      "name": "iPhone 13 Pro",
      "item_description": "Brand new iPhone 13 Pro 128GB",
      "category_name": "Electronics", 
      "brand_name": "Apple",
      "item_condition_id": 1,
      "shipping": 1
    }
  }'

# Ответ:
# {
#   "predicted_price": 847.52,
#   "confidence_score": 0.89,
#   "price_range": {"min": 678.02, "max": 1017.02},
#   "category_analysis": {...}
# }
```

### WebUI
1. Перейти на http://localhost:8001
2. Зарегистрироваться/войти
3. Пополнить баланс ($5 за прогноз)
4. Добавить товар или сделать прогноз

### Управление товарами
```bash
# Получение списка товаров
curl -X GET "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Добавление товара
curl -X POST "http://localhost/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro",
    "description": "Apple MacBook Pro 13-inch",
    "category": "Electronics",
    "brand": "Apple",
    "condition": "New"
  }'
```

## Разработка

### Локальная разработка
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
pip install -r requirements.dev.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактировать .env файл

# Запуск базы данных
docker-compose up -d db redis rabbitmq

# Запуск приложения
cd src/
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Структура проекта
```
ml-ops-final/
├── src/                     # Основное приложение
│   ├── products/           # Товары и ценообразование  
│   │   ├── domain/         # Доменные модели
│   │   ├── services/       # Бизнес-логика
│   │   ├── adapters/       # Адаптеры данных
│   │   └── entrypoints/    # API endpoints
│   ├── users/              # Пользователи
│   ├── pricing/            # ML сервисы
│   ├── base/               # Базовые классы
│   └── tests/              # Тесты
├── ml_worker/              # Масштабируемые ML воркеры
│   ├── worker.py           # Основной воркер
│   ├── Dockerfile          # Контейнер воркера
│   └── docker-compose.workers.yaml
├── webui/                  # Streamlit интерфейс
├── models/                 # Обученные ML модели
├── data/                   # Данные для обучения
├── experiments/            # Jupyter notebooks
└── docker-compose.yaml     # Основная оркестрация
```

### Добавление нового воркера
1. Скопировать `ml_worker/worker.py`
2. Модифицировать для новой задачи
3. Обновить `docker-compose.yaml`
4. Масштабировать: `--scale new-worker=N`

### Отладка
```bash
# Подключение к контейнеру
docker-compose exec api bash
docker-compose exec ml-worker bash

# Просмотр логов в реальном времени
docker-compose logs -f api
docker-compose logs -f ml-worker

# Проверка состояния базы данных
docker-compose exec db psql -U pricing_user -d pricing_optimization
```

## Безопасность

- JWT аутентификация
- Проверка баланса пользователей
- Валидация входных данных
- Ограничения на ресурсы контейнеров
- HTTPS через nginx (в продакшене)

## Масштабирование в продакшене

### Горизонтальное масштабирование
```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yaml pricing-stack

# Kubernetes
kubectl apply -f k8s/
kubectl scale deployment ml-worker --replicas=20
```

### Оптимизация производительности
- Настройка размера batch'ей
- Оптимизация количества потоков
- Мониторинг использования ресурсов
- Load balancing между воркерами

### Мониторинг в продакшене
```bash
# Настройка алертов в Grafana
# Мониторинг метрик через Prometheus
# Логирование через ELK Stack
```

## Устранение неполадок

### Частые проблемы

#### Сервисы не запускаются
```bash
# Проверка логов
docker-compose logs

# Пересборка образов
docker-compose build --no-cache

# Очистка volumes
docker-compose down -v
docker-compose up -d
```

#### ML воркеры не работают
```bash
# Проверка очередей
curl http://localhost/api/v1/pricing/info/

# Проверка Redis
docker-compose exec redis redis-cli ping

# Проверка RabbitMQ
docker-compose exec rabbitmq rabbitmqctl status
```

#### Проблемы с базой данных
```bash
# Проверка подключения
docker-compose exec db psql -U pricing_user -d pricing_optimization -c "SELECT 1;"

# Сброс базы данных
docker-compose down -v
docker-compose up -d db
```

## Поддержка

- **Логи воркеров**: `ml_worker/logs/`
- **Метрики**: Prometheus + Grafana
- **Статус очередей**: RabbitMQ Management UI
- **Документация API**: http://localhost/api/docs

### Полезные команды
```bash
# Полная перезагрузка системы
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Проверка здоровья системы
curl http://localhost/health
curl http://localhost/api/v1/pricing/info/

# Очистка системы
docker system prune -a
docker volume prune
```