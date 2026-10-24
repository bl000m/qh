"""Atomic source + whole validated batch using the existing canonical writer."""
import asyncio

import psycopg

from adapters.postgres.canonical import CanonicalRepository
from app.core.models import ContextStorageUnavailable, ContextSpaceNotFound, ContextRetrievalUnavailable
from app.understanding.enrichment import EnrichmentConflict, EXTRACTION_KEY


class PostgresEnrichmentRepository(CanonicalRepository):
    def _find_on(self, c, scope, source_id, fingerprint):
        row = c.execute('SELECT origin FROM source_revisions WHERE id=%s AND context_space_id=%s',
            (source_id, scope)).fetchone()
        if row is None:
            return None
        metadata = row['origin'].get('metadata', {})
        if (metadata.get('submission_kind') not in ('owner_selected_browser_segment', 'owner_current_browser_conversation')
                or metadata.get('submitted_by') != self.subject_id
                or metadata.get('request_sha256') != fingerprint):
            raise EnrichmentConflict('Conflicting immutable submission replay')
        rows = c.execute('''SELECT r.id FROM understanding_item_revisions r
            JOIN item_revision_provenance p ON p.item_revision_id=r.id
            WHERE p.source_revision_id=%s AND r.context_space_id=%s
              AND r.revision_no=1 AND r.origin_kind='ai'
              AND r.content->'extraction'->>'key'=%s ORDER BY r.id''',
            (source_id, scope, metadata.get('extraction_key', EXTRACTION_KEY))).fetchall()
        return dict(context_id=scope, source_revision_id=source_id,
            revision_ids=[str(r['id']) for r in rows], replayed=True, provider_mode=metadata.get('provider_mode', 'offline-literal/1'))

    def _operation(self, scope, source_id, fingerprint, source=None, revisions=()):
        try:
            with self.connect() as c:
                self._authorize(c, (scope,), lock=True)
                if source is not None:
                    c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('qh39:'+source_id,))
                prior = self._find_on(c, scope, source_id, fingerprint)
                if prior is not None or source is None:
                    return prior
                state = c.execute('SELECT desired_version,applied_version FROM context_projection_state WHERE context_space_id=%s FOR UPDATE', (scope,)).fetchone()
                if state is None or state['desired_version'] != state['applied_version']:
                    raise ContextRetrievalUnavailable('Context projection is not ready')
                # Sources and ALL proposed revisions/outbox commit together. Deferred
                # schema/provenance guards reject the whole transaction on failure.
                self._save_on(c, sources=(source,), revisions=revisions)
                c.execute('SET CONSTRAINTS ALL IMMEDIATE')
                return dict(context_id=scope, source_revision_id=source_id,
                    revision_ids=sorted(r['id'] for r in revisions), replayed=False,
                    provider_mode=source['origin']['metadata'].get('provider_mode', 'offline-literal/1'))
        except (psycopg.errors.CheckViolation, psycopg.errors.ForeignKeyViolation, psycopg.errors.UniqueViolation):
            raise EnrichmentConflict('Publication rejected atomically; nothing added') from None
        except PermissionError:
            raise ContextSpaceNotFound('Context space not found') from None
        except psycopg.Error:
            raise ContextStorageUnavailable('Enrichment storage unavailable') from None

    async def find(self, scope, source, fingerprint):
        return await asyncio.to_thread(self._operation, scope, source, fingerprint)

    async def publish(self, scope, source, revisions, fingerprint):
        return await asyncio.to_thread(self._operation, scope, source['id'], fingerprint, source, revisions)
