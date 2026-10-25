"""Selective mutable drafts only; no snapshot, share or canonical mutation."""
from alembic import op

revision = '0007_projection_drafts'
down_revision = '0006_owner_organization'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE projection_drafts (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL REFERENCES context_spaces(id),
            recipient_kind text NOT NULL CHECK (recipient_kind IN ('subject','category')),
            recipient text NOT NULL CHECK (length(btrim(recipient)) BETWEEN 1 AND 256),
            purpose text NOT NULL CHECK (length(btrim(purpose)) BETWEEN 1 AND 1024),
            expires_at timestamptz,
            version bigint NOT NULL CHECK (version > 0),
            state text NOT NULL DEFAULT 'draft' CHECK (state='draft'),
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            UNIQUE(id,context_space_id)
        );
        CREATE INDEX ix_projection_drafts_space ON projection_drafts(context_space_id,id);
        CREATE TABLE projection_draft_entries (
            draft_id uuid NOT NULL,
            context_space_id uuid NOT NULL,
            effect text NOT NULL CHECK (effect IN ('include','exclude')),
            item_id uuid NOT NULL,
            revision_id uuid NOT NULL,
            PRIMARY KEY(draft_id,effect,revision_id),
            FOREIGN KEY(draft_id,context_space_id) REFERENCES projection_drafts(id,context_space_id),
            FOREIGN KEY(revision_id,context_space_id) REFERENCES understanding_item_revisions(id,context_space_id),
            FOREIGN KEY(revision_id,item_id) REFERENCES understanding_item_revisions(id,item_id)
        );
        CREATE FUNCTION qh_guard_projection_draft() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.id<>OLD.id OR NEW.context_space_id<>OLD.context_space_id
               OR NEW.created_at<>OLD.created_at OR NEW.version<>OLD.version+1 THEN
                RAISE EXCEPTION 'Invalid draft identity or version' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER qh_projection_draft_identity BEFORE UPDATE ON projection_drafts
            FOR EACH ROW EXECUTE FUNCTION qh_guard_projection_draft();
    """)


def downgrade():
    raise RuntimeError('Draft preservation requires reviewed forward repair')
