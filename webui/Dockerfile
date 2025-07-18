FROM python:3.12-slim

WORKDIR /webui

COPY . .

RUN pip install --upgrade pip && pip install -r /webui/requirements.txt

EXPOSE 8501

CMD streamlit run main.py --server.address="0.0.0.0" --server.port="8001" --server.enableCORS=false --server.enableXsrfProtection=false
