"""Canonical draft CRUD. Owner predicates and atomic CAS fence stale policy reads."""
import asyncio
from uuid import uuid4

import psycopg

from adapters.postgres.canonical import CanonicalRepository
from app.projections.drafts import (
    DraftSpec, ProjectionConflict, ProjectionDraft, ProjectionNotFound,
    ProjectionUnavailable, RevisionKey,
)


class PostgresDraftRepository:
    def __init__(self, *, url):
        self.url = url

    def _run(self, subject, scope, draft_id=None, version=None, spec=None):
        repository = CanonicalRepository(url=self.url, subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')
        try:
            with repository.connect() as c:
                repository._authorize(c, (scope,), lock=True)
                owner = c.execute('SELECT owner_id FROM context_spaces WHERE id=%s', (scope,)).fetchone()['owner_id']
                row = None
                if draft_id is not None:
                    row = c.execute('SELECT * FROM projection_drafts WHERE id=%s AND context_space_id=%s FOR UPDATE',
                        (draft_id, scope)).fetchone()
                    if row is None:
                        raise ProjectionNotFound('Projection not found')
                    if version is not None and row['version'] != version:
                        raise ProjectionConflict('Projection changed')
                if spec is not None:
                    pairs = set(spec.included + spec.excluded)
                    refs = [p.revision_id for p in pairs]
                    actual = c.execute('SELECT id,item_id FROM understanding_item_revisions '
                        'WHERE context_space_id=%s AND id=ANY(%s::uuid[])', (scope, refs)).fetchall()
                    if {(str(r['item_id']),str(r['id'])) for r in actual} != {(p.item_id,p.revision_id) for p in pairs}:
                        raise ProjectionNotFound('Projection not found')
                    values = (spec.recipient_kind, spec.recipient, spec.purpose, spec.expires_at)
                    if row is None:
                        draft_id = str(uuid4())
                        row = c.execute('INSERT INTO projection_drafts '
                            '(id,context_space_id,recipient_kind,recipient,purpose,expires_at,version) '
                            'VALUES (%s,%s,%s,%s,%s,%s,1) RETURNING *', (draft_id, scope, *values)).fetchone()
                    else:
                        row = c.execute('UPDATE projection_drafts SET recipient_kind=%s,recipient=%s,purpose=%s,'
                            'expires_at=%s,version=version+1,updated_at=clock_timestamp() '
                            'WHERE id=%s AND context_space_id=%s AND version=%s RETURNING *',
                            (*values,draft_id,scope,version)).fetchone()
                        if row is None:
                            raise ProjectionConflict('Projection changed')
                        c.execute('DELETE FROM projection_draft_entries WHERE draft_id=%s', (draft_id,))
                    for effect, entries in (('include',spec.included), ('exclude',spec.excluded)):
                        for entry in entries:
                            c.execute('INSERT INTO projection_draft_entries VALUES (%s,%s,%s,%s,%s)',
                                (draft_id,scope,effect,entry.item_id,entry.revision_id))
                entries = c.execute('SELECT effect,item_id,revision_id FROM projection_draft_entries '
                    'WHERE draft_id=%s ORDER BY item_id,revision_id', (draft_id,)).fetchall()
                def selected(effect):
                    return tuple(RevisionKey(item_id=str(r['item_id']),revision_id=str(r['revision_id']))
                        for r in entries if r['effect'] == effect)
                return ProjectionDraft(id=str(row['id']),context_id=scope,owner_id=str(owner),
                    version=row['version'],state=row['state'],created_at=row['created_at'],updated_at=row['updated_at'],
                    spec=DraftSpec(recipient_kind=row['recipient_kind'],recipient=row['recipient'],purpose=row['purpose'],
                        included=selected('include'),excluded=selected('exclude'),expires_at=row['expires_at']))
        except PermissionError:
            raise ProjectionNotFound('Projection not found') from None
        except psycopg.IntegrityError:
            raise ProjectionNotFound('Projection not found') from None
        except psycopg.Error:
            raise ProjectionUnavailable('Projection unavailable') from None

    async def create(self, subject, scope, spec):
        return await asyncio.to_thread(self._run, subject, scope, spec=spec)

    async def read(self, subject, scope, draft_id):
        return await asyncio.to_thread(self._run, subject, scope, draft_id)

    async def replace(self, subject, scope, draft_id, version, spec):
        return await asyncio.to_thread(self._run, subject, scope, draft_id, version, spec)
