# Contributing Guide

Добро пожаловать в проект ML-Ops система ценовой оптимизации! Этот документ содержит правила и рекомендации для участия в разработке.

## Процесс разработки

### 1. Настройка окружения

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/ml-ops-final.git
cd ml-ops-final

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
make dev-install
```

### 2. Ветки и workflow

- `main` - production ветка (защищена)
- `develop` - основная ветка разработки
- `feature/название` - ветки для новых функций
- `bugfix/название` - ветки для исправлений
- `hotfix/название` - критические исправления

### 3. Процесс создания изменений

1. **Создайте ветку** от `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Внесите изменения** и регулярно коммитьте:
   ```bash
   git add .
   git commit -m "feat: добавлена новая функция"
   ```

3. **Проверьте качество кода**:
   ```bash
   make quality
   ```

4. **Запустите тесты**:
   ```bash
   make test
   ```

5. **Создайте Pull Request** в ветку `develop`

## Стандарты кода

### Форматирование
- Используем **Black** для форматирования Python кода
- Длина строки: 88 символов
- Используем **isort** для сортировки импортов

```bash
make format  # Автоматическое форматирование
```

### Линтинг
- **Flake8** для проверки стиля кода
- **mypy** для проверки типов
- **Bandit** для проверки безопасности

```bash
make lint      # Проверка стиля
make type-check # Проверка типов
make security  # Проверка безопасности
```

### Типизация
- Используйте type hints везде, где это возможно
- Для сложных типов используйте `typing` модуль

```python
from typing import List, Dict, Optional, Union

def process_data(items: List[Dict[str, Union[str, int]]]) -> Optional[Dict[str, float]]:
    """Обрабатывает данные и возвращает результат."""
    pass
```

## Стандарты коммитов

Используем [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): краткое описание

Более подробное описание (опционально)
```

### Типы коммитов:
- `feat`: новая функция
- `fix`: исправление бага
- `docs`: изменения в документации
- `style`: форматирование, отсутствующие точки с запятой и т.д.
- `refactor`: рефакторинг кода
- `test`: добавление или изменение тестов
- `chore`: обновление зависимостей, настройка CI и т.д.

### Примеры:
```
feat(api): добавлен endpoint для получения статистики
fix(worker): исправлена ошибка обработки задач
docs(readme): обновлена инструкция по установке
test(integration): добавлены тесты для API продуктов
```

## Тестирование

### Типы тестов
1. **Unit тесты** - тестируют отдельные функции/классы
2. **Integration тесты** - тестируют взаимодействие компонентов
3. **E2E тесты** - тестируют полные пользовательские сценарии

### Покрытие тестами
- Минимальное покрытие: 80%
- Проверка покрытия: `make test-cov`

### Написание тестов
```python
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    """Тесты для сервиса пользователей."""
    
    def test_create_user_success(self):
        """Тест успешного создания пользователя."""
        # Arrange
        user_data = {"email": "test@example.com", "password": "secret"}
        
        # Act
        result = create_user(user_data)
        
        # Assert
        assert result.email == "test@example.com"
        assert result.id is not None
```

## Pull Request Guidelines

### Чек-лист для PR
- [ ] Код отформатирован (`make format`)
- [ ] Все проверки качества проходят (`make quality`)
- [ ] Все тесты проходят (`make test`)
- [ ] Добавлены тесты для новой функциональности
- [ ] Обновлена документация (если необходимо)
- [ ] Коммиты следуют стандарту Conventional Commits

### Требования к PR
- Описание изменений на русском языке
- Ссылка на issue (если есть)
- Скриншоты для UI изменений
- Проверено локально в Docker

### Шаблон PR
```markdown
## Описание
Краткое описание того, что изменено.

## Тип изменений
- [ ] Bug fix (исправление, не ломающее существующую функциональность)
- [ ] New feature (новая функция, не ломающая существующую функциональность)  
- [ ] Breaking change (исправление или функция, которая ломает существующую функциональность)
- [ ] Documentation update (обновление документации)

## Тестирование
- [ ] Протестировано локально
- [ ] Протестировано в Docker
- [ ] Добавлены автотесты

## Связанные issues
Closes #123
```

## Docker разработка

### Запуск в Docker
```bash
make docker-up     # Запустить все сервисы
make docker-test   # Тесты в Docker
make docker-logs   # Логи ML worker
make docker-down   # Остановить сервисы
```

### Отладка
```bash
# Подключиться к контейнеру
docker compose exec api bash

# Проверить логи
docker compose logs api
docker compose logs ml-worker
```

## CI/CD

### GitHub Actions
Автоматически запускаются:
- **Tests** - при push в любую ветку
- **Code Quality** - при push и PR
- **Docker Tests** - при push в main/develop
- **Deploy** - при push в main

### Локальная проверка CI
```bash
make ci-test     # Тесты как в CI
make ci-quality  # Проверки качества как в CI
```

## Структура проекта

```
ml-ops-final/
├── .github/
│   └── workflows/          # GitHub Actions
├── src/
│   ├── base/              # Базовые компоненты
│   ├── products/          # Модуль продуктов
│   ├── users/             # Модуль пользователей
│   ├── pricing/           # ML модуль ценообразования
│   └── tests/             # Тесты
├── ml_worker/             # ML Worker
├── webui/                 # Streamlit UI
├── nginx/                 # Nginx конфигурация
├── models/                # ML модели (gitignore)
├── requirements.txt       # Зависимости production
├── requirements.dev.txt   # Зависимости разработки
├── docker-compose.yaml    # Docker конфигурация
└── Makefile              # Команды разработки
```

## Помощь и поддержка

- Создайте issue для вопросов
- Используйте Discussions для обсуждений
- Проверьте существующие PR перед созданием нового

## Благодарности

Спасибо за ваш вклад в проект! 🚀 