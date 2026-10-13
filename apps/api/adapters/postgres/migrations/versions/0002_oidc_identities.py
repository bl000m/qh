"""Add external identity mapping without modifying canonical QH-4 tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_oidc_identities"
down_revision = "0001_qh_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_identities",
        sa.Column("issuer", sa.Text(), primary_key=True),
        sa.Column("subject", sa.Text(), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint("btrim(issuer) <> ''", name="ck_identity_issuer"),
        sa.CheckConstraint("btrim(subject) <> ''", name="ck_identity_subject"),
    )
    op.create_index("ix_user_identities_user_id", "user_identities", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_identities")
