#!/bin/bash

# TimeTracker Backend - Production Update Script
# Быстрое обновление без даунтайма

set -e

echo "=========================================="
echo "TimeTracker Backend Update"
echo "=========================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверка git репозитория
if [ ! -d .git ]; then
    echo "Error: Not a git repository"
    exit 1
fi

# Сохранение локальных изменений
echo "Stashing local changes..."
git stash

# Получение обновлений
echo "Pulling updates..."
git pull origin main || git pull origin master

# Восстановление локальных изменений
echo "Restoring local changes..."
git stash pop || true

# Сборка нового образа
echo "Building new image..."
docker compose -f docker-compose.prod.yml build api

# Обновление контейнера без остановки БД и nginx
echo "Updating API container..."
docker compose -f docker-compose.prod.yml up -d --no-deps api

# Применение миграций
echo "Running migrations..."
sleep 5
docker exec timetracker_api alembic upgrade head

# Проверка здоровья
echo "Checking API health..."
sleep 3
HEALTH_CHECK=$(curl -s http://localhost/health | grep -o '"status":"ok"' || echo "")

if [ -n "$HEALTH_CHECK" ]; then
    echo -e "${GREEN}✓ Update completed successfully!${NC}"
else
    echo -e "${YELLOW}Warning: API health check failed${NC}"
    echo "Check logs: docker compose -f docker-compose.prod.yml logs api"
fi

echo ""
echo "View recent logs:"
docker compose -f docker-compose.prod.yml logs --tail=50 api
