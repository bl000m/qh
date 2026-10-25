"""Exact draft scope through native graph verification; no traversal or provider."""
import asyncio
from copy import deepcopy

from adapters.context.incremental import IncrementalContextEngine, immutable_snapshot
from adapters.context.native import NativeContextEngine, checked_rows
from adapters.postgres.canonical import CanonicalRepository, json_values
from app.core.models import RevisionRelation, RevisionTime, SourceRevisionRef
from app.projections.drafts import ProjectedRevision, ProjectionNotFound, ProjectionUnavailable


class NativeDraftResolver:
    def __init__(self, *, repository_for, projector):
        self.repository_for, self.projector = repository_for, projector

    @staticmethod
    def _candidates(repository, scope, keys):
        """Only identity/anchor metadata before private selected-content hydration."""
        with repository.connect() as c:
            repository._authorize(c, (scope,), lock=True)
            rows = json_values(c.execute('''
                SELECT r.id,r.item_id,d.source_item_id,d.source_revision_id,
                    d.target_item_id,d.target_revision_id
                FROM understanding_item_revisions r
                LEFT JOIN relation_revision_details d ON d.item_revision_id=r.id
                WHERE r.context_space_id=%s AND r.id=ANY(%s::uuid[])
            ''', (scope,[k.revision_id for k in keys])).fetchall())
        pairs = {(k.item_id,k.revision_id) for k in keys}
        if {(r['item_id'],r['id']) for r in rows} != pairs:
            raise ProjectionNotFound('Projection not found')
        for row in rows:
            if row['source_revision_id'] is not None:
                for side in ('source','target'):
                    if (row[side+'_item_id'],row[side+'_revision_id']) not in pairs:
                        raise ProjectionNotFound('Projection not found')

    async def resolve(self, subject, scope, keys):
        if not keys or len(keys) > 100:
            raise ProjectionNotFound('Projection not found')
        try:
            repository = self.repository_for(subject)
            if not isinstance(repository, CanonicalRepository) or repository.subject_id != subject:
                raise ProjectionUnavailable('Projection unavailable')
            await asyncio.to_thread(self._candidates, repository, scope, keys)
            engine = IncrementalContextEngine(repository,self.projector)
            before = await asyncio.to_thread(engine._ready, (scope,))
            ids = tuple(k.revision_id for k in keys)
            snapshot = None

            def read(scopes, refs):
                nonlocal snapshot
                if tuple(scopes) != (scope,) or set(refs) != set(ids):
                    raise ProjectionUnavailable('Projection unavailable')
                snapshot = repository.read_snapshot(scopes,refs,source_metadata_only=True)
                return immutable_snapshot(snapshot)

            verifier = NativeContextEngine(self.projector.driver,slice_id=self.projector.key(scope),read_snapshot=read)
            verified = await verifier.select_revisions(context_ids=(scope,),revision_ids=ids,view='history')
            if snapshot is None or {h.item_revision.revision_id for h in verified.hits} != set(ids):
                raise ProjectionUnavailable('Projection unavailable')
            checked_rows(snapshot)
            sources = {s['id']:s for s in snapshot['source_revisions']}
            result = []
            for row in snapshot['understanding_item_revisions']:
                result.append(ProjectedRevision(context_id=scope,item_id=row['item_id'],revision_id=row['id'],
                    revision_no=row['revision_no'],structural_kind=row['structural_kind'],type_id=row['type_id'],
                    type_version=row['type_version'],content=deepcopy(row['content']),origin_kind=row['origin_kind'],
                    validation_state=row['validation_state'],
                    temporal=RevisionTime(**{k:row[k] for k in ('fact_from','fact_to','valid_from','valid_to')}),
                    relation=RevisionRelation(**row['relation']) if row['relation'] else None,
                    provenance=tuple(SourceRevisionRef(source_id=sources[ref]['source_id'],revision_id=ref)
                        for ref in row['provenance'])))
            if await asyncio.to_thread(engine._ready, (scope,)) != before:
                raise ProjectionUnavailable('Projection unavailable')
            return tuple(result)
        except ProjectionNotFound:
            raise
        except PermissionError:
            raise ProjectionNotFound('Projection not found') from None
        except Exception:
            raise ProjectionUnavailable('Projection unavailable') from None
