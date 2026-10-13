"""QH-4: canonical sources and understanding; no feature workflows."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_qh_schema"
down_revision = None
branch_labels = None
depends_on = None

CATEGORIES = "'objective','current_state','decision','hypothesis','open_question','constraint','preference','concept','entity','relationship','uncertainty'"


def identity_columns() -> list:
    return [sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP"))]


def metadata_columns() -> list:
    return [sa.Column("status", sa.String(32), nullable=False, server_default="active"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                      server_default=sa.text("CURRENT_TIMESTAMP"))]


def upgrade() -> None:
    op.create_table("users", *identity_columns(), *metadata_columns(),
                    sa.Column("display_name", sa.Text(), nullable=False),
                    sa.CheckConstraint("btrim(status) <> ''", name="ck_users_status"))
    op.create_table("context_spaces", *identity_columns(), *metadata_columns(),
                    sa.Column("owner_id", sa.Uuid(), nullable=False),
                    sa.Column("name", sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT", name="fk_spaces_owner"),
                    sa.CheckConstraint("btrim(status) <> ''", name="ck_spaces_status"))
    op.create_table("sources", *identity_columns(), *metadata_columns(),
                    sa.Column("context_space_id", sa.Uuid(), nullable=False),
                    sa.Column("name", sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(["context_space_id"], ["context_spaces.id"], ondelete="RESTRICT", name="fk_sources_space"),
                    sa.UniqueConstraint("id", "context_space_id", name="uq_sources_id_space"),
                    sa.CheckConstraint("btrim(status) <> ''", name="ck_sources_status"))
    op.create_table("source_revisions", *identity_columns(),
                    sa.Column("source_id", sa.Uuid(), nullable=False),
                    sa.Column("context_space_id", sa.Uuid(), nullable=False),
                    sa.Column("revision_no", sa.Integer(), nullable=False),
                    sa.Column("content", sa.Text(), nullable=False),
                    sa.Column("origin", postgresql.JSONB(), nullable=False),
                    sa.ForeignKeyConstraint(["source_id", "context_space_id"], ["sources.id", "sources.context_space_id"],
                                            ondelete="RESTRICT", name="fk_source_revisions_space"),
                    sa.UniqueConstraint("source_id", "revision_no", name="uq_source_revision_number"),
                    sa.UniqueConstraint("id", "context_space_id", name="uq_source_revision_id_space"),
                    sa.CheckConstraint("revision_no > 0", name="ck_source_revision_number"),
                    sa.CheckConstraint("jsonb_typeof(origin) = 'object'", name="ck_source_origin_object"))
    op.create_table("understanding_items", *identity_columns(),
                    sa.Column("context_space_id", sa.Uuid(), nullable=False),
                    sa.Column("current_revision_id", sa.Uuid(), nullable=True),
                    sa.ForeignKeyConstraint(["context_space_id"], ["context_spaces.id"], ondelete="RESTRICT", name="fk_items_space"),
                    sa.UniqueConstraint("id", "context_space_id", name="uq_items_id_space"))
    op.create_table("understanding_item_revisions", *identity_columns(),
                    sa.Column("item_id", sa.Uuid(), nullable=False),
                    sa.Column("context_space_id", sa.Uuid(), nullable=False),
                    sa.Column("revision_no", sa.Integer(), nullable=False),
                    sa.Column("category", sa.String(32), nullable=False),
                    sa.Column("content", postgresql.JSONB(), nullable=False),
                    sa.Column("origin_kind", sa.String(16), nullable=False),
                    sa.Column("validation_state", sa.String(16), nullable=False),
                    sa.Column("validated_by", sa.Uuid(), nullable=True),
                    sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("based_on_revision_id", sa.Uuid(), nullable=True),
                    sa.ForeignKeyConstraint(["item_id", "context_space_id"], ["understanding_items.id", "understanding_items.context_space_id"],
                                            ondelete="RESTRICT", name="fk_item_revisions_space"),
                    sa.ForeignKeyConstraint(["validated_by"], ["users.id"], ondelete="RESTRICT", name="fk_revision_validator"),
                    sa.UniqueConstraint("item_id", "revision_no", name="uq_item_revision_number"),
                    sa.UniqueConstraint("id", "item_id", name="uq_item_revision_id_item"),
                    sa.UniqueConstraint("id", "context_space_id", name="uq_item_revision_id_space"),
                    sa.ForeignKeyConstraint(["based_on_revision_id", "item_id"], ["understanding_item_revisions.id", "understanding_item_revisions.item_id"],
                                            ondelete="RESTRICT", name="fk_revision_predecessor"),
                    sa.CheckConstraint("revision_no > 0", name="ck_item_revision_number"),
                    sa.CheckConstraint(f"category IN ({CATEGORIES})", name="ck_item_category"),
                    sa.CheckConstraint("jsonb_typeof(content) = 'object'", name="ck_item_content_object"),
                    sa.CheckConstraint("origin_kind IN ('human','ai','import')", name="ck_item_origin"),
                    sa.CheckConstraint("validation_state IN ('proposed','confirmed','rejected')", name="ck_item_validation"),
                    sa.CheckConstraint("(validation_state = 'proposed' AND validated_by IS NULL AND validated_at IS NULL) OR "
                                       "(validation_state IN ('confirmed','rejected') AND validated_by IS NOT NULL AND validated_at IS NOT NULL)",
                                       name="ck_item_validation_actor"),
                    sa.CheckConstraint("based_on_revision_id IS NULL OR based_on_revision_id <> id", name="ck_revision_not_self"))
    op.create_foreign_key("fk_current_revision_item", "understanding_items", "understanding_item_revisions",
                          ["current_revision_id", "id"], ["id", "item_id"], ondelete="RESTRICT")
    op.create_table("item_revision_provenance",
                    sa.Column("item_revision_id", sa.Uuid(), primary_key=True),
                    sa.Column("source_revision_id", sa.Uuid(), primary_key=True),
                    sa.Column("context_space_id", sa.Uuid(), nullable=False),
                    sa.ForeignKeyConstraint(["item_revision_id", "context_space_id"], ["understanding_item_revisions.id", "understanding_item_revisions.context_space_id"],
                                            ondelete="RESTRICT", deferrable=True, initially="DEFERRED", name="fk_provenance_item_space"),
                    sa.ForeignKeyConstraint(["source_revision_id", "context_space_id"], ["source_revisions.id", "source_revisions.context_space_id"],
                                            ondelete="RESTRICT", name="fk_provenance_source_space"))
    op.create_index("ix_spaces_owner", "context_spaces", ["owner_id"])
    for table in ("sources", "understanding_items"):
        op.create_index(f"ix_{table}_space", table, ["context_space_id"])
    op.create_index("ix_provenance_source", "item_revision_provenance", ["source_revision_id"])

    op.execute("""
    CREATE FUNCTION public.qh_reject_immutable_change() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        RAISE EXCEPTION 'QH revision/provenance is immutable' USING ERRCODE = '23514';
    END $$;
    """)
    for table in ("source_revisions", "understanding_item_revisions", "item_revision_provenance"):
        op.execute(f"CREATE TRIGGER qh_immutable_row BEFORE UPDATE OR DELETE ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION public.qh_reject_immutable_change()")
        op.execute(f"CREATE TRIGGER qh_immutable_truncate BEFORE TRUNCATE ON {table} "
                   "FOR EACH STATEMENT EXECUTE FUNCTION public.qh_reject_immutable_change()")
    op.execute("""
    CREATE FUNCTION public.qh_guard_provenance_publication() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE revision_id uuid;
    BEGIN
        IF TG_TABLE_NAME = 'item_revision_provenance' THEN
            revision_id := NEW.item_revision_id;
        ELSE
            revision_id := NEW.id;
        END IF;
        -- Serialize publication and provenance assembly even across connections.
        PERFORM pg_advisory_xact_lock(hashtextextended(revision_id::text, 0));
        IF TG_TABLE_NAME = 'item_revision_provenance' AND EXISTS
            (SELECT 1 FROM public.understanding_item_revisions WHERE id = revision_id) THEN
            RAISE EXCEPTION 'Provenance must be assembled before publishing its immutable revision'
                USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END $$;
    CREATE TRIGGER qh_publish_revision BEFORE INSERT ON understanding_item_revisions
        FOR EACH ROW EXECUTE FUNCTION public.qh_guard_provenance_publication();
    CREATE TRIGGER qh_assemble_provenance BEFORE INSERT ON item_revision_provenance
        FOR EACH ROW EXECUTE FUNCTION public.qh_guard_provenance_publication();
    """)
    op.execute("""
    CREATE FUNCTION public.qh_guard_current_revision() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.current_revision_id IS NOT NULL AND NOT EXISTS
            (SELECT 1 FROM public.understanding_item_revisions
             WHERE id = NEW.current_revision_id AND item_id = NEW.id AND validation_state = 'confirmed') THEN
            RAISE EXCEPTION 'Current revision must be a confirmed revision of this item'
                USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END $$;
    CREATE TRIGGER qh_current_confirmed BEFORE INSERT OR UPDATE ON understanding_items
        FOR EACH ROW EXECUTE FUNCTION public.qh_guard_current_revision();
    """)


def downgrade() -> None:
    op.drop_constraint("fk_current_revision_item", "understanding_items", type_="foreignkey")
    for table in ("item_revision_provenance", "understanding_item_revisions", "understanding_items",
                  "source_revisions", "sources", "context_spaces", "users"):
        op.drop_table(table)
    for function in ("qh_guard_current_revision", "qh_guard_provenance_publication", "qh_reject_immutable_change"):
        op.execute(f"DROP FUNCTION public.{function}()")
