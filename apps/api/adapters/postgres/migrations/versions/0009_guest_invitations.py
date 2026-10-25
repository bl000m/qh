"""Mailbox-verified snapshot invitations and transient sessions; isolated-only."""
from alembic import op

revision = '0009_guest_invitations'
down_revision = '0008_approved_disclosure'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
        CREATE TABLE guest_invitations (
            id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL,
            snapshot_id uuid NOT NULL,
            token_hash text NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            send_count integer NOT NULL DEFAULT 0 CHECK (send_count BETWEEN 0 AND 3),
            failed_verifications integer NOT NULL DEFAULT 0 CHECK (failed_verifications BETWEEN 0 AND 10),
            last_sent_at timestamptz,
            FOREIGN KEY(snapshot_id,context_space_id) REFERENCES approved_snapshots(id,context_space_id)
        );
        CREATE INDEX ix_guest_invitations_scope ON guest_invitations(context_space_id,created_at DESC,id);
        CREATE TABLE guest_challenges (
            id uuid PRIMARY KEY,
            invitation_id uuid NOT NULL REFERENCES guest_invitations(id),
            code_hash text NOT NULL CHECK (code_hash ~ '^[a-f0-9]{64}$'),
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            attempts integer NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 5),
            used_at timestamptz,
            invalidated_at timestamptz,
            delivery_state text NOT NULL DEFAULT 'pending' CHECK (delivery_state IN ('pending','sent','failed')),
            UNIQUE(id,invitation_id)
        );
        CREATE INDEX ix_guest_challenges_invitation ON guest_challenges(invitation_id,id);
        CREATE TABLE guest_sessions (
            id uuid PRIMARY KEY,
            invitation_id uuid NOT NULL REFERENCES guest_invitations(id),
            challenge_id uuid NOT NULL UNIQUE,
            token_hash text NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            revoked_at timestamptz,
            FOREIGN KEY(challenge_id,invitation_id) REFERENCES guest_challenges(id,invitation_id)
        );
        CREATE TABLE guest_request_limits (
            key_hash text PRIMARY KEY CHECK (key_hash ~ '^[a-f0-9]{64}$'),
            window_start timestamptz NOT NULL,
            requests integer NOT NULL CHECK (requests > 0)
        );
        CREATE FUNCTION qh_guard_guest_update() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE mutable text[];
        BEGIN
            IF TG_TABLE_NAME='guest_invitations' THEN
                mutable=ARRAY['revoked_at','send_count','failed_verifications','last_sent_at'];
                IF NEW.send_count<OLD.send_count OR NEW.failed_verifications<OLD.failed_verifications
                    OR (OLD.last_sent_at IS NOT NULL AND (NEW.last_sent_at IS NULL OR NEW.last_sent_at<OLD.last_sent_at)) THEN
                    RAISE EXCEPTION 'Guest counters cannot reset' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='guest_challenges' THEN
                mutable=ARRAY['attempts','used_at','invalidated_at','delivery_state'];
                IF NEW.attempts<OLD.attempts OR (OLD.delivery_state<>'pending' AND NEW.delivery_state<>OLD.delivery_state)
                    OR (OLD.used_at IS NOT NULL AND NEW.used_at IS DISTINCT FROM OLD.used_at)
                    OR (OLD.invalidated_at IS NOT NULL AND NEW.invalidated_at IS DISTINCT FROM OLD.invalidated_at) THEN
                    RAISE EXCEPTION 'Guest challenge cannot reset' USING ERRCODE='23514';
                END IF;
            ELSE
                mutable=ARRAY['revoked_at'];
            END IF;
            IF (to_jsonb(NEW)-mutable) IS DISTINCT FROM (to_jsonb(OLD)-mutable)
                OR ((to_jsonb(OLD)->>'revoked_at') IS NOT NULL
                    AND (to_jsonb(NEW)->'revoked_at') IS DISTINCT FROM (to_jsonb(OLD)->'revoked_at')) THEN
                RAISE EXCEPTION 'Guest binding is immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END $$;
    ''')
    for table in ('guest_invitations', 'guest_challenges', 'guest_sessions'):
        op.execute(f'CREATE TRIGGER qh_guest_binding BEFORE UPDATE ON {table} '
            'FOR EACH ROW EXECUTE FUNCTION qh_guard_guest_update()')
        op.execute(f'CREATE TRIGGER qh_guest_history BEFORE DELETE ON {table} '
            'FOR EACH ROW EXECUTE FUNCTION qh_reject_immutable_change()')
        op.execute(f'CREATE TRIGGER qh_guest_history_truncate BEFORE TRUNCATE ON {table} '
            'FOR EACH STATEMENT EXECUTE FUNCTION qh_reject_immutable_change()')


def downgrade():
    raise RuntimeError('Guest access/audit history requires reviewed forward repair')
