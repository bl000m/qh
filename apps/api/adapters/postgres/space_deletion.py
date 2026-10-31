"""Scoped erasure transaction; graph errors retain a revoked, resumable Space."""
import asyncio
import hashlib

from psycopg.types.json import Jsonb

from adapters.postgres.canonical import CanonicalRepository
from app.core.models import ContextSpaceNotFound, ContextStorageUnavailable
from app.core.spaces import SpaceConfirmationMismatch


TABLES = ('approved_snapshot_revisions','guest_invitations','approved_snapshots',
    'disclosure_previews','projection_draft_entries','projection_drafts',
    'context_consolidations','context_consolidation_jobs','context_intake','source_documents',
    'projection_outbox','context_projection_state','relation_revision_details',
    'item_revision_types','item_revision_provenance','understanding_item_revisions',
    'understanding_items','source_revisions','sources')


class PostgresSpaceDeletion:
    def __init__(self, *, url):
        self.url = url

    def _run(self, subject, operation):
        repository = CanonicalRepository(url=self.url,subject_id=subject,
            connection_options='-c statement_timeout=15000 -c lock_timeout=5000')
        try:
            with repository.connect() as c:
                if c.execute("SELECT to_regclass('context_space_deletions') AS name").fetchone()['name'] is None:
                    raise ContextStorageUnavailable('Space deletion activation required')
                if not c.execute("SELECT id FROM users WHERE id=%s AND status='active' FOR SHARE",(subject,)).fetchone():
                    raise ContextSpaceNotFound('Context space not found')
                return operation(c)
        except (ContextSpaceNotFound, SpaceConfirmationMismatch):
            raise
        except Exception:
            raise ContextStorageUnavailable('Space deletion unavailable or incomplete') from None

    async def owner_for(self, scope):
        def read():
            repository = CanonicalRepository(url=self.url,subject_id='')
            with repository.connect() as c:
                # Before activation there is no destructive path at all.
                if c.execute("SELECT to_regclass('context_space_deletions') AS name").fetchone()['name'] is None:
                    raise ContextStorageUnavailable('Space deletion activation required')
                row=c.execute('''SELECT s.owner_id FROM context_spaces s JOIN users u ON u.id=s.owner_id
                    WHERE s.id=%s AND u.status='active' AND s.status IN ('active','deleting')
                    UNION SELECT d.owner_id FROM context_space_deletions d JOIN users u ON u.id=d.owner_id
                    WHERE d.context_space_id=%s AND u.status='active' LIMIT 1''',(scope,scope)).fetchone()
                return str(row['owner_id']) if row else None
        try:
            return await asyncio.to_thread(read)
        except ContextStorageUnavailable:
            raise
        except Exception:
            raise ContextStorageUnavailable('Space deletion unavailable') from None

    @staticmethod
    def _lock(c, subject, scope, *, fence=True):
        if fence:
            c.execute("SELECT pg_advisory_xact_lock(hashtextextended('qh-delete:'||%s,0))",(scope,))
        return c.execute('SELECT * FROM context_spaces WHERE id=%s AND owner_id=%s FOR UPDATE',
            (scope,subject)).fetchone()

    async def prepare(self, subject, scope, name):
        def operation(c):
            space=self._lock(c,subject,scope,fence=False)
            digest=hashlib.sha256(name.encode()).hexdigest()
            job=c.execute('SELECT * FROM context_space_deletions WHERE context_space_id=%s AND owner_id=%s',
                (scope,subject)).fetchone()
            if job and job['confirmation_sha256']!=digest or space and space['name']!=name:
                raise SpaceConfirmationMismatch('Exact Space name confirmation required')
            if job and job['state']=='complete':return True
            if space is None or space['status'] not in ('active','deleting'):
                raise ContextSpaceNotFound('Context space not found')
            c.execute("INSERT INTO context_space_deletions VALUES (%s,%s,%s,'deleting',clock_timestamp(),NULL) "
                'ON CONFLICT(context_space_id) DO NOTHING',(scope,subject,digest))
            c.execute("UPDATE context_spaces SET status='deleting',updated_at=clock_timestamp() WHERE id=%s",(scope,))
            c.execute('UPDATE guest_sessions SET revoked_at=coalesce(revoked_at,clock_timestamp()) '
                'WHERE invitation_id IN (SELECT id FROM guest_invitations WHERE context_space_id=%s)',(scope,))
            c.execute('UPDATE guest_invitations SET revoked_at=coalesce(revoked_at,clock_timestamp()) WHERE context_space_id=%s',(scope,))
            return False
        return await asyncio.to_thread(self._run,subject,operation)

    async def complete(self, subject, scope, purge_graph, purge_private):
        return await asyncio.to_thread(self.complete_sync,subject,scope,purge_graph,purge_private)

    def complete_sync(self, subject, scope, purge_graph, purge_private=lambda owner, scope: None):
        def operation(c):
            space=self._lock(c,subject,scope)
            job=c.execute('SELECT state FROM context_space_deletions WHERE context_space_id=%s AND owner_id=%s FOR UPDATE',
                (scope,subject)).fetchone()
            if job and job['state']=='complete':return
            if not job or not space or space['status']!='deleting':
                raise ContextSpaceNotFound('Confirmed deletion required')
            purge_graph(scope)  # Idempotent; never purge SQL before confirmed graph completion.
            purge_private(subject,scope)
            self._purge(c,subject,scope)
            c.execute("UPDATE context_space_deletions SET state='complete',completed_at=clock_timestamp() WHERE context_space_id=%s",(scope,))
        return self._run(subject,operation)

    @staticmethod
    def _purge(c, subject, scope):
        c.execute("SELECT set_config('qh.purge_scope',%s,true),set_config('qh.purge_owner',%s,true)",(scope,subject))
        for table in ('guest_sessions','guest_challenges'):
            c.execute(f'DELETE FROM {table} WHERE invitation_id IN (SELECT id FROM guest_invitations WHERE context_space_id=%s)',(scope,))
        # Clear the cyclic confirmed-head FK without publishing new knowledge.
        c.execute('UPDATE understanding_items SET current_revision_id=NULL WHERE context_space_id=%s',(scope,))
        for table in TABLES:
            c.execute(f'DELETE FROM {table} WHERE context_space_id=%s',(scope,))
        organization=c.execute('SELECT document FROM owner_organization WHERE owner_id=%s FOR UPDATE',(subject,)).fetchone()
        if organization:
            document=organization['document']
            for field in ('memberships','primary_domains','space_descriptions','usage'):
                document.get(field,{}).pop(scope,None)
            c.execute('UPDATE owner_organization SET document=%s,version=version+1 WHERE owner_id=%s',(Jsonb(document),subject))
        c.execute('DELETE FROM context_spaces WHERE id=%s AND owner_id=%s',(scope,subject))
