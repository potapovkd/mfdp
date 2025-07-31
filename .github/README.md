# GitHub Actions CI/CD Pipeline

Этот проект использует GitHub Actions для автоматизации тестирования, проверки качества кода и развертывания.

## Workflows

### 1. Tests (`tests.yml`)
**Триггеры:** Push в ветки `main`, `develop`, `refactor` и Pull Requests

**Что делает:**
- Устанавливает Python 3.12 и зависимости
- Запускает PostgreSQL, Redis, RabbitMQ как services
- Выполняет все тесты (unit, integration, E2E)
- Генерирует отчет о покрытии кода
- Загружает отчет в Codecov

### 2. Docker Integration Tests (`docker-tests.yml`)
**Триггеры:** Push в ветки `main`, `develop` и Pull Requests в `main`

**Что делает:**
- Собирает Docker образы
- Запускает полный стек через docker-compose
- Тестирует ML Worker в реальном окружении
- Проверяет интеграцию всех компонентов

### 3. Code Quality (`code-quality.yml`)
**Триггеры:** Push в ветки `main`, `develop`, `refactor` и Pull Requests

**Что делает:**
- Проверяет форматирование кода (Black)
- Проверяет сортировку импортов (isort)
- Анализирует код на ошибки (flake8)
- Проверяет типы (mypy)
- Сканирует безопасность (bandit, safety)

### 4. Deploy to Production (`deploy.yml`)
**Триггеры:** Push в ветку `main` или теги `v*`

**Что делает:**
- Собирает и публикует Docker образы
- Развертывает на production (требует настройки)
- Выполняет health check
- Отправляет уведомления

## Настройка

### 1. Секреты GitHub
Добавьте следующие секреты в настройки репозитория:

```
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
```

### 2. Codecov (опционально)
1. Зарегистрируйтесь на [codecov.io](https://codecov.io)
2. Подключите ваш репозиторий
3. Токен будет добавлен автоматически

### 3. Production Environment
Для автоматического deployment настройте:
1. Production environment в GitHub
2. SSH ключи для доступа к серверу
3. Адрес production сервера

## Локальный запуск проверок

### Проверка качества кода
```bash
# Форматирование
black src/

# Сортировка импортов
isort src/

# Линтинг
flake8 src/

# Проверка типов
mypy src/

# Проверка безопасности
bandit -r src/
```

### Запуск тестов
```bash
# Все тесты
pytest src/tests/ -v

# С покрытием
pytest src/tests/ --cov=src/ --cov-report=html

# Параллельно
pytest src/tests/ -n auto
```

## Статусы Badges

Добавьте в README.md:

```markdown
![Tests](https://github.com/your-username/ml-ops-final/workflows/Tests/badge.svg)
![Code Quality](https://github.com/your-username/ml-ops-final/workflows/Code%20Quality/badge.svg)
![Docker Tests](https://github.com/your-username/ml-ops-final/workflows/Docker%20Integration%20Tests/badge.svg)
[![codecov](https://codecov.io/gh/your-username/ml-ops-final/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/ml-ops-final)
```

## Troubleshooting

### Тесты падают в CI
1. Проверьте логи GitHub Actions
2. Убедитесь, что все сервисы запускаются корректно
3. Проверьте переменные окружения
4. Запустите тесты локально в Docker

### Проблемы с качеством кода
1. Запустите `black src/` для форматирования
2. Запустите `isort src/` для сортировки импортов
3. Исправьте ошибки flake8 и mypy

### Проблемы с Docker
1. Проверьте Dockerfile и docker-compose.yml
2. Убедитесь, что все пути корректны
3. Проверьте доступность портов

## Конфигурационные файлы

- `.flake8` - настройки линтера
- `pyproject.toml` - настройки Black, isort, mypy, coverage
- `pytest.ini` - настройки pytest
- `requirements.dev.txt` - зависимости для разработки 