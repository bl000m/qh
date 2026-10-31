"""Context Space intake and immutable consolidated versions; activation is separate."""
from alembic import op

revision = '0010_context_consolidation'
down_revision = '0009_guest_invitations'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE context_intake (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL REFERENCES context_spaces(id),
            document jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            UNIQUE(id,context_space_id)
        );
        CREATE INDEX ix_context_intake_scope ON context_intake(context_space_id,created_at,id);
        CREATE TABLE context_consolidations (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL REFERENCES context_spaces(id),
            version integer NOT NULL CHECK(version>0),
            intake_ids uuid[] NOT NULL,
            source_revision_id uuid NOT NULL,
            revision_ids uuid[] NOT NULL,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            UNIQUE(context_space_id,version),
            FOREIGN KEY(source_revision_id,context_space_id) REFERENCES source_revisions(id,context_space_id)
        );
        CREATE TABLE context_consolidation_jobs (
            context_space_id uuid PRIMARY KEY REFERENCES context_spaces(id),
            operation_id uuid NOT NULL,
            state text NOT NULL CHECK(state IN ('running','failed','idle')),
            started_at timestamptz NOT NULL DEFAULT clock_timestamp()
        );
    """)
    for table in ('context_intake', 'context_consolidations'):
        op.execute(f'CREATE TRIGGER qh_context_immutable BEFORE UPDATE OR DELETE ON {table} '
                   'FOR EACH ROW EXECUTE FUNCTION qh_reject_immutable_change()')


def downgrade():
    raise RuntimeError('Retained intake and consolidation history cannot be discarded')
