import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


def make_database_url():
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "tg_bot" / ".env", override=False)
    test_username = os.environ.get('TEST_DB_USER')
    test_password = os.environ.get('TEST_DB_PASSWORD')
    test_host = os.environ.get('TEST_DB_HOST')
    test_port = int(os.environ.get('TEST_DB_PORT', '5432'))
    test_name = os.environ.get('TEST_DB_NAME')

    if not all([test_username, test_password, test_host, test_name]):
        raise RuntimeError('TEST_DB_USER, TEST_DB_PASSWORD, TEST_DB_HOST and TEST_DB_NAME are required')

    return URL.create(
        drivername="postgresql+psycopg",
        username=test_username,
        password=test_password,
        host=test_host,
        port=test_port,
        database=test_name,
    )


def make_alembic_config(engine):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    config.attributes["connection"] = engine
    return config


def drop_database_schema(engine):
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope='session')
def migrated_db_engine():
    database_url = make_database_url()
    engine = create_engine(database_url)
    alembic_config = make_alembic_config(engine)

    drop_database_schema(engine)
    command.upgrade(alembic_config, "head")

    yield engine

    drop_database_schema(engine)
    engine.dispose()


@pytest.fixture()
def db(migrated_db_engine):
    SessionLocal = sessionmaker(
        bind=migrated_db_engine,
        expire_on_commit=False,
    )

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def clean_db(migrated_db_engine):
    yield

    with migrated_db_engine.begin() as connection:
        table_names = connection.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename != 'alembic_version'
        """)).scalars().all()

        if table_names:
            quoted_table_names = ', '.join(f'"{table_name}"' for table_name in table_names)
            connection.execute(text(f'TRUNCATE {quoted_table_names} RESTART IDENTITY CASCADE'))
