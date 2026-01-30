# 🚀 Быстрый старт деплоя на VPS

## За 5 минут до production

### 1️⃣ Подготовка VPS (1 минута)

```bash
# Обновление и установка Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Установка Git
sudo apt install git -y
```

### 2️⃣ Клонирование и настройка (2 минуты)

```bash
# Клонирование
git clone <your-repo-url> timetracker
cd timetracker

# Настройка окружения
cp .env.production .env
nano .env

# ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ:
# - DB_ROOT_PASSWORD
# - DB_PASSWORD  
# - JWT_SECRET (сгенерируйте: openssl rand -hex 32)
# - ADMIN_PASSWORD
```

### 3️⃣ Запуск (2 минуты)

```bash
# Дать права на выполнение
chmod +x deploy.sh update.sh backup_db.sh

# Запуск
./deploy.sh
```

### 4️⃣ Проверка

```bash
# Проверка работы
curl http://localhost/health

# Должен вернуть: {"status":"ok",...}
```

---

## 📱 Настройка терминала

**API_BASE_URL:**
```
http://YOUR_VPS_IP
```

Или с доменом:
```
https://yourdomain.com
```

---

## 🔐 Настройка SSL (опционально, 3 минуты)

```bash
# Остановка nginx
docker compose -f docker-compose.prod.yml stop nginx

# Получение сертификата
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com

# Обновление nginx.conf (раскомментировать строки Let's Encrypt)
nano nginx.conf

# Перезапуск
docker compose -f docker-compose.prod.yml start nginx
```

---

## 🔄 Обновление приложения

```bash
./update.sh
```

---

## 💾 Резервное копирование

```bash
# Ручной бэкап
./backup_db.sh

# Автоматический бэкап (каждый день в 2:00)
chmod +x backup_db.sh
crontab -e
# Добавить: 0 2 * * * /home/$USER/timetracker/backup_db.sh
```

---

## 📊 Полезные команды

```bash
# Логи
docker compose -f docker-compose.prod.yml logs -f

# Статус
docker compose -f docker-compose.prod.yml ps

# Перезапуск API
docker compose -f docker-compose.prod.yml restart api

# Остановка всего
docker compose -f docker-compose.prod.yml down
```

---

## 🆘 Проблемы?

**API не запускается:**
```bash
docker compose -f docker-compose.prod.yml logs api
```

**БД не подключается:**
```bash
docker compose -f docker-compose.prod.yml logs db
docker exec -it timetracker_api nc -zv db 3306
```

**Порты заняты:**
```bash
sudo netstat -tulpn | grep :80
sudo systemctl stop apache2  # если установлен
```

---

📖 **Полная документация:** `README_DEPLOY_VPS.md`
