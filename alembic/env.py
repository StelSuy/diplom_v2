from logging.config import fileConfig

from sqlalchemy import engine_from_config, text
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.db.base import Base

# Імпортуємо всі моделі
from app.models.employee import Employee      # noqa
from app.models.event import Event            # noqa
from app.models.schedule import Schedule      # noqa
from app.models.terminal import Terminal      # noqa
from app.models.user import User              # noqa
from app.models.audit_log import AuditLog     # noqa
from app.models.position import Position      # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _ensure_database_exists() -> None:
    """
    Створює БД якщо її немає — щоб alembic не падав з 'Unknown database'.
    Підключається до MySQL без вказання бази (через /  в URL).
    """
    import re
    import pymysql

    url = settings.database_url
    # Витягуємо параметри з DATABASE_URL
    m = re.match(
        r"mysql\+pymysql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>[^?]+)",
        url,
    )
    if not m:
        return

    host     = m.group("host")
    port     = int(m.group("port") or 3306)
    user     = m.group("user")
    password = m.group("password")
    db_name  = m.group("db").split("?")[0]

    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=5)
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conn.commit()
        conn.close()
        print(f"[alembic/env] ✔ Database '{db_name}' ready.")
    except Exception as e:
        print(f"[alembic/env] ⚠ Could not auto-create DB: {e}")


# ── Гарантуємо існування БД перед підключенням ────────────────────────────────
_ensure_database_exists()

config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
