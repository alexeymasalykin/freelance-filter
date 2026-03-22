FROM python:3.11-slim AS base

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py filter.py main.py ./

RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-u", "main.py"]
