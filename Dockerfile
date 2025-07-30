FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только необходимые файлы для API
COPY requirements.txt requirements.dev.txt ./
COPY src/base ./src/base
COPY src/pricing ./src/pricing
COPY src/products ./src/products
COPY src/users ./src/users
COPY src/main.py ./src/main.py
COPY src/tests ./src/tests

# Устанавливаем зависимости, включая dev зависимости для тестирования
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements.dev.txt

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]