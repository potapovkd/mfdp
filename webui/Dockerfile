FROM python:3.12-slim

WORKDIR /app

# Копируем только необходимые файлы для WebUI
COPY webui/requirements.txt .
COPY webui/main.py .
COPY webui/dashboards ./dashboards

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["streamlit", "run", "main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
