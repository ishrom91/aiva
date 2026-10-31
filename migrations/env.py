from logging.config import fileConfig
import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import make_url

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.models import Base  # pylint: disable=wrong-import-position

target_metadata = Base.metadata


def get_url() -> str:
    """Convert async application URLs to synchronous Alembic driver URLs."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return url

    parsed = make_url(url)
    query = dict(parsed.query)
    if parsed.drivername == "sqlite+aiosqlite":
        parsed = parsed.set(drivername="sqlite")
    elif parsed.drivername == "postgresql+asyncpg":
        parsed = parsed.set(drivername="postgresql+psycopg2")
        if "ssl" in query:
            query["sslmode"] = query.pop("ssl")
    return parsed.set(query=query).render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url() or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url() or config.get_main_option("sqlalchemy.url")
    if url:
        config.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
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
