"""Migration boundary; intentionally independent of FastAPI and QH Core."""

from alembic import context
from sqlalchemy import create_engine, pool

from adapters.postgres.config import database_url

# Handwritten migrations are the schema authority. No duplicate ORM models.
if context.is_offline_mode():
    context.configure(
        url=database_url(), target_metadata=None,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(database_url(), poolclass=pool.NullPool, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
