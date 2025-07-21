FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем только нужные файлы и директории
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY worker.py .
COPY logs/ logs/
COPY docker-compose.workers.yaml .
COPY __pycache__/ __pycache__/

# Создание директории для моделей
RUN mkdir -p /app/models

# Запуск воркера
CMD ["python", "worker.py"] 