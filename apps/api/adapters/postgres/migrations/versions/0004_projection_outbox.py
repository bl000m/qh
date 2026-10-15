"""QH-30: transactional projection intent and per-scope sync/fencing state."""

from alembic import op

revision = "0004_projection_outbox"
down_revision = "0003_native_semantics"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE context_projection_state (
      context_space_id uuid PRIMARY KEY REFERENCES context_spaces(id) ON DELETE RESTRICT,
      epoch uuid NOT NULL DEFAULT gen_random_uuid(),
      desired_version bigint NOT NULL DEFAULT 0,
      applied_version bigint NOT NULL DEFAULT 0,
      last_success_at timestamptz,
      CHECK (applied_version>=0 AND desired_version>=applied_version)
    );
    CREATE TABLE projection_outbox (
      id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      context_space_id uuid NOT NULL REFERENCES context_projection_state(context_space_id),
      scope_version bigint NOT NULL CHECK (scope_version>0),
      item_id uuid NOT NULL,
      revision_id uuid,
      kind text NOT NULL CHECK (kind IN ('revision','current')),
      state text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','processing','ready','failed')),
      attempts integer NOT NULL DEFAULT 0 CHECK (attempts>=0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      lease_token uuid,
      lease_until timestamptz,
      completed_at timestamptz,
      error_code text,
      error_type text,
      UNIQUE(context_space_id,scope_version),
      FOREIGN KEY(item_id,context_space_id) REFERENCES understanding_items(id,context_space_id),
      FOREIGN KEY(revision_id,item_id,context_space_id)
        REFERENCES understanding_item_revisions(id,item_id,context_space_id),
      CHECK (kind<>'revision' OR revision_id IS NOT NULL),
      CHECK ((state='processing')=(lease_token IS NOT NULL AND lease_until IS NOT NULL))
    );
    CREATE UNIQUE INDEX uq_projection_revision_intent ON projection_outbox(revision_id) WHERE kind='revision';
    CREATE INDEX ix_projection_pending ON projection_outbox(context_space_id,scope_version)
      WHERE state<>'ready';
    CREATE INDEX ix_projection_retry ON projection_outbox(available_at) WHERE state IN ('pending','failed');
    INSERT INTO context_projection_state(context_space_id) SELECT id FROM context_spaces;
    INSERT INTO projection_outbox(context_space_id,scope_version,item_id,revision_id,kind)
      SELECT context_space_id,row_number() OVER (PARTITION BY context_space_id ORDER BY created_at,id),item_id,id,'revision'
      FROM understanding_item_revisions;
    UPDATE context_projection_state s SET desired_version=(
      SELECT count(*) FROM projection_outbox o WHERE o.context_space_id=s.context_space_id);

    CREATE FUNCTION public.qh30_outbox_identity() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF (NEW.id,NEW.context_space_id,NEW.scope_version,NEW.item_id,NEW.revision_id,NEW.kind,NEW.created_at)
         IS DISTINCT FROM (OLD.id,OLD.context_space_id,OLD.scope_version,OLD.item_id,OLD.revision_id,OLD.kind,OLD.created_at) THEN
        RAISE EXCEPTION 'Projection intent identity is immutable' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER qh30_outbox_identity BEFORE UPDATE ON projection_outbox
      FOR EACH ROW EXECUTE FUNCTION public.qh30_outbox_identity();

    CREATE FUNCTION public.qh30_projection_scope() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      INSERT INTO public.context_projection_state(context_space_id) VALUES(NEW.id);
      RETURN NEW;
    END $$;
    CREATE TRIGGER qh30_projection_scope AFTER INSERT ON context_spaces
      FOR EACH ROW EXECUTE FUNCTION public.qh30_projection_scope();

    CREATE FUNCTION public.qh30_enqueue_projection() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE next_version bigint; scope uuid; item uuid; rev uuid; event_kind text;
    BEGIN
      IF TG_TABLE_NAME='understanding_item_revisions' THEN
        scope:=NEW.context_space_id; item:=NEW.item_id; rev:=NEW.id; event_kind:='revision';
      ELSE
        IF NEW.current_revision_id IS NOT DISTINCT FROM OLD.current_revision_id THEN RETURN NEW; END IF;
        scope:=NEW.context_space_id; item:=NEW.id; rev:=NEW.current_revision_id; event_kind:='current';
      END IF;
      -- Row lock makes version allocation and commit order serial within the scope.
      UPDATE public.context_projection_state SET desired_version=desired_version+1
        WHERE context_space_id=scope RETURNING desired_version INTO next_version;
      IF NOT FOUND THEN RAISE EXCEPTION 'Projection state missing' USING ERRCODE='23514'; END IF;
      INSERT INTO public.projection_outbox(context_space_id,scope_version,item_id,revision_id,kind)
        VALUES(scope,next_version,item,rev,event_kind);
      RETURN NEW;
    END $$;
    CREATE TRIGGER qh30_enqueue_revision AFTER INSERT ON understanding_item_revisions
      FOR EACH ROW EXECUTE FUNCTION public.qh30_enqueue_projection();
    CREATE TRIGGER qh30_enqueue_current AFTER UPDATE OF current_revision_id ON understanding_items
      FOR EACH ROW EXECUTE FUNCTION public.qh30_enqueue_projection();
    """)


def downgrade():
    raise RuntimeError(
        "Projection outbox is forward-only; do not discard unacknowledged work"
    )
