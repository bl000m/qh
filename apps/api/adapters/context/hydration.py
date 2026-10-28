"""Translate verified repository snapshots into provider-neutral canonical values."""

from app.core.models import CanonicalRevision, CanonicalSource, RevisionRelation, RevisionTime
from adapters.context.native import NativeContextError, checked_rows


def hydrate(repository, query, revision_ids, *, snapshot=None):
    if snapshot is None:
        snapshot = repository.read_snapshot(query.context_ids, revision_ids)
    checked_rows(snapshot)
    rows = snapshot['understanding_item_revisions']
    if {r['id'] for r in rows} != set(revision_ids):
        raise NativeContextError('Missing canonical revision')
    refs = {r['current_revision_id'] for r in rows if r['current_revision_id']}
    for row in rows:
        if row['relation'] is not None:
            refs.update(row['relation'][side + '_revision_id'] for side in ('source', 'target'))
    anchors = repository.read_snapshot(query.context_ids, sorted(refs)) if refs else None
    indexed = {r['id']: r for r in anchors['understanding_item_revisions']} if anchors else {}
    sources = {s['id']: s for s in snapshot['source_revisions']}
    result = []
    for row in rows:
        scope, detail = row['context_space_id'], row['relation']
        if scope not in query.context_ids:
            raise NativeContextError('Foreign canonical revision')
        if (row['structural_kind'] == 'relation') != (detail is not None):
            raise NativeContextError('Relation detail disagrees with structural kind')
        current = row['current_revision_id']
        if current:
            head = indexed.get(current)
            if not head or head['item_id'] != row['item_id'] or head['context_space_id'] != scope or head['validation_state'] != 'confirmed':
                raise NativeContextError('Invalid confirmed-current pointer')
        if (query.view == 'current' and (current != row['id'] or row['validation_state'] != 'confirmed')
                or query.view == 'proposed' and row['validation_state'] != 'proposed'):
            raise NativeContextError('Candidate view disagrees with canonical state')
        if detail is not None:
            if not detail['predicate'].strip():
                raise NativeContextError('Empty canonical relation predicate')
            for side in ('source', 'target'):
                endpoint = indexed.get(detail[side + '_revision_id'])
                if not endpoint or endpoint['item_id'] != detail[side + '_item_id'] or endpoint['context_space_id'] != scope:
                    raise NativeContextError('Missing or foreign canonical relation endpoint')
        # QH-8 emits this receipt together with its reserved locator payload.
        # Historical registered schemas can use a property named "citations"
        # for other JSON values; do not impose the extractor envelope on them.
        receipt = row['content'].get('extraction')
        qh8_locators = isinstance(receipt, dict) and {'key', 'input_sha256'} <= receipt.keys()
        citations = row['content'].get('citations') if qh8_locators else []
        if not isinstance(citations, list) or qh8_locators and not citations:
            raise NativeContextError('Missing canonical QH-8 citations')
        for citation in citations:
            source = sources.get(citation['source_revision_id'])
            start, end = citation['start'], citation['end']
            if (citation['source_revision_id'] not in row['provenance'] or source is None
                    or type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(source['content'])
                    or source['content'][start:end] != citation['quote']):
                raise NativeContextError('Invalid canonical citation')
        result.append(CanonicalRevision(
            context_space_id=scope, item_id=row['item_id'], revision_id=row['id'],
            revision_no=row['revision_no'], structural_kind=row['structural_kind'],
            type_id=row['type_id'], type_version=row['type_version'], content=row['content'],
            origin_kind=row['origin_kind'], validation_state=row['validation_state'],
            validated_by=row['validated_by'], validated_at=row['validated_at'],
            current_revision_id=current, is_current_confirmed=current == row['id'] and row['validation_state'] == 'confirmed',
            based_on_revision_id=row['based_on_revision_id'], created_at=row['created_at'],
            temporal=RevisionTime(**{k: row[k] for k in ('fact_from','fact_to','valid_from','valid_to')}),
            relation=RevisionRelation(**detail) if detail is not None else None,
            provenance=tuple(CanonicalSource(source_id=sources[ref]['source_id'],
                            source_revision_id=ref, revision_no=sources[ref]['revision_no'],
                            origin=sources[ref]['origin']) for ref in row['provenance']),
        ))
    return tuple(result)
