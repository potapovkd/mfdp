FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY ml_worker/requirements.txt ./ml_worker/
RUN pip install --no-cache-dir -r ml_worker/requirements.txt

# Копирование DVC конфигурации и git репозитория в корень проекта
COPY .git ./.git
COPY .dvc ./.dvc
COPY models.dvc ./

# Копирование кода ML worker
COPY ml_worker/ ./ml_worker/

# Создание директории для моделей
RUN mkdir -p /app/models

# Запуск воркера
WORKDIR /app/ml_worker
CMD ["python", "worker.py"] 