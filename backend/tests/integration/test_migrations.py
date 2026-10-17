import pytest
from alembic import command
from sqlalchemy import Engine, inspect

from relevo.config import Settings

from ..conftest import migration_config

pytestmark = pytest.mark.integration


def test_migration_roundtrip_and_metadata_match(db_engine: Engine, db_settings: Settings) -> None:
    config = migration_config(db_settings)
    command.check(config)
    command.downgrade(config, "base")
    assert set(inspect(db_engine).get_table_names()) == {"alembic_version"}
    assert "relevo_demo" not in inspect(db_engine).get_schema_names()
    command.upgrade(config, "head")
    assert {"jobs", "attempts", "job_events"}.issubset(inspect(db_engine).get_table_names())
    assert set(inspect(db_engine).get_table_names(schema="relevo_demo")) == {
        "operations",
        "effects",
    }
    command.check(config)
