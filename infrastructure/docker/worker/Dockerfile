FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt celery redis

COPY . .

CMD ["python", "-m", "celery", "-A", "app.celery", "worker", "--loglevel=info"]
