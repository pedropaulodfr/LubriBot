# Imagem de producao do LubriBot.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN rm -rf .git .venv Backups .agent-panel agent-panel.html dist \
    && useradd --system --uid 10001 --home /app lubribot \
    && chown -R lubribot:lubribot /app

USER lubribot
EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:10000/ping || exit 1

CMD ["python", "main.py"]
