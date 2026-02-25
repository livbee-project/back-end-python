"""
Alembic 환경 설정
데이터베이스 마이그레이션을 위한 환경 구성
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from alembic import context

# app 모듈 import를 위한 경로 설정
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# app 설정 및 모델 import
from app.core.config import settings
from app.core.database import Base, DATABASE_URL
import app.models  # noqa: F401 - 모든 모델을 import하여 Base.metadata에 등록

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """데이터베이스 URL 반환"""
    return DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
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

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Alembic 기본 version_num은 VARCHAR(32). 긴 리비전 ID 저장 시 StringDataRightTruncation 발생하므로,
        # PostgreSQL이고 테이블이 이미 있으면 컬럼을 VARCHAR(255)로 확장.
        if connection.dialect.name == "postgresql":
            try:
                r = connection.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema = current_schema() AND table_name = 'alembic_version'"
                    )
                )
                if r.scalar() is not None:
                    connection.execute(
                        text(
                            "ALTER TABLE alembic_version "
                            "ALTER COLUMN version_num TYPE VARCHAR(255)"
                        )
                    )
                    connection.commit()
            except Exception:
                # 테이블 없음, 이미 확장됨, 권한 등은 무시
                pass

        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

