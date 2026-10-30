"""Owner-scoped intake and atomic Source/proposals/outbox/version publication."""
import asyncio
from uuid import UUID, uuid5

import psycopg

from adapters.postgres.canonical import CanonicalRepository, json_values
from app.core.models import ContextSpaceNotFound, ContextStorageUnavailable
from app.understanding.enrichment import EnrichmentConflict, EnrichmentUnavailable
from app.understanding import recap as recap_output
from adapters.postgres.workspace_chat import WorkspaceChatStorage
from adapters.postgres.current_understanding import current_understanding


class PostgresConsolidationRepository(WorkspaceChatStorage, CanonicalRepository):
    def _latest(self, c, scope):
        row = c.execute("""SELECT v.*, EXISTS(SELECT 1 FROM understanding_item_revisions r
            WHERE r.id=ANY(v.revision_ids) AND r.context_space_id=v.context_space_id
            AND r.content #>> '{extraction,recap,version_id}'=v.id::text
            AND r.content #>> '{extraction,recap,presentation_version}'=%s) AS has_recap
            FROM context_consolidations v WHERE context_space_id=%s
            ORDER BY version DESC LIMIT 1""", (str(recap_output.PRESENTATION_VERSION),scope)).fetchone()
        return json_values(row) if row else None

    def _read(self, c, scope):
        latest = self._latest(c, scope)
        rows = c.execute('SELECT id,document,created_at FROM context_intake WHERE context_space_id=%s '
                         "AND document->>'kind' NOT IN ('chat_attempt','regeneration_attempt') ORDER BY created_at,id LIMIT 501", (scope,)).fetchall()
        if len(rows) > 500:
            raise ValueError('Context intake exceeds supported limit')
        consumed = set(latest['intake_ids']) if latest else set()
        pending = [str(r['id']) for r in rows if str(r['id']) not in consumed]
        job = c.execute('SELECT state FROM context_consolidation_jobs WHERE context_space_id=%s', (scope,)).fetchone()
        state = 'running' if job and job['state']=='running' else 'failed' if job and job['state']=='failed' else 'pending' if pending else 'current' if latest else 'empty'
        knowledge = current_understanding(c, scope)
        if len(knowledge)>100:
            raise EnrichmentUnavailable('Current understanding exceeds supported item bound')
        return dict(understanding_ids=[r['id'] for r in knowledge], context_id=scope, current=latest, pending_count=len(pending), state=state,
                    intake=[dict(id=str(r['id']), **r['document'],created_at=r['created_at'].isoformat()) for r in rows],
                    chat_attempts=self._chat_states(c, scope))

    def _append_on(self, c, scope, document):
        from app.understanding.extractor import canonical_json
        old = c.execute('SELECT 1 FROM context_intake WHERE id=%s AND context_space_id=%s',
            (document['id'],scope)).fetchone()
        size = c.execute('SELECT coalesce(sum(octet_length(document::text)),0) n FROM context_intake WHERE context_space_id=%s', (scope,)).fetchone()['n']
        if not old and size+len(canonical_json(document).encode())>800000:
            raise ValueError('Context exceeds supported original intake byte limit')
        self._immutable(c, 'context_intake', dict(id=document['id'], context_space_id=scope,
            document={k:v for k,v in document.items() if k!='id'}))

    def _operation(self, action, scope, document=None, source=None, revisions=()):
        try:
            with self.connect() as c:
                self._authorize(c, (scope,), lock=True)
                c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('qh-context:'+scope,))
                if action=='document':
                    intake, original, data = document
                    old = c.execute('SELECT sha256,filename FROM source_documents WHERE source_revision_id=%s AND context_space_id=%s', (original['id'],scope)).fetchone()
                    if old:
                        saved=c.execute('SELECT document FROM context_intake WHERE id=%s AND context_space_id=%s',(intake['id'],scope)).fetchone()
                        old_name=saved['document'].get('display_name',old['filename']) if saved else old['filename']
                        if old_name!=intake.get('display_name',intake['name']):
                            raise EnrichmentConflict('Document display name changed')
                        if old['sha256']!=original['origin']['metadata']['sha256'] or old['filename']!=intake['name']:
                            raise EnrichmentConflict('Original document changed')
                        return self._read(c, scope)
                    self._save_on(c, sources=(original,))
                    c.execute('INSERT INTO source_documents VALUES (%s,%s,%s,%s,%s,%s)',
                        (original['id'],scope,intake['name'],'application/pdf',original['origin']['metadata']['sha256'],data))
                    self._append_on(c, scope, intake)
                if action=='append':
                    self._append_on(c, scope, document)
                if action=='claim':
                    state = self._read(c, scope)
                    regeneration = document and document.get('regeneration')
                    if regeneration:
                        operation = str(uuid5(UUID(scope), 'regenerate:'+regeneration))
                        if c.execute('SELECT 1 FROM context_consolidations WHERE id=%s AND context_space_id=%s', (operation,scope)).fetchone():
                            return dict(replayed=True, **state)
                        if c.execute('SELECT 1 FROM context_intake WHERE id=%s AND context_space_id=%s',
                                (str(uuid5(UUID(operation), 'regeneration-failed')),scope)).fetchone():
                            raise EnrichmentConflict('Regeneration failed; a new explicit operation is required')
                        if not state['current']:
                            raise ValueError('No memorized source to regenerate')
                    if state['state']=='running':
                        # Never expire a running paid operation silently. A process crash
                        # needs an operator to establish that no request remains in flight.
                        raise EnrichmentUnavailable('Consolidation already in progress')
                    if not regeneration and not state['pending_count'] and (not state['current'] or state['current']['has_recap']):
                        return dict(replayed=True, **state)
                    ids = [row['id'] for row in state['intake']]
                    if regeneration:
                        ids = state['current']['intake_ids']
                        state['intake'] = [r for r in state['intake'] if r['id'] in ids]
                    else:
                        operation = str(uuid5(UUID(scope), f'consolidation:recap-v{recap_output.PRESENTATION_VERSION}:'+':'.join(ids)))
                    if regeneration:
                        self._immutable(c, 'context_intake', dict(id=operation, context_space_id=scope,
                            document=dict(kind='regeneration_attempt')))
                    c.execute("""INSERT INTO context_consolidation_jobs(context_space_id,operation_id,state)
                        VALUES (%s,%s,'running') ON CONFLICT(context_space_id) DO UPDATE
                        SET operation_id=EXCLUDED.operation_id,state='running',started_at=clock_timestamp()""", (scope,operation))
                    return dict(operation_id=operation, regenerating=bool(regeneration), **state)
                if action=='fail':
                    changed = c.execute("UPDATE context_consolidation_jobs SET state='failed' WHERE context_space_id=%s AND operation_id=%s AND state='running'", (scope,document['operation_id'])).rowcount
                    operation = document['operation_id']
                    if changed and c.execute("SELECT 1 FROM context_intake WHERE id=%s AND context_space_id=%s AND document->>'kind'='regeneration_attempt'", (operation,scope)).fetchone():
                        self._immutable(c, 'context_intake', dict(id=str(uuid5(UUID(operation),'regeneration-failed')),
                            context_space_id=scope,document=dict(kind='regeneration_attempt')))
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
                    self._save_on(c, sources=() if latest and source['id']==latest['source_revision_id'] else (source,), revisions=revisions)
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

    async def claim(self, scope, regeneration=None):
        return await asyncio.to_thread(self._operation, 'claim', scope, dict(regeneration=regeneration))

    async def original(self, scope, revision):
        return (await asyncio.to_thread(self.read_sources, (scope,), (revision,)))[0]

    async def fail(self, scope, operation):
        return await asyncio.to_thread(self._operation, 'fail', scope, dict(operation_id=operation))

    async def publish(self, scope, operation, intake_ids, source, revisions):
        return await asyncio.to_thread(self._operation, 'publish', scope,
            dict(operation_id=operation, intake_ids=intake_ids), source, revisions)

    async def import_document(self, scope, document, source, data):
        return await asyncio.to_thread(self._operation, 'document', scope, (document,source,data))

    async def document(self, scope, revision):
        def read():
            with self.connect() as c:
                self._authorize(c, (scope,), lock=True)
                row=c.execute('SELECT filename,media_type,original FROM source_documents WHERE context_space_id=%s AND source_revision_id=%s', (scope,revision)).fetchone()
                if row is None:
                    raise ContextSpaceNotFound('Source not found')
                return row
        try:
            return await asyncio.to_thread(read)
        except PermissionError:
            raise ContextSpaceNotFound('Source not found') from None

    async def documents(self, scope):
        def read():
            with self.connect() as c:
                self._authorize(c, (scope,), lock=True)
                from adapters.postgres.source_documents import document_metadata
                return document_metadata(c,scope)
        try:
            return await asyncio.to_thread(read)
        except PermissionError:
            raise ContextSpaceNotFound('Source not found') from None
