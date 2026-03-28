FROM python:3.11-slim AS base

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py evaluator.py filter.py bot.py main.py ./

RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/freelance_filter.session') else 1)"

CMD ["python", "-u", "main.py"]
