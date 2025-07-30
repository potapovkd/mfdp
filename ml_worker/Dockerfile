FROM python:3.11-slim

WORKDIR /app/ml_worker

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY ml_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY ml_worker/ .

# Создание директории для моделей
RUN mkdir -p /app/models

# Запуск воркера
CMD ["python", "worker.py"] 