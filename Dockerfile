FROM python:3.13
LABEL authors="oldev-prog"
LABEL version="1.0"
LABEL description="Telegram bot LanguageAssistant with FastAPI and Celery"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
