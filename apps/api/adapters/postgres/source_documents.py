"""Private original metadata, joined to immutable intake naming without a backfill."""
from adapters.postgres.canonical import json_values


def document_metadata(connection, scope, allowed=None):
    restriction=' AND d.source_revision_id=ANY(%s::uuid[])' if allowed is not None else ''
    values=(scope,allowed) if allowed is not None else (scope,)
    rows=connection.execute("""
        SELECT d.source_revision_id,d.filename,d.media_type,
            coalesce(nullif(i.document->>'display_name',''),d.filename) AS display_name,
            octet_length(d.original) AS size_bytes,
            coalesce(i.created_at,r.created_at) AS created_at
        FROM source_documents d JOIN source_revisions r
            ON r.id=d.source_revision_id AND r.context_space_id=d.context_space_id
        LEFT JOIN context_intake i ON i.context_space_id=d.context_space_id
            AND i.document->>'source_revision_id'=d.source_revision_id::text
            AND i.document->>'kind'='document'
        WHERE d.context_space_id=%s"""+restriction+" ORDER BY created_at DESC,d.source_revision_id DESC",values).fetchall()
    return json_values(rows)


def document_source_ids(connection, scope):
    """Immutable source classification, including original rows with older metadata."""
    ids = {str(r['id']) for r in connection.execute("SELECT id FROM source_revisions WHERE context_space_id=%s "
        "AND origin #>> '{metadata,media_type}'='application/pdf'", (scope,)).fetchall()}
    if connection.execute("SELECT to_regclass('source_documents') AS name").fetchone()['name']:
        ids.update(str(r['source_revision_id']) for r in connection.execute(
            'SELECT source_revision_id FROM source_documents WHERE context_space_id=%s', (scope,)).fetchall())
    return tuple(sorted(ids))
