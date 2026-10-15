"""QH-30: registered semantics, universal endpoints and temporal assertions.

Forward-only; QH-4/QH-5 rows are never rewritten. No automatic deployment binding.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_native_semantics"
down_revision = "0002_oidc_identities"
branch_labels = None
depends_on = None

LEGACY = (
    "objective",
    "current_state",
    "decision",
    "hypothesis",
    "open_question",
    "constraint",
    "preference",
    "concept",
    "entity",
    "relationship",
    "uncertainty",
)


def upgrade():
    op.execute("""
    CREATE FUNCTION public.qh30_schema_supported(s jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE AS $$
    DECLARE k text; v jsonb; t text;
    BEGIN
      IF s IS NULL OR jsonb_typeof(s) <> 'object' OR NOT s ? 'type' THEN RETURN false; END IF;
      t := s->>'type';
      IF t NOT IN ('object','string','integer','number','boolean','null','array')
        OR jsonb_typeof(s->'type') <> 'string' THEN RETURN false; END IF;
      FOR k,v IN SELECT * FROM jsonb_each(s) LOOP
        IF k NOT IN ('type','properties','required','additionalProperties','enum','items','minLength')
          THEN RETURN false; END IF;
        IF k='properties' THEN
          IF t<>'object' OR jsonb_typeof(v)<>'object' THEN RETURN false; END IF;
          IF EXISTS (SELECT 1 FROM jsonb_each(v) p WHERE NOT public.qh30_schema_supported(p.value))
            THEN RETURN false; END IF;
        ELSIF k='required' THEN
          IF t<>'object' OR jsonb_typeof(v)<>'array' THEN RETURN false; END IF;
          IF EXISTS (SELECT 1 FROM jsonb_array_elements(v) x WHERE jsonb_typeof(x)<>'string')
            THEN RETURN false; END IF;
        ELSIF k='additionalProperties' THEN
          IF t<>'object' OR jsonb_typeof(v)<>'boolean' THEN RETURN false; END IF;
        ELSIF k='enum' THEN
          IF jsonb_typeof(v)<>'array' OR jsonb_array_length(v)=0 THEN RETURN false; END IF;
        ELSIF k='items' THEN
          IF t<>'array' OR NOT public.qh30_schema_supported(v) THEN RETURN false; END IF;
        ELSIF k='minLength' THEN
          IF t<>'string' OR jsonb_typeof(v)<>'number' OR v::text !~ '^[0-9]+$'
            THEN RETURN false; END IF;
        END IF;
      END LOOP;
      RETURN true;
    END $$;
    CREATE FUNCTION public.qh30_schema_matches(s jsonb, value jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE AS $$
    DECLARE t text; k text; child jsonb;
    BEGIN
      IF value IS NULL OR NOT public.qh30_schema_supported(s) THEN RETURN false; END IF;
      t := s->>'type';
      IF t='integer' THEN
        IF jsonb_typeof(value)<>'number' THEN RETURN false; END IF;
        IF (value::text)::numeric <> trunc((value::text)::numeric) THEN RETURN false; END IF;
      ELSIF jsonb_typeof(value) <> t
        THEN RETURN false;
      END IF;
      IF s ? 'enum' AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(s->'enum') AS e(candidate) WHERE e.candidate=$2) THEN RETURN false; END IF;
      IF t='string' AND s ? 'minLength' AND length(value #>> '{}') < (s->>'minLength')::numeric
        THEN RETURN false; END IF;
      IF t='object' THEN
        FOR k IN SELECT jsonb_array_elements_text(COALESCE(s->'required','[]')) LOOP
          IF NOT value ? k THEN RETURN false; END IF;
        END LOOP;
        FOR k,child IN SELECT * FROM jsonb_each(value) LOOP
          IF COALESCE(s->'properties','{}') ? k THEN
            IF NOT public.qh30_schema_matches(s->'properties'->k,child) THEN RETURN false; END IF;
          ELSIF s->'additionalProperties'='false'::jsonb THEN RETURN false;
          END IF;
        END LOOP;
      ELSIF t='array' AND s ? 'items' THEN
        FOR child IN SELECT jsonb_array_elements(value) LOOP
          IF NOT public.qh30_schema_matches(s->'items',child) THEN RETURN false; END IF;
        END LOOP;
      END IF;
      RETURN true;
    END $$;
    """)
    op.create_table(
        "semantic_type_versions",
        sa.Column("type_id", sa.Text(), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True),
        sa.Column("structural_kind", sa.Text(), nullable=False),
        sa.Column("property_schema", JSONB(), nullable=False),
        sa.Column("relation_rules", JSONB(none_as_null=True), nullable=True),
        sa.Column(
            "validator_version", sa.Text(), nullable=False, server_default="qh-schema-1"
        ),
        sa.CheckConstraint(
            "type_id ~ '^[a-z][a-z0-9_]*[.][a-zA-Z0-9_.-]+$'",
            name="ck_semantic_namespace",
        ),
        sa.CheckConstraint("version > 0", name="ck_semantic_version"),
        sa.CheckConstraint(
            "structural_kind IN ('item','entity','relation')", name="ck_semantic_shape"
        ),
        sa.CheckConstraint(
            "validator_version='qh-schema-1' AND public.qh30_schema_supported(property_schema)",
            name="ck_semantic_schema",
        ),
    )
    op.create_unique_constraint(
        "uq_revision_item_space",
        "understanding_item_revisions",
        ["id", "item_id", "context_space_id"],
    )
    op.create_table(
        "item_revision_types",
        sa.Column("item_revision_id", sa.Uuid(), primary_key=True),
        sa.Column("context_space_id", sa.Uuid(), nullable=False),
        sa.Column("type_id", sa.Text(), nullable=False),
        sa.Column("type_version", sa.Integer(), nullable=False),
        *(
            sa.Column(n, sa.DateTime(timezone=True), nullable=True)
            for n in ("fact_from", "fact_to", "valid_from", "valid_to")
        ),
        sa.ForeignKeyConstraint(
            ["item_revision_id", "context_space_id"],
            [
                "understanding_item_revisions.id",
                "understanding_item_revisions.context_space_id",
            ],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            name="fk_semantic_revision_scope",
        ),
        sa.ForeignKeyConstraint(
            ["type_id", "type_version"],
            ["semantic_type_versions.type_id", "semantic_type_versions.version"],
            ondelete="RESTRICT",
            name="fk_semantic_registered_type",
        ),
        sa.CheckConstraint(
            "fact_from IS NULL OR fact_to IS NULL OR fact_from <= fact_to",
            name="ck_semantic_fact_time",
        ),
        sa.CheckConstraint(
            "valid_from IS NULL OR valid_to IS NULL OR valid_from < valid_to",
            name="ck_semantic_valid_time",
        ),
    )
    op.create_index(
        "ix_revision_registered_type",
        "item_revision_types",
        ["type_id", "type_version"],
    )
    op.create_table(
        "relation_revision_details",
        sa.Column("item_revision_id", sa.Uuid(), primary_key=True),
        sa.Column("context_space_id", sa.Uuid(), nullable=False),
        *(
            sa.Column(n, sa.Uuid(), nullable=False)
            for n in (
                "source_item_id",
                "source_revision_id",
                "target_item_id",
                "target_revision_id",
            )
        ),
        sa.Column("predicate", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["item_revision_id", "context_space_id"],
            [
                "understanding_item_revisions.id",
                "understanding_item_revisions.context_space_id",
            ],
            ondelete="RESTRICT",
            deferrable=True,
            initially="DEFERRED",
            name="fk_relation_parent_scope",
        ),
        *(
            sa.ForeignKeyConstraint(
                [f"{side}_revision_id", f"{side}_item_id", "context_space_id"],
                [
                    "understanding_item_revisions.id",
                    "understanding_item_revisions.item_id",
                    "understanding_item_revisions.context_space_id",
                ],
                ondelete="RESTRICT",
                deferrable=True,
                initially="DEFERRED",
                name=f"fk_relation_{side}_anchor",
            )
            for side in ("source", "target")
        ),
        sa.CheckConstraint("btrim(predicate) <> ''", name="ck_relation_predicate"),
    )
    for side in ("source", "target"):
        op.create_index(
            f"ix_relation_{side}",
            "relation_revision_details",
            [f"{side}_revision_id", f"{side}_item_id", "context_space_id"],
        )
    op.execute("""
    CREATE FUNCTION public.qh30_register_type() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE entry jsonb;
    BEGIN
      IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'Semantic publication requires READ COMMITTED' USING ERRCODE='23514';
      END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended('type:'||NEW.type_id,0));
      IF EXISTS (SELECT 1 FROM public.semantic_type_versions
                 WHERE type_id=NEW.type_id AND structural_kind<>NEW.structural_kind) THEN
        RAISE EXCEPTION 'Type structural shape is immutable across versions' USING ERRCODE='23514';
      END IF;
      IF NEW.structural_kind <> 'relation' THEN
        IF NEW.relation_rules IS NOT NULL THEN
          RAISE EXCEPTION 'Only relation types carry endpoint rules' USING ERRCODE='23514';
        END IF;
      ELSE
        IF NOT COALESCE(jsonb_typeof(NEW.relation_rules)='object'
          AND jsonb_typeof(NEW.relation_rules->'mode')='string'
          AND NEW.relation_rules->>'mode' IN ('allowlist','any_registered'),false) THEN
          RAISE EXCEPTION 'Explicit versioned relation rules required' USING ERRCODE='23514';
        END IF;
        IF EXISTS (SELECT 1 FROM jsonb_object_keys(NEW.relation_rules) k
                   WHERE k NOT IN ('mode','entries'))
          OR (NEW.relation_rules->>'mode'='any_registered' AND NEW.relation_rules ? 'entries') THEN
          RAISE EXCEPTION 'Unsupported relation rule fields' USING ERRCODE='23514';
        END IF;
        IF NEW.relation_rules->>'mode'='allowlist' THEN
          IF jsonb_typeof(NEW.relation_rules->'entries') IS DISTINCT FROM 'array' THEN
            RAISE EXCEPTION 'Endpoint allowlist required' USING ERRCODE='23514';
          END IF;
          IF jsonb_array_length(NEW.relation_rules->'entries')=0 THEN
            RAISE EXCEPTION 'Nonempty endpoint allowlist required' USING ERRCODE='23514';
          END IF;
          FOR entry IN SELECT jsonb_array_elements(NEW.relation_rules->'entries') LOOP
            IF jsonb_typeof(entry)<>'object' THEN
              RAISE EXCEPTION 'Invalid endpoint rule object' USING ERRCODE='23514';
            END IF;
            IF EXISTS (SELECT 1 FROM jsonb_object_keys(entry) k WHERE k NOT IN
                 ('predicate','source_type','source_version','target_type','target_version'))
               OR NOT COALESCE(
                 jsonb_typeof(entry->'predicate')='string' AND btrim(entry->>'predicate')<>''
                 AND jsonb_typeof(entry->'source_type')='string' AND btrim(entry->>'source_type')<>''
                 AND jsonb_typeof(entry->'target_type')='string' AND btrim(entry->>'target_type')<>''
                 AND jsonb_typeof(entry->'source_version')='number'
                 AND (entry->>'source_version') ~ '^[1-9][0-9]*$'
                 AND jsonb_typeof(entry->'target_version')='number'
                 AND (entry->>'target_version') ~ '^[1-9][0-9]*$',false) THEN
              RAISE EXCEPTION 'Invalid versioned endpoint rule' USING ERRCODE='23514';
            END IF;
          END LOOP;
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    """)
    op.execute(
        "CREATE TRIGGER qh30_register BEFORE INSERT ON semantic_type_versions FOR EACH ROW EXECUTE FUNCTION public.qh30_register_type()"
    )
    table = sa.table(
        "semantic_type_versions",
        sa.column("type_id", sa.Text()),
        sa.column("version", sa.Integer()),
        sa.column("structural_kind", sa.Text()),
        sa.column("property_schema", JSONB()),
        sa.column("relation_rules", JSONB(none_as_null=True)),
    )
    op.bulk_insert(
        table,
        [
            dict(
                type_id="qh." + c,
                version=1,
                structural_kind="entity"
                if c == "entity"
                else "relation"
                if c == "relationship"
                else "item",
                property_schema={"type": "object"},
                relation_rules={"mode": "any_registered"}
                if c == "relationship"
                else None,
            )
            for c in LEGACY
        ],
    )
    # Existing parent rows and provenance are untouched. Seed bindings before guards.
    op.execute("""
    LOCK TABLE understanding_items, understanding_item_revisions, item_revision_provenance IN SHARE ROW EXCLUSIVE MODE;
    INSERT INTO item_revision_types (item_revision_id,context_space_id,type_id,type_version)
      SELECT id,context_space_id,'qh.'||category,1 FROM understanding_item_revisions;
    -- Only a documented, complete legacy relation representation can be mapped.
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM understanding_item_revisions r
        JOIN item_revision_types t ON t.item_revision_id=r.id
        JOIN semantic_type_versions s ON (s.type_id,s.version)=(t.type_id,t.type_version)
        GROUP BY r.item_id HAVING count(DISTINCT s.structural_kind)>1) THEN
        RAISE EXCEPTION 'Mixed legacy structural shapes; review required' USING ERRCODE='23514';
      END IF;
      IF EXISTS (SELECT 1 FROM understanding_item_revisions WHERE category='relationship'
        AND (jsonb_typeof(content->'relation') IS DISTINCT FROM 'object'
          OR NOT (content->'relation') ?& ARRAY['source_item_id','source_revision_id','target_item_id','target_revision_id','predicate'])) THEN
        RAISE EXCEPTION 'Incomplete legacy relation; review required before migration' USING ERRCODE='23514';
      END IF;
      IF EXISTS (SELECT 1 FROM understanding_item_revisions WHERE content ? 'temporal') THEN
        RAISE EXCEPTION 'Legacy temporal assertions require explicit reviewed mapping' USING ERRCODE='23514';
      END IF;
    END $$;
    INSERT INTO relation_revision_details
      SELECT id,context_space_id,(content->'relation'->>'source_item_id')::uuid,
        (content->'relation'->>'source_revision_id')::uuid,
        (content->'relation'->>'target_item_id')::uuid,
        (content->'relation'->>'target_revision_id')::uuid,content->'relation'->>'predicate'
      FROM understanding_item_revisions WHERE category='relationship';
    SET CONSTRAINTS ALL IMMEDIATE;
    SET CONSTRAINTS ALL DEFERRED;
    """)
    op.alter_column(
        "understanding_item_revisions",
        "category",
        existing_type=sa.String(32),
        nullable=True,
    )
    op.drop_constraint(
        "ck_item_category", "understanding_item_revisions", type_="check"
    )
    op.execute("""
    CREATE FUNCTION public.qh30_assemble() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      PERFORM pg_advisory_xact_lock(hashtextextended(NEW.item_revision_id::text,0));
      IF EXISTS (SELECT 1 FROM public.understanding_item_revisions WHERE id=NEW.item_revision_id) THEN
        RAISE EXCEPTION 'Semantic metadata must precede immutable publication' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION public.qh30_publish() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.category IS NOT NULL THEN
        RAISE EXCEPTION 'Legacy category is not a current discriminator' USING ERRCODE='23514';
      END IF;
      IF current_setting('transaction_isolation') <> 'read committed' THEN
        RAISE EXCEPTION 'Semantic publication requires READ COMMITTED' USING ERRCODE='23514';
      END IF;
      PERFORM 1 FROM public.understanding_items WHERE id=NEW.item_id FOR UPDATE;
      RETURN NEW;
    END $$;
    CREATE FUNCTION public.qh30_verify_revision() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE binding record; detail record; source_binding record; target_binding record;
    BEGIN
      SELECT t.*,s.structural_kind,s.property_schema,s.relation_rules INTO binding
        FROM public.item_revision_types t JOIN public.semantic_type_versions s
        ON (s.type_id,s.version)=(t.type_id,t.type_version) WHERE t.item_revision_id=NEW.id;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'Registered type binding required' USING ERRCODE='23514';
      END IF;
      IF NOT public.qh30_schema_matches(binding.property_schema,NEW.content) THEN
        RAISE EXCEPTION 'Payload violates pinned schema' USING ERRCODE='23514';
      END IF;
      IF EXISTS (SELECT 1 FROM public.understanding_item_revisions r
         JOIN public.item_revision_types t ON t.item_revision_id=r.id
         JOIN public.semantic_type_versions s ON (s.type_id,s.version)=(t.type_id,t.type_version)
         WHERE r.item_id=NEW.item_id AND s.structural_kind<>binding.structural_kind) THEN
        RAISE EXCEPTION 'Item structural shape cannot change' USING ERRCODE='23514';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM public.item_revision_provenance WHERE item_revision_id=NEW.id) THEN
        RAISE EXCEPTION 'Source revision provenance required' USING ERRCODE='23514';
      END IF;
      SELECT * INTO detail FROM public.relation_revision_details WHERE item_revision_id=NEW.id;
      IF (binding.structural_kind='relation') <> FOUND THEN
        RAISE EXCEPTION 'Relation detail must match registered shape' USING ERRCODE='23514';
      END IF;
      IF binding.structural_kind='relation' THEN
        SELECT * INTO source_binding FROM public.item_revision_types WHERE item_revision_id=detail.source_revision_id;
        SELECT * INTO target_binding FROM public.item_revision_types WHERE item_revision_id=detail.target_revision_id;
        IF source_binding IS NULL OR target_binding IS NULL THEN
          RAISE EXCEPTION 'Endpoint type bindings required' USING ERRCODE='23514';
        END IF;
        IF binding.relation_rules->>'mode'='allowlist' AND NOT EXISTS (
          SELECT 1 FROM jsonb_array_elements(binding.relation_rules->'entries') e
          WHERE e->>'predicate'=detail.predicate
            AND e->>'source_type'=source_binding.type_id
            AND (e->>'source_version')::integer=source_binding.type_version
            AND e->>'target_type'=target_binding.type_id
            AND (e->>'target_version')::integer=target_binding.type_version) THEN
          RAISE EXCEPTION 'Relation violates pinned endpoint rules' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER qh30_publish_revision BEFORE INSERT ON understanding_item_revisions
      FOR EACH ROW EXECUTE FUNCTION public.qh30_publish();
    CREATE CONSTRAINT TRIGGER qh30_verify_revision AFTER INSERT ON understanding_item_revisions
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.qh30_verify_revision();
    """)
    for name in ("item_revision_types", "relation_revision_details"):
        op.execute(
            f"CREATE TRIGGER qh30_assemble BEFORE INSERT ON {name} FOR EACH ROW EXECUTE FUNCTION public.qh30_assemble()"
        )
    for name in (
        "semantic_type_versions",
        "item_revision_types",
        "relation_revision_details",
    ):
        op.execute(
            f"CREATE TRIGGER qh30_immutable_row BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION public.qh_reject_immutable_change()"
        )
        op.execute(
            f"CREATE TRIGGER qh30_immutable_truncate BEFORE TRUNCATE ON {name} FOR EACH STATEMENT EXECUTE FUNCTION public.qh_reject_immutable_change()"
        )


def downgrade():
    raise RuntimeError(
        "QH-30 is forward-only: legacy CHECK cannot represent new types; reviewed restore/forward repair required"
    )
