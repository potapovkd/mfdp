# Marketplace Price Optimization System

Система оптимизации цен для маркетплейса на основе машинного обучения с использованием CatBoost модели.

## 🆕 Новые функции (v2.0)

### 💰 Тарифная система и баланс
- **Баланс пользователя** - каждый пользователь имеет персональный баланс
- **Тарификация запросов** - $5 за один прогноз, скидки для bulk запросов
- **Пополнение баланса** - возможность пополнения через API
- **Автоматическое списание** - средства списываются при выполнении прогнозов

### 📁 Загрузка товаров из Excel
- **Шаблон Excel** - скачивание готового шаблона с инструкциями
- **Массовая загрузка** - загрузка множества товаров из Excel файла
- **Валидация данных** - проверка обязательных полей и форматов
- **Обработка ошибок** - детальный отчет об ошибках при загрузке

### 🔮 Множественное прогнозирование
- **Выбор товаров** - множественный выбор из списка пользователя
- **Bulk прогнозирование** - прогноз для множества товаров одним запросом
- **Экспорт результатов** - выгрузка результатов в Excel файл
- **Скидки для bulk** - 20% скидка при 10+ товарах

### 📊 Улучшенный интерфейс
- **Новый раздел "Баланс и тарифы"** - управление балансом и просмотр тарифов
- **Калькулятор стоимости** - расчет стоимости для любого количества товаров
- **Множественный выбор** - удобный интерфейс для выбора товаров
- **Экспорт результатов** - кнопка для выгрузки результатов в Excel

## Архитектура

### Основные компоненты
- **API Gateway**: FastAPI приложение с REST endpoints
- **PostgreSQL**: База данных для хранения товаров, прогнозов и балансов
- **ML Model**: CatBoost модель для прогнозирования цен (RMSE ~35$)
- **WebUI**: Streamlit интерфейс для пользователей
- **Масштабируемые ML Воркеры**: Redis + RabbitMQ для обработки задач
- **Мониторинг**: Prometheus + Grafana для метрик

### Domain-Driven Design
- **Domain Layer**: Бизнес-модели (Product, PricePrediction, User, Billing)
- **Service Layer**: Сервисы приложения (ProductService, PricingService, UserService)
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

## Тарифная система

### Стоимость услуг
- **Одиночный прогноз**: $5.00
- **Bulk прогноз (10+ товаров)**: 20% скидка
- **Анализ товара**: Бесплатно
- **Загрузка товаров**: Бесплатно

### Примеры расчета стоимости
```bash
# 1 товар = $5.00
# 5 товаров = $25.00
# 10 товаров = $40.00 (скидка 20%)
# 20 товаров = $80.00 (скидка 20%)
# 100 товаров = $400.00 (скидка 20%)
```

### Управление балансом
```bash
# Проверка баланса
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/v1/users/balance/

# Пополнение баланса
curl -X POST "http://localhost/api/v1/users/balance/add/?amount=50.00" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Получение тарифов
curl http://localhost/api/v1/users/tariffs/

# Расчет стоимости
curl -X POST "http://localhost/api/v1/users/calculate-cost/?items_count=15"
```

## Работа с Excel файлами

### Скачивание шаблона
```bash
# Скачать шаблон Excel
curl http://localhost/api/v1/users/products/template/ \
  -o products_template.xlsx
```

### Структура Excel файла
| Поле | Описание | Обязательное | Пример |
|------|----------|--------------|---------|
| name | Название товара | Да | iPhone 13 Pro 128GB |
| item_description | Описание товара | Нет | Отличное состояние |
| category_name | Категория | Да | Electronics |
| brand_name | Бренд | Нет | Apple |
| item_condition_id | Состояние (1-5) | Нет | 2 |
| shipping | Доставка (0/1) | Нет | 1 |

### Загрузка товаров
```bash
# Загрузка Excel файла
curl -X POST "http://localhost/api/v1/products/upload-excel/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.xlsx"
```

## Множественное прогнозирование

### Выбор товаров для прогноза
```bash
# Получение списка товаров пользователя
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/v1/products/

# Прогнозирование для множества товаров
curl -X POST "http://localhost/api/v1/products/pricing/predict-multiple/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4, 5]'
```

### Экспорт результатов
```bash
# Экспорт результатов в Excel
curl -X POST "http://localhost/api/v1/products/pricing/export-results/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[...results...]'
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

### Регистрация и пополнение баланса
```bash
# Регистрация пользователя
curl -X POST "http://localhost/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Получение токена
curl -X POST "http://localhost/api/v1/users/auth/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Пополнение баланса
curl -X POST "http://localhost/api/v1/users/balance/add/?amount=100.00" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Работа с товарами
```bash
# Скачивание шаблона Excel
curl http://localhost/api/v1/users/products/template/ \
  -o template.xlsx

# Загрузка товаров из Excel
curl -X POST "http://localhost/api/v1/products/upload-excel/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.xlsx"

# Получение списка товаров
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost/api/v1/products/
```

### Прогнозирование цен
```bash
# Одиночный прогноз
curl -X POST "http://localhost/api/v1/products/pricing/predict/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_data": {
      "name": "iPhone 13 Pro 128GB",
      "item_description": "Отличное состояние, полный комплект",
      "category_name": "Electronics",
      "brand_name": "Apple",
      "item_condition_id": 2,
      "shipping": 1
    }
  }'

# Множественный прогноз
curl -X POST "http://localhost/api/v1/products/pricing/predict-multiple/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3, 4, 5]'
```

## API Endpoints

### Пользователи
- `POST /api/v1/users/` - Регистрация
- `POST /api/v1/users/auth/` - Авторизация
- `GET /api/v1/users/balance/` - Получение баланса
- `POST /api/v1/users/balance/add/` - Пополнение баланса
- `GET /api/v1/users/tariffs/` - Получение тарифов
- `POST /api/v1/users/calculate-cost/` - Расчет стоимости
- `GET /api/v1/users/products/template/` - Скачивание шаблона Excel

### Товары
- `GET /api/v1/products/` - Список товаров
- `POST /api/v1/products/` - Создание товара
- `POST /api/v1/products/upload-excel/` - Загрузка из Excel
- `GET /api/v1/products/{id}/` - Детали товара
- `POST /api/v1/products/pricing/predict/` - Одиночный прогноз
- `POST /api/v1/products/pricing/predict-multiple/` - Множественный прогноз
- `POST /api/v1/products/pricing/export-results/` - Экспорт результатов
- `GET /api/v1/products/pricing/info/` - Информация о сервисе
- `POST /api/v1/products/pricing/analyze/` - Анализ товара

## Ключевые преимущества

1. **Высокая точность** - RMSE ~35$ благодаря CatBoost модели
2. **Масштабируемость** - поддержка высоких нагрузок через ML воркеры
3. **Тарифная система** - гибкая система оплаты с скидками
4. **Массовая обработка** - загрузка и прогнозирование множества товаров
5. **Удобный интерфейс** - интуитивный Web интерфейс с новыми функциями
6. **Мониторинг** - полная видимость производительности системы
7. **Надежность** - graceful shutdown, восстановление после сбоев
8. **Экспорт данных** - выгрузка результатов в Excel формат

Система готова к использованию в продакшене и может быть легко масштабирована под потребности бизнеса.