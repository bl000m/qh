"""Retire unused legacy metadata, preserving registered historical bindings.

Prepared for a separately authorized upgrade. Non-null historical categories
block this migration: their explicit archival/mapping requires a separate review.
No immutable record, registry entry, schema, provenance or binding is rewritten.
"""

from alembic import op

revision = "0005_retire_legacy_category"
down_revision = "0004_projection_outbox"
branch_labels = None
depends_on = None


def upgrade():
    # Lock before checking so publication cannot race the precondition/DDL.
    op.execute(
        "LOCK TABLE public.understanding_item_revisions IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM public.understanding_item_revisions WHERE category IS NOT NULL) THEN
        RAISE EXCEPTION 'Historical category data requires explicit preservation review';
      END IF;
    END $$;
    CREATE OR REPLACE FUNCTION public.qh30_publish() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'Semantic publication requires READ COMMITTED' USING ERRCODE='23514';
      END IF;
      PERFORM 1 FROM public.understanding_items WHERE id=NEW.item_id FOR UPDATE;
      RETURN NEW;
    END $$;
    """)
    # No CASCADE: unexpected dependent objects must block rather than disappear.
    op.drop_column("understanding_item_revisions", "category")


def downgrade():
    raise RuntimeError("Forward-only semantic cleanup; use reviewed forward repair")
