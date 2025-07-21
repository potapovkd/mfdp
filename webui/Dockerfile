FROM python:3.12-slim

WORKDIR /webui

# Копируем только нужные файлы и директории
COPY requirements.txt .
COPY main.py .
COPY dashboards/ dashboards/
COPY __init__.py .

# Позволяет прокидывать переменные окружения для подключения к БД
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_NAME=pricing_optimization
ENV DB_USER=pricing_user
ENV DB_PASSWORD=pricing_password

RUN pip install --upgrade pip && pip install -r /webui/requirements.txt

EXPOSE 8501

CMD streamlit run main.py --server.address="0.0.0.0" --server.port="8001" --server.enableCORS=false --server.enableXsrfProtection=false
