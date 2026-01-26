#!/bin/bash

# TimeTracker Backend - Database Backup Script
# Создание резервной копии БД

set -e

BACKUP_DIR="${HOME}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "TimeTracker Database Backup"
echo "=========================================="

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Получение пароля root из .env
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Проверка что контейнер БД запущен
if ! docker ps | grep -q timetracker_db; then
    echo "Error: Database container is not running"
    exit 1
fi

# Создание бэкапа
echo "Creating backup..."
docker exec timetracker_db sh -c \
    'mysqldump -u root -p$MYSQL_ROOT_PASSWORD --all-databases --routines --triggers --events' \
    > $BACKUP_DIR/backup_$TIMESTAMP.sql

# Проверка размера бэкапа
BACKUP_SIZE=$(du -h $BACKUP_DIR/backup_$TIMESTAMP.sql | cut -f1)
echo -e "${GREEN}✓ Backup created: $BACKUP_DIR/backup_$TIMESTAMP.sql ($BACKUP_SIZE)${NC}"

# Сжатие бэкапа
echo "Compressing backup..."
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql
COMPRESSED_SIZE=$(du -h $BACKUP_DIR/backup_$TIMESTAMP.sql.gz | cut -f1)
echo -e "${GREEN}✓ Backup compressed: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz ($COMPRESSED_SIZE)${NC}"

# Удаление старых бэкапов
echo "Removing old backups (older than $RETENTION_DAYS days)..."
DELETED=$(find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ $DELETED -gt 0 ]; then
    echo -e "${GREEN}✓ Removed $DELETED old backup(s)${NC}"
else
    echo "No old backups to remove"
fi

# Список текущих бэкапов
echo ""
echo "Current backups:"
ls -lh $BACKUP_DIR/backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
echo ""
echo "To restore from this backup:"
echo "  1. Stop API: docker compose -f docker-compose.prod.yml stop api"
echo "  2. Restore: gunzip < $BACKUP_DIR/backup_$TIMESTAMP.sql.gz | docker exec -i timetracker_db mysql -u root -p\$MYSQL_ROOT_PASSWORD"
echo "  3. Start API: docker compose -f docker-compose.prod.yml start api"
