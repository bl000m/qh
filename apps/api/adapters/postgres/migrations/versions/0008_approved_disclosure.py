"""Materialized minimized snapshots and exact private anchors; isolated-only."""
from alembic import op

revision = '0008_approved_disclosure'
down_revision = '0007_projection_drafts'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE TABLE disclosure_previews (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL REFERENCES context_spaces(id),
            draft_id uuid,
            policy jsonb NOT NULL CHECK (jsonb_typeof(policy)='object'),
            selection_stamp text NOT NULL CHECK (selection_stamp ~ '^[a-f0-9]{64}$'),
            fingerprint text NOT NULL CHECK (fingerprint ~ '^[a-f0-9]{64}$'),
            payload jsonb NOT NULL CHECK (payload->>'format'='qh.disclosure/1' AND jsonb_typeof(payload->'items')='array'),
            report jsonb NOT NULL CHECK (jsonb_typeof(report)='object'),
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            UNIQUE(id,context_space_id),
            FOREIGN KEY(draft_id,context_space_id) REFERENCES projection_drafts(id,context_space_id)
        );
        CREATE INDEX ix_disclosure_previews_scope ON disclosure_previews(context_space_id,id);
        CREATE TABLE approved_snapshots (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL REFERENCES context_spaces(id),
            preview_id uuid NOT NULL UNIQUE,
            fingerprint text NOT NULL CHECK (fingerprint ~ '^[a-f0-9]{64}$'),
            policy jsonb NOT NULL CHECK (jsonb_typeof(policy)='object'),
            payload jsonb NOT NULL CHECK (payload->>'format'='qh.disclosure/1'
                AND jsonb_typeof(payload->'items')='array' AND jsonb_array_length(payload->'items') BETWEEN 1 AND 100),
            accepted_exceptions jsonb NOT NULL CHECK (jsonb_typeof(accepted_exceptions)='array'),
            approved_by uuid NOT NULL REFERENCES users(id),
            approved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            UNIQUE(id,context_space_id),
            FOREIGN KEY(preview_id,context_space_id) REFERENCES disclosure_previews(id,context_space_id)
        );
        CREATE INDEX ix_approved_snapshots_scope ON approved_snapshots(context_space_id,id);
        CREATE TABLE approved_snapshot_revisions (
            snapshot_id uuid NOT NULL,
            context_space_id uuid NOT NULL,
            reference text NOT NULL CHECK (reference ~ '^R[1-9][0-9]*$'),
            item_id uuid NOT NULL,
            revision_id uuid NOT NULL,
            PRIMARY KEY(snapshot_id,reference),
            UNIQUE(snapshot_id,revision_id),
            FOREIGN KEY(snapshot_id,context_space_id) REFERENCES approved_snapshots(id,context_space_id),
            FOREIGN KEY(revision_id,context_space_id) REFERENCES understanding_item_revisions(id,context_space_id),
            FOREIGN KEY(revision_id,item_id) REFERENCES understanding_item_revisions(id,item_id)
        );
    ''')
    for table in ('disclosure_previews', 'approved_snapshots', 'approved_snapshot_revisions'):
        op.execute(f'CREATE TRIGGER qh_immutable_row BEFORE UPDATE OR DELETE ON {table} '
            'FOR EACH ROW EXECUTE FUNCTION qh_reject_immutable_change()')
        op.execute(f'CREATE TRIGGER qh_immutable_truncate BEFORE TRUNCATE ON {table} '
            'FOR EACH STATEMENT EXECUTE FUNCTION qh_reject_immutable_change()')


def downgrade():
    raise RuntimeError('Approved snapshot history requires reviewed forward repair')
