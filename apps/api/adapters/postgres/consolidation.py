"""Owner-scoped intake and atomic Source/proposals/outbox/version publication."""
import asyncio
from uuid import UUID, uuid5

import psycopg

from adapters.postgres.canonical import CanonicalRepository, json_values
from app.core.models import ContextSpaceNotFound, ContextStorageUnavailable
from app.understanding.enrichment import EnrichmentConflict, EnrichmentUnavailable


class PostgresConsolidationRepository(CanonicalRepository):
    def _latest(self, c, scope):
        row = c.execute("""SELECT v.*, EXISTS(SELECT 1 FROM understanding_item_revisions r
            WHERE r.id=ANY(v.revision_ids) AND r.context_space_id=v.context_space_id
            AND r.content #>> '{extraction,recap,version_id}'=v.id::text) AS has_recap
            FROM context_consolidations v WHERE context_space_id=%s
            ORDER BY version DESC LIMIT 1""", (scope,)).fetchone()
        return json_values(row) if row else None

    def _read(self, c, scope):
        latest = self._latest(c, scope)
        rows = c.execute('SELECT id,document FROM context_intake WHERE context_space_id=%s '
                         'ORDER BY created_at,id LIMIT 501', (scope,)).fetchall()
        if len(rows) > 500:
            raise ValueError('Context intake exceeds supported limit')
        consumed = set(latest['intake_ids']) if latest else set()
        pending = [str(r['id']) for r in rows if str(r['id']) not in consumed]
        job = c.execute('SELECT state FROM context_consolidation_jobs WHERE context_space_id=%s', (scope,)).fetchone()
        state = 'running' if job and job['state']=='running' else 'failed' if job and job['state']=='failed' else 'pending' if pending else 'current' if latest else 'empty'
        return dict(context_id=scope, current=latest, pending_count=len(pending), state=state,
                    intake=[dict(id=str(r['id']), **r['document']) for r in rows])

    def _operation(self, action, scope, document=None, source=None, revisions=()):
        try:
            with self.connect() as c:
                self._authorize(c, (scope,), lock=True)
                c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('qh-context:'+scope,))
                if action=='append':
                    from app.understanding.extractor import canonical_json
                    old=c.execute('SELECT 1 FROM context_intake WHERE id=%s AND context_space_id=%s',
                                  (document['id'],scope)).fetchone()
                    size=c.execute('SELECT coalesce(sum(octet_length(document::text)),0) n FROM context_intake WHERE context_space_id=%s', (scope,)).fetchone()['n']
                    if not old and size+len(canonical_json(document).encode())>800000:
                        raise ValueError('Context exceeds supported original intake byte limit')
                    self._immutable(c, 'context_intake', dict(id=document['id'],
                        context_space_id=scope, document={k:v for k,v in document.items() if k!='id'}))
                if action=='claim':
                    state = self._read(c, scope)
                    if state['state']=='running':
                        # Never expire a running paid operation silently. A process crash
                        # needs an operator to establish that no request remains in flight.
                        raise EnrichmentUnavailable('Consolidation already in progress')
                    if not state['pending_count'] and (not state['current'] or state['current']['has_recap']):
                        return dict(replayed=True, **state)
                    ids = [row['id'] for row in state['intake']]
                    operation = str(uuid5(UUID(scope), 'consolidation:recap-v1:'+':'.join(ids)))
                    c.execute("""INSERT INTO context_consolidation_jobs(context_space_id,operation_id,state)
                        VALUES (%s,%s,'running') ON CONFLICT(context_space_id) DO UPDATE
                        SET operation_id=EXCLUDED.operation_id,state='running',started_at=clock_timestamp()""", (scope,operation))
                    return dict(operation_id=operation, **state)
                if action=='fail':
                    c.execute("UPDATE context_consolidation_jobs SET state='failed' WHERE context_space_id=%s AND operation_id=%s AND state='running'", (scope,document['operation_id']))
                if action=='publish':
                    job = c.execute('SELECT * FROM context_consolidation_jobs WHERE context_space_id=%s FOR UPDATE', (scope,)).fetchone()
                    existing = c.execute('SELECT 1 FROM context_consolidations WHERE id=%s AND context_space_id=%s', (document['operation_id'],scope)).fetchone()
                    if existing:
                        return self._read(c, scope)
                    if not job or str(job['operation_id'])!=document['operation_id'] or job['state']!='running':
                        raise EnrichmentConflict('Consolidation operation changed')
                    state = c.execute('SELECT desired_version,applied_version FROM context_projection_state WHERE context_space_id=%s FOR UPDATE', (scope,)).fetchone()
                    if not state or state['desired_version']!=state['applied_version']:
                        raise EnrichmentUnavailable('Context projection not ready')
                    latest = self._latest(c, scope)
                    self._save_on(c, sources=(source,), revisions=revisions)
                    c.execute("""INSERT INTO context_consolidations(id,context_space_id,version,intake_ids,source_revision_id,revision_ids)
                        VALUES (%s,%s,%s,%s::uuid[],%s,%s::uuid[])""",
                        (document['operation_id'],scope,(latest['version'] if latest else 0)+1,
                         document['intake_ids'],source['id'],[r['id'] for r in revisions]))
                    c.execute("UPDATE context_consolidation_jobs SET state='idle' WHERE context_space_id=%s", (scope,))
                    c.execute('SET CONSTRAINTS ALL IMMEDIATE')
                return self._read(c, scope)
        except PermissionError:
            raise ContextSpaceNotFound('Context space not found') from None
        except psycopg.Error:
            raise ContextStorageUnavailable('Context consolidation storage unavailable') from None

    async def read(self, scope):
        return await asyncio.to_thread(self._operation, 'read', scope)

    async def append(self, scope, document):
        return await asyncio.to_thread(self._operation, 'append', scope, document)

    async def claim(self, scope):
        return await asyncio.to_thread(self._operation, 'claim', scope)

    async def fail(self, scope, operation):
        return await asyncio.to_thread(self._operation, 'fail', scope, dict(operation_id=operation))

    async def publish(self, scope, operation, intake_ids, source, revisions):
        return await asyncio.to_thread(self._operation, 'publish', scope,
            dict(operation_id=operation, intake_ids=intake_ids), source, revisions)
