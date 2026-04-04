# =============================================================================
#  TimeTracker API — Production Dockerfile
#  Multi-stage build: builder → runtime
#  Non-root user, minimal image, built-in healthcheck
# =============================================================================

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Системные зависимости для сборки C-расширений (mysqlclient, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc \
      default-libmysqlclient-dev \
      pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Устанавливаем зависимости в изолированный prefix (быстрый кэш слоёв)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Только runtime-библиотеки MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
      default-mysql-client \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder-стадии
COPY --from=builder /install /usr/local

# Создаём непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Копируем исходный код
COPY --chown=appuser:appuser . .

# Переключаемся на непривилегированного пользователя
USER appuser

# Переменные окружения Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Healthcheck — проверяет /health каждые 30 секунд
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production: gunicorn + uvicorn workers
# Workers = 2*CPU+1, переопределяются через GUNICORN_WORKERS в .env
CMD ["sh", "-c", \
     "alembic upgrade head && \
      gunicorn app.main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers ${GUNICORN_WORKERS:-2} \
        --bind 0.0.0.0:8000 \
        --timeout ${GUNICORN_TIMEOUT:-120} \
        --keepalive 5 \
        --access-logfile - \
        --error-logfile - \
        --log-level ${LOG_LEVEL:-info}"]
