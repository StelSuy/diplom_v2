#!/bin/bash

# TimeTracker Backend - Production Deployment Script
# Быстрый деплой на VPS

set -e  # Остановка при ошибке

echo "=========================================="
echo "TimeTracker Backend Deployment"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка .env файла
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file from .env.production template"
    exit 1
fi

# Проверка критических переменных
check_env_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env | cut -d '=' -f2)
    
    if [ -z "$var_value" ] || [ "$var_value" == "CHANGE_ME"* ]; then
        echo -e "${RED}Error: ${var_name} is not set or has default value${NC}"
        return 1
    fi
    return 0
}

echo "Checking environment variables..."
MISSING_VARS=0

for var in DB_ROOT_PASSWORD DB_PASSWORD JWT_SECRET ADMIN_PASSWORD; do
    if ! check_env_var $var; then
        MISSING_VARS=1
    fi
done

if [ $MISSING_VARS -eq 1 ]; then
    echo -e "${RED}Please configure all required variables in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables OK${NC}"

# Останавливаем контейнеры если запущены
echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# Создание SSL директории если нет
if [ ! -d "ssl" ]; then
    echo "Creating SSL directory with self-signed certificate..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/self-signed.key \
        -out ssl/self-signed.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" 2>/dev/null
    echo -e "${GREEN}✓ Self-signed certificate created${NC}"
fi

# Сборка и запуск
echo "Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Ожидание запуска БД
echo "Waiting for database to be ready..."
sleep 10

# Проверка здоровья БД
echo "Checking database health..."
until docker exec timetracker_db mysqladmin ping -h"localhost" --silent; do
    echo "Waiting for database..."
    sleep 2
done
echo -e "${GREEN}✓ Database is ready${NC}"

# Применение миграций
echo "Running database migrations..."
docker exec timetracker_api alembic upgrade head
echo -e "${GREEN}✓ Migrations applied${NC}"

# Проверка API
echo "Checking API health..."
sleep 5

HEALTH_CHECK=$(curl -s http://localhost/health | grep -o '"status":"ok"' || echo "")
if [ -n "$HEALTH_CHECK" ]; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${YELLOW}Warning: API health check failed${NC}"
    echo "Check logs: docker compose -f docker-compose.prod.yml logs api"
fi

# Вывод информации
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment completed!${NC}"
echo "=========================================="
echo ""
echo "Services status:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Access points:"
echo "  • API: http://localhost/api"
echo "  • Docs: http://localhost/docs"
echo "  • Health: http://localhost/health"
echo "  • Admin: http://localhost/admin"
echo ""
echo "Useful commands:"
echo "  • View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "  • Restart API: docker compose -f docker-compose.prod.yml restart api"
echo "  • Stop all: docker compose -f docker-compose.prod.yml down"
echo ""
echo -e "${YELLOW}Note: Configure SSL certificate for HTTPS in production!${NC}"
echo "See README_DEPLOY_VPS.md for SSL setup instructions"
