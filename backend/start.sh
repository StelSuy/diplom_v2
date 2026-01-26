#!/bin/bash
# start.sh - Production startup script

# Встановлення дефолтів для PORT якщо не задано
export PORT=${PORT:-8000}

# Виведення інформації про запуск
echo "============================================"
echo "Starting TimeTracker API"
echo "Environment: ${APP_ENV:-production}"
echo "Port: $PORT"
echo "============================================"

# Запуск з Gunicorn (рекомендовано)
if command -v gunicorn &> /dev/null; then
    echo "Starting with Gunicorn..."
    exec gunicorn -c gunicorn.conf.py app.main:app
else
    # Fallback на Uvicorn
    echo "Gunicorn not found, starting with Uvicorn..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
fi
