"""Immutable owner review through the canonical publisher and existing outbox."""
import asyncio
from copy import deepcopy
from uuid import NAMESPACE_URL, uuid5

import psycopg

from adapters.postgres.canonical import CanonicalRepository, TEMPORAL, json_values
from app.core.models import ContextSpaceNotFound, ContextStorageUnavailable, ContextRetrievalUnavailable
from app.review.service import ReviewConflict


class PostgresReviewRepository:
    def __init__(self, *, url):
        self.url = url

    def _run(self, subject, scope, revision=None, operation=None, *, limit=20, after=None):
        repo = CanonicalRepository(url=self.url, subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')
        try:
            with repo.connect() as c:
                repo._authorize(c, (scope,), lock=True)
                if revision is None:
                    rows = c.execute('''SELECT r.id FROM understanding_item_revisions r
                        WHERE r.context_space_id=%s AND r.validation_state='proposed'
                        AND NOT EXISTS(SELECT 1 FROM understanding_item_revisions child
                            WHERE child.based_on_revision_id=r.id)
                        AND NOT EXISTS(SELECT 1 FROM understanding_item_revisions newer
                            WHERE newer.item_id=r.item_id AND newer.revision_no>r.revision_no)
                        AND (%s::uuid IS NULL OR r.id>%s::uuid) ORDER BY r.id LIMIT %s''',
                        (scope, after, after, limit)).fetchall()
                    return [str(row['id']) for row in rows]
                target = c.execute('SELECT * FROM understanding_item_revisions WHERE id=%s AND context_space_id=%s', (revision, scope)).fetchone()
                if target is None:
                    raise ContextSpaceNotFound('Revision not found')
                item = c.execute('SELECT * FROM understanding_items WHERE id=%s FOR UPDATE', (target['item_id'],)).fetchone()
                latest = c.execute('SELECT id,revision_no FROM understanding_item_revisions WHERE item_id=%s ORDER BY revision_no DESC LIMIT 1', (target['item_id'],)).fetchone()
                child = c.execute('SELECT id FROM understanding_item_revisions WHERE based_on_revision_id=%s ORDER BY revision_no LIMIT 1', (revision,)).fetchone()
                status = dict(revision_id=revision, latest_revision_id=str(latest['id']),
                    current_revision_id=str(item['current_revision_id']) if item['current_revision_id'] else None,
                    pending=target['validation_state']=='proposed' and child is None and str(latest['id'])==revision,
                    successor_revision_id=str(child['id']) if child else None)
                if operation is None:
                    return status
                action = operation['action']
                new_id = str(uuid5(NAMESPACE_URL, 'qh.review/'+str(subject)+'/'+scope+'/'+operation['operation_id']))
                receipt = dict(operation, actor_id=str(subject), target_revision_id=revision, version=1)
                content = deepcopy(target['content'])
                content['qh_review'] = receipt
                if action == 'correct':
                    content['text'] = operation['text']
                if action == 'review_assignments':
                    from app.core.assignments import review_assignments
                    binding = c.execute('SELECT * FROM item_revision_types WHERE item_revision_id=%s', (revision,)).fetchone()
                    if binding['type_version'] != 2 or binding['type_id'] not in ('qh.generic.item', 'qh.generic.entity', 'qh.generic.relation'):
                        raise ValueError('Qualified semantic profile required')
                    content['descriptors'] = review_assignments(content.get('descriptors'), operation['assignment_decisions'], len(content.get('citations', [])))
                existing = c.execute('SELECT * FROM understanding_item_revisions WHERE id=%s', (new_id,)).fetchone()
                if existing:
                    if existing['content'] != content or str(existing['based_on_revision_id']) != revision or str(existing['context_space_id']) != scope:
                        raise ReviewConflict('Conflicting operation replay')
                    return dict(revision_id=new_id, action=action, replayed=True)
                if str(latest['id']) != operation['expected_latest_revision_id'] or status['current_revision_id'] != operation['expected_current_revision_id']:
                    raise ReviewConflict('Review changed; reload before acting')
                if action in ('confirm', 'reject') and (not status['pending'] or str(latest['id']) != revision):
                    raise ReviewConflict('Only the pending latest proposal can be reviewed')
                if action in ('correct', 'review_assignments') and not ((status['pending'] and str(latest['id']) == revision) or status['current_revision_id'] == revision):
                    raise ReviewConflict('Only current understanding or a pending latest proposal can be corrected')
                state = c.execute('SELECT desired_version,applied_version FROM context_projection_state WHERE context_space_id=%s FOR UPDATE', (scope,)).fetchone()
                if state is None or state['desired_version'] != state['applied_version']:
                    raise ContextRetrievalUnavailable('Context projection is not ready')
                if action == 'review_assignments':
                    for decision in operation['assignment_decisions']:
                        name = decision.get('reuse_value')
                        if name is not None and not c.execute('''SELECT 1 FROM understanding_item_revisions r
                            JOIN understanding_items i ON i.id=r.item_id
                            WHERE r.context_space_id=%s AND (r.id=i.current_revision_id OR
                              (r.validation_state='proposed' AND NOT EXISTS (SELECT 1 FROM understanding_item_revisions n WHERE n.item_id=r.item_id AND n.revision_no>r.revision_no)))
                            AND EXISTS (SELECT 1 FROM jsonb_array_elements(CASE WHEN jsonb_typeof(r.content->'descriptors')='array' THEN r.content->'descriptors' ELSE '[]'::jsonb END) d
                              WHERE d->>'dimension'='thematic' AND d->>'value'=%s AND d->>'review_state' IN ('proposed','accepted') AND NOT d ? 'name_candidate') LIMIT 1''', (scope,name)).fetchone():
                            raise ReviewConflict('Theme reuse scope changed')
                binding = c.execute('SELECT * FROM item_revision_types WHERE item_revision_id=%s', (revision,)).fetchone()
                relation = c.execute('SELECT * FROM relation_revision_details WHERE item_revision_id=%s', (revision,)).fetchone()
                sources = c.execute('SELECT source_revision_id FROM item_revision_provenance WHERE item_revision_id=%s ORDER BY source_revision_id', (revision,)).fetchall()
                now = c.execute('SELECT clock_timestamp() AS value').fetchone()['value']
                record = dict(id=new_id, item_id=str(target['item_id']), context_space_id=scope,
                    revision_no=latest['revision_no']+1, type_id=binding['type_id'], type_version=binding['type_version'],
                    content=content, origin_kind='human' if action=='correct' else target['origin_kind'],
                    validation_state={'confirm':'confirmed','reject':'rejected','correct':'proposed','review_assignments':'proposed'}[action],
                    validated_by=None if action in ('correct','review_assignments') else str(subject), validated_at=None if action in ('correct','review_assignments') else now,
                    based_on_revision_id=revision, created_at=now,
                    provenance=[str(s['source_revision_id']) for s in sources], **{k:binding[k] for k in TEMPORAL})
                if relation:
                    record['relation'] = {k: relation[k] for k in ('source_item_id','source_revision_id','target_item_id','target_revision_id','predicate')}
                repo._save_on(c, revisions=(record,))
                if action == 'confirm':
                    c.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s', (new_id, target['item_id']))
                # Force deferred profile/provenance guards before returning a receipt.
                c.execute('SET CONSTRAINTS ALL IMMEDIATE')
                return json_values(dict(revision_id=new_id, action=action, replayed=False))
        except (psycopg.errors.CheckViolation, psycopg.errors.UniqueViolation, psycopg.errors.ForeignKeyViolation):
            raise ReviewConflict('Revision/profile constraints rejected the review; nothing published') from None
        except psycopg.Error:
            raise ContextStorageUnavailable('Review unavailable') from None

    async def pending(self, subject, scope, limit, after):
        return await asyncio.to_thread(self._run, subject, scope, limit=limit, after=after)

    async def status(self, subject, scope, revision):
        return await asyncio.to_thread(self._run, subject, scope, revision)

    async def apply(self, subject, scope, revision, operation):
        return await asyncio.to_thread(self._run, subject, scope, revision, operation)
