"""Alembic uses the same validated, timeout-bounded settings as the API."""

from alembic import context

from relevo.config import Settings
from relevo.db.connection import build_engine
from relevo.db.models import Base
from relevo.demo.models import DemoBase

config = context.config
settings = config.attributes.get("settings") or Settings()
metadata = [Base.metadata, DemoBase.metadata]


def include_name(name, type_, parent_names):
    return type_ != "schema" or name in (None, "relevo_demo")


if context.is_offline_mode():
    context.configure(
        url=settings.database_url.get_secret_value(),
        target_metadata=metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(settings)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=metadata,
                include_schemas=True,
                include_name=include_name,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
