"""Private immutable originals, separate from understanding and shared payloads."""
from alembic import op

revision = '0011_source_documents'
down_revision = '0010_context_consolidation'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE source_documents (
            source_revision_id uuid PRIMARY KEY,
            context_space_id uuid NOT NULL,
            filename text NOT NULL CHECK(length(filename) BETWEEN 1 AND 256),
            media_type text NOT NULL CHECK(media_type='application/pdf'),
            sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
            original bytea NOT NULL CHECK(octet_length(original) BETWEEN 1 AND 3145728),
            FOREIGN KEY(source_revision_id,context_space_id) REFERENCES source_revisions(id,context_space_id)
        );
        CREATE INDEX ix_source_documents_scope ON source_documents(context_space_id);
        CREATE TRIGGER qh_original_immutable BEFORE UPDATE OR DELETE ON source_documents
            FOR EACH ROW EXECUTE FUNCTION qh_reject_immutable_change();
    """)


def downgrade():
    raise RuntimeError('Retained original documents cannot be discarded')
