"""Project the existing version-bound recap without new inference or text assembly."""
from app.core.uum import RECAP_FORMAT, RECAP_PRESENTATION_VERSIONS


def projected_recap(rows, anchors, redact, high_risk):
    """Disclose the canonical recap when its own text is safe and a support is disclosed.

    Supports resolve to the exact canonical version. Excluded supports stay excluded
    (neither text nor identifiers leave the perimeter) without hiding the recap; the
    recap is withheld only when no support is disclosed or its own text is unsafe.
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
                and _safe_summary(recap.get('title'), recap.get('text'), redact, high_risk)):
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


def _safe_summary(title, text, redact, high_risk):
    return (isinstance(title,str) and 1<=len(title.strip())<=120
        and isinstance(text,str) and 1<=len(text.strip())<=1500 and len(text.split())<=100
        and not high_risk.search(title+' '+text) and not redact(title+' '+text)[1]
        and not any(ord(ch)<32 and ch not in '\n\t' for ch in title+text))
