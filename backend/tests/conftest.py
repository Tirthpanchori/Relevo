"""Unit tests require no services; integration tests use only an explicit *_test database."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url

from relevo.api.app import create_app
from relevo.config import Settings
from relevo.db.connection import build_engine
from tests.accounting import assert_job_accounting

TEST_TOKEN = "test-only-token-never-use-outside-tests-12345"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption("--recordings-dir", help="Write sanitized actual execution recordings")


def migration_config(settings: Settings) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    return config


@pytest.fixture
def unit_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://unused:unused@127.0.0.1:1/unused",
        api_token=TEST_TOKEN,
        db_connect_timeout_seconds=1,
    )


@pytest.fixture(scope="session")
def db_settings() -> Settings:
    database_url = os.environ.get("RELEVO_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set RELEVO_TEST_DATABASE_URL to a dedicated PostgreSQL *_test database")
    if not (make_url(database_url).database or "").endswith("_test"):
        pytest.fail("Integration tests refuse a database whose name does not end in _test")
    return Settings(database_url=database_url, api_token=TEST_TOKEN, db_pool_size=12)


@pytest.fixture(scope="session")
def migrated_engine(db_settings: Settings) -> Iterator[Engine]:
    command.upgrade(migration_config(db_settings), "head")
    engine = build_engine(db_settings)
    yield engine
    engine.dispose()


@pytest.fixture
def db_engine(migrated_engine: Engine) -> Iterator[Engine]:
    # This database is dedicated to tests. Never truncate a development or arbitrary URL.
    with migrated_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE relevo_demo.effects, relevo_demo.operations, job_events, attempts, jobs")
        )
    yield migrated_engine
    assert_job_accounting(migrated_engine)


@pytest.fixture
def api_client(db_engine: Engine, db_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(db_settings)) as client:
        client.headers["Authorization"] = f"Bearer {TEST_TOKEN}"
        yield client
