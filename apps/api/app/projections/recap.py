"""Project the existing version-bound recap without new inference or text assembly."""
from app.core.uum import RECAP_FORMAT, RECAP_PRESENTATION_VERSIONS


def projected_recap(rows, anchors):
    """Share the canonical recap exactly as persisted when its provenance resolves.

    Supports resolve to the exact canonical version, with full-basis presence and at
    least one shared support. No share-time filtering, rewriting or regeneration.
    """
    disclosed = {a['revision_id'] for a in anchors}
    present = {row.revision_id for row in rows}
    candidates = []
    for row in rows:
        extraction = row.content.get('extraction')
        recap = extraction.get('recap') if isinstance(extraction, dict) else None
        if not isinstance(recap, dict):
            continue
        basis, support = recap.get('basis_revision_ids'), recap.get('support_revision_ids')
        if (recap.get('format') == RECAP_FORMAT
                and recap.get('presentation_version') in RECAP_PRESENTATION_VERSIONS
                and _identifiers(basis) and _identifiers(support) and row.revision_id in basis
                and set(support) <= set(basis) <= present and set(support) & disclosed
                and _bounded(recap.get('title'), recap.get('text'))):
            candidates.append(dict(title=recap['title'], text=recap['text']))
    # Do not arbitrarily choose between historical consolidated versions.
    return candidates[0] if len(candidates) == 1 else None


def recap_status(rows, recap):
    if recap:
        return 'available'
    present = any(isinstance(row.content.get('extraction'), dict)
        and isinstance(row.content['extraction'].get('recap'), dict) for row in rows)
    return 'restricted' if present else 'unavailable'


def _identifiers(values):
    return isinstance(values, list) and bool(values) and all(isinstance(v, str) for v in values)


def _bounded(title, text):
    # Same envelope the recipient payload validates; persisted recaps already satisfy it.
    return (isinstance(title, str) and 1 <= len(title.strip()) <= 120
        and isinstance(text, str) and 1 <= len(text.strip()) <= 1500 and len(text.split()) <= 100)
