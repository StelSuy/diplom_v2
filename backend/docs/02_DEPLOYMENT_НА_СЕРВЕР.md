# 🚀 DEPLOYMENT НА ЗОВНІШНІЙ СЕРВЕР

**Дата оновлення:** 30 січня 2026  
**Версія:** 2.0

---

## 📋 ЗМІСТ

1. [Вимоги до сервера](#-вимоги-до-сервера)
2. [Підготовка сервера](#-підготовка-сервера)
3. [Варіант А: Без Docker](#-варіант-а-без-docker-простіше)
4. [Варіант Б: З Docker](#-варіант-б-з-docker-рекомендовано)
5. [Налаштування безпеки](#-налаштування-безпеки)
6. [Автозапуск сервісу](#-автозапуск-сервісу)
7. [Backup та моніторинг](#-backup-та-моніторинг)
8. [Перевірка після деплою](#-перевірка-після-деплою)

---

## 💻 Вимоги до сервера

### Мінімальні характеристики:

- **ОС:** Ubuntu 22.04 LTS або новіше (рекомендовано)
- **CPU:** 2 ядра
- **RAM:** 2 GB (мінімум), 4 GB (рекомендовано)
- **Диск:** 20 GB SSD
- **Мережа:** Статична IP адреса або домен

### Опціонально:

- 🌐 **Домен** - для HTTPS (наприклад: api.timetracker.com)
- 🔒 **SSL сертифікат** - Let's Encrypt (безкоштовно)
- 🔥 **Firewall** - UFW або iptables
- 📊 **Моніторинг** - Grafana, Prometheus

---

## 🔧 Підготовка сервера

### 1. Оновлення системи

```bash
# Увійдіть на сервер через SSH
ssh user@your-server-ip

# Оновіть систему
sudo apt update && sudo apt upgrade -y

# Встановіть базові утиліти
sudo apt install -y curl wget git vim nano htop net-tools
```

### 2. Створення користувача для застосунку

```bash
# Створити окремого користувача (рекомендовано для безпеки)
sudo adduser timetracker

# Додати до sudo групи (якщо потрібно)
sudo usermod -aG sudo timetracker

# Перейти на нового користувача
sudo su - timetracker
```

### 3. Налаштування firewall

```bash
# Встановити UFW
sudo apt install ufw -y

# Дозволити SSH (ВАЖЛИВО: перед увімкненням!)
sudo ufw allow 22/tcp

# Дозволити HTTP та HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Увімкнути firewall
sudo ufw enable

# Перевірити статус
sudo ufw status
```

---

## 🐧 Варіант А: Без Docker (простіше)

### Крок 1: Встановлення Python 3.12

```bash
# Додати PPA для Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Встановити Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Перевірити версію
python3.12 --version
```

### Крок 2: Встановлення MySQL

```bash
# Встановити MySQL Server
sudo apt install mysql-server -y

# Запустити безпечну інсталяцію
sudo mysql_secure_installation

# Відповіді на питання:
# - Set root password? Y (введіть сильний пароль)
# - Remove anonymous users? Y
# - Disallow root login remotely? Y
# - Remove test database? Y
# - Reload privilege tables? Y
```

### Крок 3: Створення бази даних

```bash
# Увійти в MySQL
sudo mysql -u root -p

# Виконати SQL команди:
```

```sql
-- Створити базу даних
CREATE DATABASE timetracker_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Створити користувача
CREATE USER 'timetracker'@'localhost' IDENTIFIED BY 'ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_123!@#';

-- Надати права
GRANT ALL PRIVILEGES ON timetracker_prod.* TO 'timetracker'@'localhost';

-- Застосувати зміни
FLUSH PRIVILEGES;

-- Вийти
EXIT;
```

### Крок 4: Клонування проекту

```bash
# Перейти в домашню директорію
cd ~

# Клонувати репозиторій (замініть на ваш)
git clone https://github.com/your-username/timetracker-backend.git timetracker

# Перейти в директорію
cd timetracker

# Або завантажити архів
# wget https://github.com/your-username/timetracker-backend/archive/main.zip
# unzip main.zip
# cd timetracker-backend-main
```

### Крок 5: Налаштування Python оточення

```bash
# Створити віртуальне оточення
python3.12 -m venv venv

# Активувати
source venv/bin/activate

# Оновити pip
pip install --upgrade pip

# Встановити залежності
pip install -r requirements.txt
```

### Крок 6: Налаштування .env файлу

```bash
# Скопіювати приклад
cp .env.example .env

# Відредагувати
nano .env
```

**Критичні параметри для production:**

```ini
# Застосунок
APP_NAME=TimeTracker API
ENV=production
DEBUG=false

# База даних
DATABASE_URL=mysql+pymysql://timetracker:ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_123!@#@localhost:3306/timetracker_prod

# Безпека (ОБОВ'ЯЗКОВО ЗМІНІТЬ!)
JWT_SECRET=ЗГЕНЕРУЙТЕ_ДОВГИЙ_СЕКРЕТ_КЛЮЧ_МІНІМУМ_64_СИМВОЛИ
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Адмін (ОБОВ'ЯЗКОВО ЗМІНІТЬ!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_АДМІНА_456!@#

# CORS (вкажіть ваш домен!)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Логування
LOG_LEVEL=WARNING
SQL_ECHO=false
```

**Генерація JWT_SECRET:**

```bash
# Через OpenSSL (рекомендовано)
openssl rand -hex 64

# Через Python
python3 -c "import secrets; print(secrets.token_hex(64))"
```

### Крок 7: Застосування міграцій

```bash
# Активувати venv (якщо не активоване)
source venv/bin/activate

# Застосувати міграції
alembic upgrade head

# Перевірити
alembic current
```

### Крок 8: Тестовий запуск

```bash
# Запустити сервер для тесту
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Відкрити в іншому терміналі та перевірити
curl http://localhost:8000/health

# Зупинити (Ctrl+C)
```

---

## 🐳 Варіант Б: З Docker (рекомендовано)

### Крок 1: Встановлення Docker

```bash
# Встановити Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Додати користувача до групи docker
sudo usermod -aG docker $USER

# Перелогінитись (або logout/login)
newgrp docker

# Перевірити
docker --version
```

### Крок 2: Встановлення Docker Compose

```bash
# Встановити Docker Compose
sudo apt install docker-compose-plugin -y

# Перевірити
docker compose version
```

### Крок 3: Клонування проекту

```bash
# Перейти в домашню директорію
cd ~

# Клонувати
git clone https://github.com/your-username/timetracker-backend.git timetracker

cd timetracker
```

### Крок 4: Налаштування production конфігурації

```bash
# Скопіювати приклад
cp .env.production.example .env.production

# Відредагувати
nano .env.production
```

**Приклад .env.production:**

```ini
# Застосунок
APP_NAME=TimeTracker API
ENV=production
DEBUG=false

# База даних
DB_NAME=timetracker_prod
DB_USER=timetracker
DB_PASSWORD=ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_БД_789!@#
DB_ROOT_PASSWORD=ДУЖЕ_СИЛЬНИЙ_ROOT_ПАРОЛЬ_000!@#

# Внутрішній URL для Docker контейнера
DATABASE_URL=mysql+pymysql://timetracker:ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_БД_789!@#@db:3306/timetracker_prod

# Безпека
JWT_SECRET=ЗГЕНЕРУЙТЕ_ДОВГИЙ_СЕКРЕТ_КЛЮЧ_МІНІМУМ_64_СИМВОЛИ
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Адмін
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_АДМІНА_456!@#

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Логування
LOG_LEVEL=WARNING
SQL_ECHO=false

# Терміналів
TERMINAL_SCAN_COOLDOWN_SECONDS=5
```

### Крок 5: Запуск Docker Compose

```bash
# Запустити в production режимі
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Перевірити статус
docker compose -f docker-compose.prod.yml ps

# Переглянути логи
docker compose -f docker-compose.prod.yml logs -f
```

### Крок 6: Застосування міграцій (Docker)

```bash
# Застосувати міграції в контейнері
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# Перевірити
docker compose -f docker-compose.prod.yml exec api alembic current
```

---

## 🌐 Налаштування Nginx (Reverse Proxy)

### Варіант 1: Без Docker (якщо API запущено без Docker)

```bash
# Встановити Nginx
sudo apt install nginx -y

# Створити конфігурацію
sudo nano /etc/nginx/sites-available/timetracker
```

**Конфігурація Nginx:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Логи
    access_log /var/log/nginx/timetracker-access.log;
    error_log /var/log/nginx/timetracker-error.log;

    # Проксі до API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймаути
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check (без логування)
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
# Активувати конфігурацію
sudo ln -s /etc/nginx/sites-available/timetracker /etc/nginx/sites-enabled/

# Перевірити конфігурацію
sudo nginx -t

# Перезапустити Nginx
sudo systemctl restart nginx

# Додати в автозапуск
sudo systemctl enable nginx
```

### Варіант 2: З Docker (якщо використовуєте docker-compose.prod.yml)

Docker Compose вже включає Nginx контейнер, тому додаткове налаштування не потрібне.

---

## 🔒 Налаштування HTTPS (Let's Encrypt)

### 1. Встановлення Certbot

```bash
# Встановити Certbot
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Отримання SSL сертифіката

```bash
# Автоматичне налаштування для Nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Відповісти на питання:
# Email: your@email.com
# Terms: A (Agree)
# Share email: N (No)
# Redirect HTTP to HTTPS: 2 (Yes)
```

### 3. Автоматичне оновлення сертифіката

```bash
# Certbot автоматично додає cron job, перевірити:
sudo certbot renew --dry-run

# Якщо потрібно додати вручну:
sudo crontab -e

# Додати рядок:
0 3 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 🔐 Налаштування безпеки

### 1. Налаштування firewall (UFW)

```bash
# Дозволити тільки необхідні порти
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Відхилити все інше
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Увімкнути
sudo ufw enable

# Статус
sudo ufw status verbose
```

### 2. Обмеження SSH доступу

```bash
# Редагувати конфігурацію SSH
sudo nano /etc/ssh/sshd_config

# Рекомендовані зміни:
# PermitRootLogin no              # Заборонити root login
# PasswordAuthentication no       # Тільки SSH ключі (після налаштування)
# Port 2222                       # Змінити порт (опціонально)

# Перезапустити SSH
sudo systemctl restart sshd
```

### 3. Fail2Ban (захист від brute-force)

```bash
# Встановити Fail2Ban
sudo apt install fail2ban -y

# Створити конфігурацію
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# Увімкнути SSH захист:
# [sshd]
# enabled = true
# port = 22
# maxretry = 3
# bantime = 3600

# Запустити
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Статус
sudo fail2ban-client status sshd
```

### 4. Оновлення системи

```bash
# Налаштувати автоматичні оновлення безпеки
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🔄 Автозапуск сервісу

### Варіант А: Systemd сервіс (без Docker)

```bash
# Створити systemd unit файл
sudo nano /etc/systemd/system/timetracker.service
```

**Вміст файлу:**

```ini
[Unit]
Description=TimeTracker API
After=network.target mysql.service

[Service]
Type=simple
User=timetracker
Group=timetracker
WorkingDirectory=/home/timetracker/timetracker
Environment="PATH=/home/timetracker/timetracker/venv/bin"

ExecStart=/home/timetracker/timetracker/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

Restart=always
RestartSec=10

# Логування
StandardOutput=journal
StandardError=journal
SyslogIdentifier=timetracker

[Install]
WantedBy=multi-user.target
```

```bash
# Перезавантажити systemd
sudo systemctl daemon-reload

# Запустити сервіс
sudo systemctl start timetracker

# Додати в автозапуск
sudo systemctl enable timetracker

# Перевірити статус
sudo systemctl status timetracker

# Переглянути логи
sudo journalctl -u timetracker -f
```

### Варіант Б: Docker автозапуск (з Docker)

```bash
# Docker Compose автоматично налаштовує restart policy
# Перевірити:
docker compose -f docker-compose.prod.yml ps

# Якщо потрібно змінити restart policy:
# В docker-compose.prod.yml додати/змінити:
# restart: always

# Додати Docker в автозапуск (якщо ще не додано)
sudo systemctl enable docker
```

---

## 💾 Backup та моніторинг

### 1. Автоматичний backup бази даних

```bash
# Створити директорію для backup
mkdir -p ~/backups

# Створити скрипт backup
nano ~/backup_db.sh
```

**Вміст скрипту:**

```bash
#!/bin/bash

# Параметри
DB_NAME="timetracker_prod"
DB_USER="timetracker"
DB_PASS="ДУЖЕ_СИЛЬНИЙ_ПАРОЛЬ_БД_789!@#"
BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Створити backup
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_FILE

# Стиснути
gzip $BACKUP_FILE

# Видалити старі backup (старіше 7 днів)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE.gz"
```

```bash
# Зробити виконуваним
chmod +x ~/backup_db.sh

# Додати в cron (щоденно о 2:00)
crontab -e

# Додати рядок:
0 2 * * * /home/timetracker/backup_db.sh >> /home/timetracker/backup.log 2>&1
```

### 2. Моніторинг логів

```bash
# Системний лог (без Docker)
sudo journalctl -u timetracker -f

# Docker логи
docker compose -f docker-compose.prod.yml logs -f api

# Nginx логи
sudo tail -f /var/log/nginx/timetracker-access.log
sudo tail -f /var/log/nginx/timetracker-error.log

# MySQL логи
sudo tail -f /var/log/mysql/error.log
```

### 3. Моніторинг ресурсів

```bash
# CPU та пам'ять
htop

# Диск
df -h

# Мережа
sudo netstat -tuln | grep LISTEN

# Процеси
ps aux | grep uvicorn
# або
ps aux | grep python
```

---

## ✅ Перевірка після деплою

### 1. Health Check

```bash
# Локально на сервері
curl http://localhost:8000/health
curl https://yourdomain.com/health

# З іншого комп'ютера
curl https://yourdomain.com/health
```

**Очікувана відповідь:**

```json
{
  "status": "ok",
  "app": "TimeTracker API",
  "env": "production",
  "version": "1.0.0"
}
```

### 2. Тест API документації

```bash
# Перевірити чи доступна документація (має бути вимкнена в production)
curl https://yourdomain.com/docs
# Очікується: 404 або редірект

# Якщо хочете залишити docs в production:
# В .env встановіть: DEBUG=true
```

### 3. Тест логіну

```bash
# Тест через curl
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ВАШІ_АДМІН_ПАРОЛЬ"}'
```

**Очікувана відповідь:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Перевірка SSL

```bash
# Перевірити сертифікат
curl -vI https://yourdomain.com

# Тест SSL через онлайн сервіс:
# https://www.ssllabs.com/ssltest/
```

### 5. Навантажувальне тестування (опціонально)

```bash
# Встановити Apache Bench
sudo apt install apache2-utils -y

# Тест 1000 запитів, 10 одночасно
ab -n 1000 -c 10 https://yourdomain.com/health
```

---

## 🔧 Управління сервісом

### Без Docker:

```bash
# Запустити
sudo systemctl start timetracker

# Зупинити
sudo systemctl stop timetracker

# Перезапустити
sudo systemctl restart timetracker

# Статус
sudo systemctl status timetracker

# Логи
sudo journalctl -u timetracker -f
```

### З Docker:

```bash
# Запустити
docker compose -f docker-compose.prod.yml up -d

# Зупинити
docker compose -f docker-compose.prod.yml down

# Перезапустити
docker compose -f docker-compose.prod.yml restart

# Статус
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f
```

---

## 🆙 Оновлення застосунку

### Без Docker:

```bash
# 1. Зупинити сервіс
sudo systemctl stop timetracker

# 2. Backup БД
~/backup_db.sh

# 3. Отримати нові зміни
cd ~/timetracker
git pull

# 4. Оновити залежності (якщо змінились)
source venv/bin/activate
pip install -r requirements.txt

# 5. Застосувати нові міграції
alembic upgrade head

# 6. Запустити сервіс
sudo systemctl start timetracker

# 7. Перевірити
curl http://localhost:8000/health
```

### З Docker:

```bash
# 1. Backup БД
~/backup_db.sh

# 2. Отримати нові зміни
cd ~/timetracker
git pull

# 3. Пересобрати та перезапустити
docker compose -f docker-compose.prod.yml up -d --build

# 4. Застосувати міграції
docker compose -f docker-compose.prod.yml exec api alembic upgrade head

# 5. Перевірити
curl https://yourdomain.com/health
```

---

## 📋 Чеклист готовності до production

- [ ] ✅ Сервер оновлено та налаштовано
- [ ] ✅ Встановлено Python 3.12 або Docker
- [ ] ✅ Встановлено та налаштовано MySQL
- [ ] ✅ Створено базу даних та користувача
- [ ] ✅ Згенеровано сильний JWT_SECRET (64+ символи)
- [ ] ✅ Змінено ADMIN_PASSWORD на сильний
- [ ] ✅ Налаштовано .env або .env.production файл
- [ ] ✅ Застосовано всі міграції БД
- [ ] ✅ Налаштовано Nginx reverse proxy
- [ ] ✅ Отримано SSL сертифікат (Let's Encrypt)
- [ ] ✅ Налаштовано firewall (UFW)
- [ ] ✅ Налаштовано автозапуск сервісу
- [ ] ✅ Налаштовано автоматичні backup
- [ ] ✅ Перевірено health endpoint
- [ ] ✅ Протестовано login
- [ ] ✅ Перевірено SSL
- [ ] ✅ ENV=production, DEBUG=false
- [ ] ✅ CORS налаштовано на конкретні домени
- [ ] ✅ Всі паролі сильні та унікальні

---

## 🆘 Розв'язання проблем

### Проблема: Не можу підключитися до сервера

```bash
# Перевірити чи запущено сервіс
sudo systemctl status timetracker
# або
docker compose -f docker-compose.prod.yml ps

# Перевірити чи слухає порт
sudo netstat -tuln | grep 8000

# Перевірити firewall
sudo ufw status

# Переглянути логи
sudo journalctl -u timetracker -n 100
```

### Проблема: 502 Bad Gateway в Nginx

```bash
# Перевірити чи працює API
curl http://localhost:8000/health

# Переглянути логи Nginx
sudo tail -f /var/log/nginx/timetracker-error.log

# Перевірити конфігурацію Nginx
sudo nginx -t

# Перезапустити Nginx
sudo systemctl restart nginx
```

### Проблема: Помилки з базою даних

```bash
# Перевірити чи працює MySQL
sudo systemctl status mysql

# Підключитися до БД
mysql -u timetracker -p

# Перевірити логи MySQL
sudo tail -f /var/log/mysql/error.log

# Перезапустити MySQL
sudo systemctl restart mysql
```

---

**Успіхів з deployment! 🎉**

Створено: 30 січня 2026  
Версія документації: 2.0
