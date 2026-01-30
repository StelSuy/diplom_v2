# Команды для быстрого копирования в терминал VPS

## ═══════════════════════════════════════════════════════════
## УСТАНОВКА DOCKER НА VPS (Ubuntu 22.04/24.04)
## ═══════════════════════════════════════════════════════════

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker (один скрипт)
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Применение без перелогина
newgrp docker

# Проверка установки
docker --version
docker compose version

# Установка Git
sudo apt install git -y

## ═══════════════════════════════════════════════════════════
## КЛОНИРОВАНИЕ И НАСТРОЙКА ПРОЕКТА
## ═══════════════════════════════════════════════════════════

# Переход в домашнюю директорию
cd ~

# Клонирование репозитория (ЗАМЕНИТЕ URL!)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git timetracker
cd timetracker

# Копирование шаблона env
cp .env.production .env

## ═══════════════════════════════════════════════════════════
## ГЕНЕРАЦИЯ СЕКРЕТОВ
## ═══════════════════════════════════════════════════════════

# JWT секрет (64 символа hex)
echo "JWT_SECRET=$(openssl rand -hex 32)"

# DB Root пароль
echo "DB_ROOT_PASSWORD=$(openssl rand -base64 24)"

# DB User пароль
echo "DB_PASSWORD=$(openssl rand -base64 24)"

# Admin пароль
echo "ADMIN_PASSWORD=$(openssl rand -base64 16)"

## ═══════════════════════════════════════════════════════════
## РЕДАКТИРОВАНИЕ .env ФАЙЛА
## ═══════════════════════════════════════════════════════════

# Открыть редактор (nano или vim)
nano .env

# ИЛИ использовать sed для быстрой замены:
# sed -i 's/DB_ROOT_PASSWORD=.*/DB_ROOT_PASSWORD=YOUR_GENERATED_PASSWORD/' .env
# sed -i 's/DB_PASSWORD=.*/DB_PASSWORD=YOUR_GENERATED_PASSWORD/' .env
# sed -i 's/JWT_SECRET=.*/JWT_SECRET=YOUR_GENERATED_SECRET/' .env
# sed -i 's/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=YOUR_GENERATED_PASSWORD/' .env

## ═══════════════════════════════════════════════════════════
## ПРАВА НА ВЫПОЛНЕНИЕ СКРИПТОВ
## ═══════════════════════════════════════════════════════════

chmod +x deploy.sh update.sh backup_db.sh

## ═══════════════════════════════════════════════════════════
## ПЕРВЫЙ ЗАПУСК
## ═══════════════════════════════════════════════════════════

# Запуск деплоя
./deploy.sh

# ИЛИ вручную:
# docker compose -f docker-compose.prod.yml up -d --build
# sleep 15
# docker exec timetracker_api alembic upgrade head

## ═══════════════════════════════════════════════════════════
## ПРОВЕРКА РАБОТОСПОСОБНОСТИ
## ═══════════════════════════════════════════════════════════

# Проверка health endpoint
curl http://localhost/health

# Проверка статуса контейнеров
docker compose -f docker-compose.prod.yml ps

# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

## ═══════════════════════════════════════════════════════════
## НАСТРОЙКА SSL (Let's Encrypt) - ПОСЛЕ НАСТРОЙКИ DNS
## ═══════════════════════════════════════════════════════════

# Остановка nginx для получения сертификата
docker compose -f docker-compose.prod.yml stop nginx

# Установка certbot
sudo apt install certbot -y

# Получение сертификата (ЗАМЕНИТЕ ДОМЕН!)
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --agree-tos \
  --email your-email@example.com \
  --non-interactive

# Редактирование nginx.conf (раскомментировать Let's Encrypt строки)
nano nginx.conf

# Замените:
# server_name _;
# на:
# server_name yourdomain.com www.yourdomain.com;

# И раскомментируйте:
# ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Запуск nginx
docker compose -f docker-compose.prod.yml start nginx

# Проверка HTTPS
curl https://yourdomain.com/health

## ═══════════════════════════════════════════════════════════
## АВТООБНОВЛЕНИЕ SSL СЕРТИФИКАТА
## ═══════════════════════════════════════════════════════════

# Добавление в crontab
sudo crontab -e

# Добавьте строку:
# 0 3 * * * certbot renew --quiet --post-hook "docker exec timetracker_nginx nginx -s reload"

## ═══════════════════════════════════════════════════════════
## НАСТРОЙКА FIREWALL (UFW)
## ═══════════════════════════════════════════════════════════

# Установка UFW
sudo apt install ufw -y

# Разрешение SSH (ВАЖНО! Сделайте это первым)
sudo ufw allow 22/tcp

# Разрешение HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включение firewall
sudo ufw enable

# Проверка статуса
sudo ufw status

## ═══════════════════════════════════════════════════════════
## НАСТРОЙКА АВТОМАТИЧЕСКИХ БЭКАПОВ
## ═══════════════════════════════════════════════════════════

# Создание директории для бэкапов
mkdir -p ~/backups

# Тестовый запуск бэкапа
./backup_db.sh

# Добавление в crontab (каждый день в 2:00 AM)
crontab -e

# Добавьте строку:
# 0 2 * * * /home/$USER/timetracker/backup_db.sh >> /home/$USER/backups/backup.log 2>&1

## ═══════════════════════════════════════════════════════════
## ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ
## ═══════════════════════════════════════════════════════════

# Быстрое обновление (без даунтайма)
./update.sh

# ИЛИ вручную:
# git pull
# docker compose -f docker-compose.prod.yml up -d --build
# docker exec timetracker_api alembic upgrade head

## ═══════════════════════════════════════════════════════════
## ПОЛЕЗНЫЕ КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ
## ═══════════════════════════════════════════════════════════

# Просмотр логов всех сервисов
docker compose -f docker-compose.prod.yml logs -f

# Просмотр логов конкретного сервиса
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f db
docker compose -f docker-compose.prod.yml logs -f nginx

# Перезапуск конкретного сервиса
docker compose -f docker-compose.prod.yml restart api
docker compose -f docker-compose.prod.yml restart nginx

# Остановка всех сервисов
docker compose -f docker-compose.prod.yml down

# Запуск всех сервисов
docker compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker compose -f docker-compose.prod.yml ps

# Вход в контейнер API
docker exec -it timetracker_api sh

# Вход в MySQL
docker exec -it timetracker_db mysql -u root -p

# Применение миграций вручную
docker exec -it timetracker_api alembic upgrade head

# Откат миграции
docker exec -it timetracker_api alembic downgrade -1

# Просмотр текущей миграции
docker exec -it timetracker_api alembic current

# Проверка конфигурации nginx
docker exec timetracker_nginx nginx -t

# Перезагрузка nginx без перезапуска
docker exec timetracker_nginx nginx -s reload

## ═══════════════════════════════════════════════════════════
## МОНИТОРИНГ РЕСУРСОВ
## ═══════════════════════════════════════════════════════════

# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h

# Размер volumes
docker system df

# Очистка неиспользуемых образов
docker image prune -a

## ═══════════════════════════════════════════════════════════
## ВОССТАНОВЛЕНИЕ ИЗ БЭКАПА
## ═══════════════════════════════════════════════════════════

# Остановка API
docker compose -f docker-compose.prod.yml stop api

# Восстановление из сжатого бэкапа
gunzip < ~/backups/backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i timetracker_db mysql -u root -p

# ИЛИ из несжатого:
# docker exec -i timetracker_db mysql -u root -p < ~/backups/backup_XXXXXX.sql

# Запуск API
docker compose -f docker-compose.prod.yml start api

## ═══════════════════════════════════════════════════════════
## НАСТРОЙКА ТЕРМИНАЛА (Android)
## ═══════════════════════════════════════════════════════════

# API_BASE_URL для терминала:
# http://YOUR_VPS_IP (без SSL)
# или
# https://yourdomain.com (с SSL)

# Пример:
# https://api.timetracker.com
