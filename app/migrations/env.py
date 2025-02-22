from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from app.config import settings

# Import the database configuration and the Base from your models
from app.database import Base

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
# This will allow Alembic to detect changes in your database models

target_metadata = Base.metadata

# Other values from the config can be acquired here if needed
# For example, you can retrieve options like the database URL
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
# Read the database URL from the environment variable
config.set_section_option("alembic", "sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    In this mode, we don't need a DBAPI or engine, only the URL.
    The migration will be generated as a string and printed to the console.
    """
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
    """Run migrations in 'online' mode.

    In this mode, we need to create an Engine and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Get the database URL from the settings (from .env file)
    connectable.url = settings.DATABASE_URL

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Choose whether to run the migrations offline or online based on the mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
