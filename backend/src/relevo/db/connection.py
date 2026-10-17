"""Synchronous connections for bounded transactions in FastAPI's worker threads."""

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, create_engine, text

from relevo.config import Settings


def build_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=0,
        pool_timeout=settings.db_connect_timeout_seconds,
        hide_parameters=True,
        connect_args={
            "connect_timeout": settings.db_connect_timeout_seconds,
            "application_name": "relevo",
            "options": (
                f"-c statement_timeout={settings.db_statement_timeout_ms} "
                f"-c lock_timeout={settings.db_lock_timeout_ms} "
                "-c timezone=UTC -c synchronous_commit=on"
            ),
        },
    )


def schema_head() -> str:
    """Single expected migration head, usable regardless of the shell's cwd."""
    from pathlib import Path

    migration_path = Path(__file__).resolve().with_name("migrations")
    config = Config()
    config.set_main_option("script_location", str(migration_path))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("missing migration head")
    return head


def database_ready(engine: Engine, expected_head: str) -> bool:
    with engine.connect() as connection:
        # Include schema and durability checks: connectivity alone cannot promise safe acceptance.
        heads = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
        settings = connection.execute(
            text(
                "SELECT current_setting('fsync'), current_setting('full_page_writes'), "
                "current_setting('synchronous_commit')"
            )
        ).one()
        return heads == [expected_head] and settings == ("on", "on", "on")
