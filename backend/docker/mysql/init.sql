-- docker/mysql/init.sql
-- Выполняется автоматически при первом запуске контейнера

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Убеждаемся, что БД создана с правильной кодировкой
-- (Docker уже создаёт её через MYSQL_DATABASE, но на всякий случай)

CREATE DATABASE IF NOT EXISTS timetracker_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Права уже выданы через MYSQL_USER/MYSQL_PASSWORD,
-- но явно указываем для надёжности

GRANT ALL PRIVILEGES ON timetracker_db.* TO 'timetracker_user'@'%';
FLUSH PRIVILEGES;
