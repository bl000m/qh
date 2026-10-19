"""Owner-approved organization metadata only; no canonical content changes."""
from alembic import op

revision = '0006_owner_organization'
down_revision = '0005_retire_legacy_category'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE owner_organization (
            owner_id uuid PRIMARY KEY REFERENCES users(id),
            version bigint NOT NULL CHECK (version > 0),
            document jsonb NOT NULL CHECK (jsonb_typeof(document)='object')
        )
    """)


def downgrade():
    raise RuntimeError('Owner metadata preservation requires reviewed forward repair')
