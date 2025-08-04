# Marketplace Price Optimization System

Система оптимизации цен для маркетплейса на основе машинного обучения с использованием CatBoost модели.

## �� Новые функции (v2.1)

### 🔄 **DVC интеграция с MinIO**
- **Версионирование моделей** - автоматическое управление версиями ML моделей через DVC
- **MinIO Remote Storage** - хранение моделей в S3-совместимом объектном хранилище
- **Автоматическая синхронизация** - модели автоматически загружаются при старте сервисов
- **Безопасная публикация** - новые модели автоматически сохраняются в MinIO после обучения

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
- **DVC + MinIO**: Версионирование и хранение ML моделей
- **Мониторинг**: Prometheus + Grafana для метрик

### Domain-Driven Design
- **Domain Layer**: Бизнес-модели (Product, PricePrediction, User, Billing)
- **Service Layer**: Сервисы приложения (ProductService, PricingService, UserService)
- **Repository Layer**: Доступ к данным (ORM, адаптеры)
- **API Layer**: REST endpoints и зависимости

## 🔄 DVC + MinIO: Управление моделями

### Что такое DVC интеграция?
DVC (Data Version Control) управляет версиями ML моделей, а MinIO предоставляет S3-совместимое объектное хранилище для их централизованного хранения.

### Преимущества интеграции
- **🔒 Централизованное хранение** - все модели в одном месте
- **📈 Версионирование** - отслеживание изменений моделей
- **🚀 Автоматическая синхронизация** - модели загружаются при старте сервисов
- **⚡ Быстрое развертывание** - новые версии моделей доступны мгновенно
- **🔄 Откат версий** - возможность вернуться к предыдущим версиям

### Архитектура DVC + MinIO
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Service   │    │   ML Worker     │    │     WebUI       │
│                 │    │                 │    │                 │
│  DVC Pull  ⬇️   │    │  DVC Pull  ⬇️   │    │  DVC Pull  ⬇️   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MinIO S3      │
                    │   (Remote)      │
                    │                 │
                    │ 📦 Models       │
                    │ 📦 Pipelines    │
                    └─────────────────┘
                                 ⬆️
                    ┌─────────────────┐
                    │  Model Training │
                    │                 │
                    │  DVC Push  ⬆️   │
                    └─────────────────┘
```

### Конфигурация DVC
Модели автоматически управляются через DVC с следующей конфигурацией:

```bash
# .dvc/config
[core]
    remote = ml_ops_bucket
['remote "ml_ops_bucket"']
    url = s3://potapow/final-project-models
    endpointurl = http://89.223.69.137:9000

# .dvc/config.local (credentials)
['remote "ml_ops_bucket"']
    access_key_id = <MinIO_ACCESS_KEY>
    secret_access_key = <MinIO_SECRET_KEY>
```

### Автоматические процессы
1. **При старте сервисов**: автоматический `dvc pull` для загрузки актуальных моделей
2. **При обучении модели**: автоматический `dvc push` для сохранения в MinIO
3. **При развертывании**: модели загружаются из MinIO, а не из локальных файлов

## Требования системы

### Системные требования
- **Docker**: версия 20.10+
- **Docker Compose**: версия 2.0+
- **Python**: 3.9+ (для локальной разработки)
- **Память**: минимум 4GB RAM
- **Диск**: минимум 2GB свободного места
- **Интернет**: доступ к MinIO серверу для загрузки моделей

### Новые зависимости
- **DVC[s3]**: версионирование данных с поддержкой S3
- **Git**: для работы DVC репозитория

## Быстрый старт

### 1. Клонирование и подготовка
```bash
# Клонирование репозитория
git clone <repository-url>
cd ml-ops-final

# Проверка структуры проекта
ls -la

# Проверка DVC конфигурации
cat .dvc/config
```

### 2. Настройка DVC credentials (если нужно)
```bash
# Создание .dvc/config.local с credentials
# (обычно уже настроен для тестирования)
```

### 3. Запуск основной системы
```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса сервисов
docker-compose ps

# Проверка загрузки моделей в логах
docker-compose logs api | grep -i dvc
docker-compose logs ml-worker | grep -i dvc

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

### 4. Масштабирование ML воркеров

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

### 5. Переменные масштабирования

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
- **Хранение**: Версионирование через DVC + MinIO

### 🔄 Управление моделями с DVC

#### Автоматическая загрузка моделей
При запуске каждого сервиса модели автоматически загружаются из MinIO:
```bash
# В логах сервисов вы увидите:
🔄 Загружаем модели из DVC remote storage...
✅ Модели успешно загружены из DVC
✅ Модель загружена из models/catboost_pricing_model.cbm
✅ Pipeline предобработки загружен из models/preprocessing_pipeline.pkl
```

#### Обучение новой модели
```bash
# Обучение новой модели с автоматической публикацией в MinIO
cd src/pricing/
python quick_train.py

# Процесс автоматически:
# 1. Обучает модель
# 2. Сохраняет локально в models/
#    - catboost_pricing_model.cbm
#    - preprocessing_pipeline.pkl
# 3. Добавляет в DVC (dvc add models)
# 4. Загружает в MinIO (dvc push)

# В выводе вы увидите:
🔄 Обновляем модели в DVC и загружаем в MinIO...
✅ Модели добавлены в DVC
✅ Модели успешно загружены в MinIO
```

#### Ручное управление моделями (опционально)
```bash
# Загрузка моделей из MinIO
dvc pull models.dvc

# Загрузка новых моделей в MinIO
dvc add models
dvc push models.dvc

# Откат к предыдущей версии модели
git checkout HEAD~1 models.dvc
dvc checkout models.dvc

# Просмотр истории изменений
git log --oneline models.dvc
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

# Проверка загрузки через DVC
python -c "
from pricing.pricing_service import PricingService
service = PricingService()
print('✅ Модель загружена!' if service.model else '❌ Ошибка загрузки')
"
```

### Статус моделей в системе
```bash
# Проверка статуса DVC
dvc status

# Информация о моделях
dvc list . models/

# Размер моделей в MinIO
dvc data status

# Проверка подключения к MinIO
dvc remote list
dvc remote -v list
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

# Проверка загрузки моделей через DVC
docker-compose logs api | grep -i dvc
docker-compose logs ml-worker | grep -i dvc
```

## 🔧 Диагностика DVC + MinIO

### Проверка подключения к MinIO
```bash
# Тест подключения к MinIO
dvc remote list
dvc remote -v list

# Проверка статуса моделей
dvc status models.dvc

# Информация о remote storage
dvc data status
```

### Распространенные проблемы и решения

#### ❌ Ошибка: "Unable to locate credentials"
```bash
# Проверьте наличие .dvc/config.local
ls -la .dvc/config.local

# Создайте файл с credentials (если отсутствует)
cat > .dvc/config.local << EOF
['remote "ml_ops_bucket"']
    access_key_id = gAJphVrgFEjIPuT8sDPp
    secret_access_key = i8Q9LvC4L58LHb6emO2ElF7Zd7Knyuk4Z87ps03S
EOF
```

#### ❌ Ошибка: "is not a git repository"
```bash
# Убедитесь что .git директория скопирована в Docker контейнер
# Проверьте Dockerfile:
COPY .git ./.git
COPY .dvc ./.dvc
```

#### ❌ Модели не загружаются при старте сервиса
```bash
# Проверьте логи загрузки моделей
docker-compose logs api | grep -E "(DVC|модел|model)"

# Ручная проверка в контейнере
docker-compose exec api dvc pull models.dvc
docker-compose exec api ls -la models/
```

#### ❌ Новые модели не сохраняются в MinIO
```bash
# Проверьте процесс обучения
cd src/pricing/
python quick_train.py 2>&1 | grep -E "(DVC|MinIO|models)"

# Ручная загрузка в MinIO
dvc add models
dvc push models.dvc
```

### Мониторинг DVC операций
```bash
# Включение подробных логов DVC
export DVC_LOG_LEVEL=DEBUG

# Проверка версий моделей
git log --oneline models.dvc

# Сравнение версий
dvc diff HEAD~1 models.dvc

# Размер моделей в MinIO
dvc cache dir --show
du -sh $(dvc cache dir --show)
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

1. **🎯 Высокая точность** - RMSE ~35$ благодаря CatBoost модели
2. **🚀 Масштабируемость** - поддержка высоких нагрузок через ML воркеры
3. **🔄 Версионирование моделей** - автоматическое управление версиями через DVC + MinIO
4. **☁️ Централизованное хранение** - модели хранятся в S3-совместимом объектном хранилище
5. **⚡ Быстрое развертывание** - автоматическая загрузка моделей при старте сервисов
6. **💰 Тарифная система** - гибкая система оплаты с скидками
7. **📦 Массовая обработка** - загрузка и прогнозирование множества товаров
8. **🖥️ Удобный интерфейс** - интуитивный Web интерфейс с новыми функциями
9. **📊 Мониторинг** - полная видимость производительности системы
10. **🛡️ Надежность** - graceful shutdown, восстановление после сбоев
11. **📄 Экспорт данных** - выгрузка результатов в Excel формат
12. **🔧 DevOps готовность** - полная интеграция с современными инструментами ML

### 🌟 Уникальные возможности DVC интеграции

- **🔁 Безшовное обновление** - новые модели доступны всем сервисам мгновенно
- **📈 Отслеживание экспериментов** - полная история изменений моделей
- **🔒 Безопасность** - централизованное управление доступом к моделям  
- **💾 Эффективность** - дедупликация и сжатие данных в MinIO
- **🌐 Отказоустойчивость** - модели доступны из любой точки инфраструктуры
- **🔄 Простой откат** - возврат к предыдущим версиям одной командой

Система готова к использованию в продакшене и может быть легко масштабирована под потребности бизнеса. **DVC интеграция обеспечивает enterprise-уровень управления ML моделями.**

---

## 🚀 Быстрый старт с DVC

Для тех, кто хочет быстро опробовать новую DVC интеграцию:

```bash
# 1. Клонируйте репозиторий
git clone <repository-url> && cd ml-ops-final

# 2. Проверьте что DVC настроен
cat .dvc/config

# 3. Запустите систему
docker-compose up -d

# 4. Убедитесь что модели загрузились из MinIO
docker-compose logs api | grep "✅ Модели успешно загружены из DVC"

# 5. Попробуйте веб-интерфейс
open http://localhost

# 6. (Опционально) Переобучите модель с автоматической публикацией
docker-compose exec api python src/pricing/quick_train.py
```

**🎉 Готово!** Теперь ваши модели автоматически версионируются и хранятся в MinIO, доступные всем сервисам системы.

---

## 📋 Changelog v2.1

### ✨ Новое
- DVC интеграция с MinIO для версионирования моделей
- Автоматическая загрузка моделей при старте сервисов  
- Автоматическая публикация моделей после обучения
- Централизованное хранение в S3-совместимом объектном хранилище

### 🔧 Технические улучшения
- Добавлена зависимость `dvc[s3]` во все сервисы
- Обновлены Dockerfile'ы для поддержки Git и DVC
- Улучшена обработка ошибок в predict endpoint
- Добавлены инструменты диагностики DVC

### 🐛 Исправления
- Исправлена ошибка 500 "Product not found" в predict endpoint
- Улучшена стабильность загрузки моделей в контейнерах