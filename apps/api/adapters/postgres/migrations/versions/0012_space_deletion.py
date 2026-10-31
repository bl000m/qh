"""Explicit confirmed owner erasure; installation never deletes application data."""
from alembic import op

revision = '0012_space_deletion'
down_revision = '0011_source_documents'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE TABLE context_space_deletions (
            context_space_id uuid PRIMARY KEY,
            owner_id uuid NOT NULL REFERENCES users(id),
            confirmation_sha256 text NOT NULL CHECK(confirmation_sha256 ~ '^[a-f0-9]{64}$'),
            state text NOT NULL CHECK(state IN ('deleting','complete')),
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            completed_at timestamptz
        );
        CREATE OR REPLACE FUNCTION public.qh_reject_immutable_change()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE scope uuid;
        BEGIN
            IF TG_OP='DELETE' AND nullif(current_setting('qh.purge_scope',true),'') IS NOT NULL THEN
                scope := (to_jsonb(OLD)->>'context_space_id')::uuid;
                IF scope IS NULL AND TG_TABLE_NAME IN ('guest_sessions','guest_challenges') THEN
                    SELECT context_space_id INTO scope FROM guest_invitations
                    WHERE id=(to_jsonb(OLD)->>'invitation_id')::uuid;
                END IF;
                IF scope::text=current_setting('qh.purge_scope',true) AND EXISTS (
                    SELECT 1 FROM context_space_deletions d JOIN context_spaces s ON s.id=d.context_space_id
                    WHERE d.context_space_id=scope AND d.state='deleting' AND s.status='deleting'
                    AND s.owner_id=d.owner_id AND d.owner_id::text=current_setting('qh.purge_owner',true)
                ) THEN RETURN OLD; END IF;
            END IF;
            RAISE EXCEPTION 'QH revision/provenance is immutable' USING ERRCODE='23514';
        END $$;
    ''')


def downgrade():
    raise RuntimeError('Owner erasure requires reviewed forward repair')
