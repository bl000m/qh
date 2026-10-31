"""Owner-bound previews and immutable snapshots; no guest route or provider call."""
import asyncio
import json
from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from adapters.context.incremental import IncrementalContextEngine
from adapters.postgres.canonical import CanonicalRepository, json_values
from adapters.postgres.current_understanding import current_understanding
from app.projections.disclosure import (
    AccessPolicy, ApprovedSnapshot, Candidate, DisclosurePreview, Selection, digest, validate_preview,
)
from app.projections.document_scope import is_empty_projection
from app.projections.drafts import ProjectionConflict, ProjectionNotFound, ProjectionUnavailable, RevisionKey, identifier


class PostgresDisclosureRepository:
    def __init__(self, *, url, projector):
        self.url, self.projector = url, projector

    def _canonical(self, subject):
        identifier(subject)
        return CanonicalRepository(url=self.url, subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')

    def _selection(self, repository, c, scope):
        repository._authorize(c, (scope,), lock=True)
        # Canonical publication advances this row in its transaction. Hold it through
        # receipt/snapshot INSERT so a concurrent publication cannot invalidate consent.
        state = c.execute('SELECT epoch,desired_version,applied_version FROM context_projection_state '
            'WHERE context_space_id=%s FOR SHARE', (scope,)).fetchone()
        if state is None or state['desired_version'] != state['applied_version']:
            raise ProjectionUnavailable('Disclosure unavailable')
        IncrementalContextEngine(repository, self.projector)._ready((scope,))
        rows = current_understanding(c, scope)
        if len(rows) > 100:
            raise ProjectionUnavailable('Space exceeds the 100-revision disclosure bound; no partial snapshot')
        candidates = tuple(Candidate(key=RevisionKey(item_id=r['item_id'], revision_id=r['id']),
            state=r['validation_state'], endpoints=tuple(RevisionKey(item_id=r[side+'_item_id'],
                revision_id=r[side+'_revision_id']) for side in ('source', 'target'))
                if r['source_revision_id'] is not None else ()) for r in rows)
        name = c.execute('SELECT name FROM context_spaces WHERE id=%s', (scope,)).fetchone()['name']
        from adapters.postgres.source_documents import document_source_ids
        documents = document_source_ids(c, scope)
        stamp = dict(state=json_values(state), rows=rows, name=name)
        if documents:
            stamp['document_sources'] = documents
        return Selection(context_id=scope, stamp=digest(stamp), candidates=candidates, name=name, document_sources=documents)

    def _with_owner(self, subject, scope, operation):
        identifier(scope)
        repository = self._canonical(subject)
        try:
            with repository.connect() as c:
                repository._authorize(c, (scope,), lock=True)
                return operation(repository, c)
        except (ProjectionConflict, ProjectionNotFound, ProjectionUnavailable):
            raise
        except PermissionError:
            raise ProjectionNotFound('Projection not found') from None
        except psycopg.Error:
            raise ProjectionUnavailable('Disclosure unavailable') from None
        except Exception:
            raise ProjectionUnavailable('Disclosure unavailable') from None

    async def select(self, subject, scope):
        return await asyncio.to_thread(self._with_owner, subject, scope,
            lambda r, c: self._selection(r, c, scope))

    def _pin(self, repository, c, preview):
        validate_preview(preview, repository.subject_id, preview.context_id)
        if self._selection(repository, c, preview.context_id).stamp != preview.selection_stamp:
            raise ProjectionConflict('Context changed; prepare a new preview')
        valid = c.execute('SELECT %s::timestamptz>clock_timestamp() AND '
            '%s::timestamptz>clock_timestamp()-interval \'15 minutes\' AS valid',
            (preview.policy.expires_at, preview.created_at)).fetchone()['valid']
        if not valid:
            raise ProjectionConflict('Disclosure expired; prepare a new preview')
        if preview.draft_id is not None:
            draft = c.execute('SELECT * FROM projection_drafts WHERE id=%s AND context_space_id=%s FOR SHARE',
                (preview.draft_id, preview.context_id)).fetchone()
            if (draft is None or draft['version'] != 1 or draft['expires_at'] != preview.policy.expires_at
                    or draft['recipient'] != preview.policy.recipient_email or draft['purpose'] != preview.policy.purpose):
                raise ProjectionConflict('Projection changed')

    @staticmethod
    def _preview(row, owner):
        return DisclosurePreview(id=str(row['id']), context_id=str(row['context_space_id']), owner_id=owner,
            draft_id=str(row['draft_id']) if row['draft_id'] else None, policy=AccessPolicy.from_wire(row['policy']),
            selection_stamp=row['selection_stamp'], payload_json=json.dumps(row['payload'], sort_keys=True, ensure_ascii=False),
            report_json=json.dumps(row['report'], sort_keys=True, ensure_ascii=False),
            fingerprint=row['fingerprint'], created_at=row['created_at'])

    async def prepare(self, preview):
        def insert(repository, c):
            self._pin(repository, c, preview)
            row = c.execute('INSERT INTO disclosure_previews '
                '(id,context_space_id,draft_id,policy,selection_stamp,payload,report,fingerprint,created_at) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                (preview.id, preview.context_id, preview.draft_id, Jsonb(preview.policy.wire()), preview.selection_stamp,
                 Jsonb(preview.payload), Jsonb(preview.report), preview.fingerprint, preview.created_at)).fetchone()
            return self._preview(row, preview.owner_id)
        return await asyncio.to_thread(self._with_owner, preview.owner_id, preview.context_id, insert)

    async def preview(self, subject, scope, preview_id):
        identifier(preview_id)
        def read(repository, c):
            row = c.execute('SELECT * FROM disclosure_previews WHERE id=%s AND context_space_id=%s',
                (preview_id, scope)).fetchone()
            if row is None:
                raise ProjectionNotFound('Projection not found')
            return self._preview(row, subject)
        return await asyncio.to_thread(self._with_owner, subject, scope, read)

    @staticmethod
    def _snapshot(row):
        return ApprovedSnapshot(id=str(row['id']), context_id=str(row['context_space_id']),
            owner_id=str(row['approved_by']), preview_id=str(row['preview_id']), fingerprint=row['fingerprint'],
            payload_json=json.dumps(row['payload'], sort_keys=True, ensure_ascii=False),
            policy=AccessPolicy.from_wire(row['policy']), approved_at=row['approved_at'],
            exceptions=tuple(row['accepted_exceptions']))

    async def approve(self, preview, exceptions):
        def insert(repository, c):
            self._pin(repository, c, preview)
            # Trust only the persisted exact receipt, never a client-supplied payload.
            stored = c.execute('SELECT * FROM disclosure_previews WHERE id=%s AND context_space_id=%s',
                (preview.id, preview.context_id)).fetchone()
            if stored is None or self._preview(stored, preview.owner_id) != preview:
                raise ProjectionConflict('Disclosure changed')
            if ((not is_empty_projection(preview.payload) and (not preview.payload['items'] or preview.draft_id is None))
                or tuple(sorted(set(exceptions))) != tuple(sorted(preview.report['risks']))):
                raise ProjectionConflict('Explicit disclosure decision required')
            # A unique preview makes an explicit approval replay idempotent.
            c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', (preview.id,))
            row = c.execute('SELECT * FROM approved_snapshots WHERE preview_id=%s', (preview.id,)).fetchone()
            if row is not None:
                if tuple(row['accepted_exceptions']) != exceptions:
                    raise ProjectionConflict('Disclosure changed')
                return self._snapshot(row)
            row = c.execute('INSERT INTO approved_snapshots '
                '(id,context_space_id,preview_id,fingerprint,policy,payload,accepted_exceptions,approved_by) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                (str(uuid4()), preview.context_id, preview.id, preview.fingerprint,
                 Jsonb(preview.policy.wire()), Jsonb(preview.payload), Jsonb(list(exceptions)), preview.owner_id)).fetchone()
            for anchor in preview.report['anchors']:
                c.execute('INSERT INTO approved_snapshot_revisions VALUES (%s,%s,%s,%s,%s)',
                    (row['id'], preview.context_id, anchor['reference'], anchor['item_id'], anchor['revision_id']))
            return self._snapshot(row)
        return await asyncio.to_thread(self._with_owner, preview.owner_id, preview.context_id, insert)

    async def snapshot(self, subject, scope, snapshot_id):
        identifier(snapshot_id)
        def read(repository, c):
            row = c.execute('SELECT * FROM approved_snapshots WHERE id=%s AND context_space_id=%s',
                (snapshot_id, scope)).fetchone()
            if row is None:
                raise ProjectionNotFound('Projection not found')
            return self._snapshot(row)
        return await asyncio.to_thread(self._with_owner, subject, scope, read)
