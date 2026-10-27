"""One current knowledge selection; legacy review flags never grant human truth."""
from adapters.postgres.canonical import json_values


def current_understanding(c, scope):
    versioned = c.execute("SELECT to_regclass('context_consolidations') AS name").fetchone()['name'] is not None
    prefix, restriction, params = '', '', (scope,)
    if versioned:
        prefix = '''WITH latest AS (SELECT revision_ids FROM context_consolidations
            WHERE context_space_id=%s ORDER BY version DESC LIMIT 1),
            historical AS (SELECT unnest(revision_ids) id FROM context_consolidations WHERE context_space_id=%s) '''
        restriction = '''AND (r.id=ANY(COALESCE((SELECT revision_ids FROM latest),'{}'::uuid[]))
            OR NOT EXISTS(SELECT 1 FROM historical h WHERE h.id=r.id))'''
        params = (scope,scope,scope)
    return json_values(c.execute(prefix+'''
        SELECT DISTINCT ON (r.item_id) r.item_id,r.id,r.validation_state,
            d.source_item_id,d.source_revision_id,d.target_item_id,d.target_revision_id
        FROM understanding_item_revisions r JOIN understanding_items i ON i.id=r.item_id
        LEFT JOIN relation_revision_details d ON d.item_revision_id=r.id
        WHERE r.context_space_id=%s AND
          ((r.id=i.current_revision_id AND r.validation_state='confirmed') OR
           (r.validation_state='proposed' AND NOT EXISTS (
             SELECT 1 FROM understanding_item_revisions n WHERE n.item_id=r.item_id
             AND (n.revision_no>r.revision_no OR n.based_on_revision_id=r.id))))
        '''+restriction+''' ORDER BY r.item_id,r.revision_no DESC LIMIT 101''', params).fetchall())
