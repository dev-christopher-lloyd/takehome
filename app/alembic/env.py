import os
import sys
from pathlib import Path
import logging
from sqlalchemy import engine_from_config, pool
from alembic import context
import sqlalchemy as sa

# needed to find Base
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
  sys.path.insert(0, str(BASE_DIR))

from core.db import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
  logging.basicConfig(level=logging.INFO)

target_metadata = Base.metadata


def get_url():
  # Docker compose sets DATABASE_URL
  return os.getenv("DATABASE_URL")


def run_migrations_offline():
  url = get_url()
  context.configure(
      url=url,
      target_metadata=target_metadata,
      literal_binds=True,
      version_table_column_type=sa.String(64),
  )

  with context.begin_transaction():
    context.run_migrations()


def run_migrations_online():
  configuration = config.get_section(config.config_ini_section)
  configuration["sqlalchemy.url"] = get_url()  # type: ignore

  connectable = engine_from_config(
      configuration,  # type: ignore
      prefix="sqlalchemy.",
      poolclass=pool.NullPool,
  )

  with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_column_type=sa.String(64),
    )

    with context.begin_transaction():
      context.run_migrations()


if context.is_offline_mode():
  run_migrations_offline()
else:
  run_migrations_online()
