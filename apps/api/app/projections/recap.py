"""Share a recap only as part of the fully covered, owner-approved payload."""
from app.understanding.recap import PRESENTATION_VERSION


def projected_recap(rows, anchors, masks, redact, high_risk, safe_items=()):
    allowed = {a['revision_id'] for a in anchors}
    candidates = []
    for row in rows:
        extraction = row.content.get('extraction')
        recap = extraction.get('recap') if isinstance(extraction, dict) else None
        if not isinstance(recap, dict) or recap.get('presentation_version') != PRESENTATION_VERSION:
            continue
        basis, support = recap.get('basis_revision_ids'), recap.get('support_revision_ids')
        title, text = recap.get('title'), recap.get('text')
        if (recap.get('format') != 'qh.context-recap/1' or not isinstance(basis, list)
                or not basis or any(not isinstance(r, str) for r in basis)
                or row.revision_id not in basis
                or not isinstance(support, list) or not support
                or any(not isinstance(r, str) or r not in basis for r in support)
                or not isinstance(title, str) or not 1 <= len(title.strip()) <= 120
                or not isinstance(text, str) or not 1 <= len(text.strip()) <= 1500
                or len(text.split()) > 100 or high_risk.search(title+' '+text)
                or any(ord(c) < 32 and c not in '\n\t' for c in title+text)
                or redact(title+' '+text)[1]):
            continue
        # The normal route still requires the entire unmasked basis. A restrictive
        # projection may reuse the SAME existing synopsis only when it is already
        # one complete disclosed semantic statement, including every qualification.
        # Never stitch items, truncate statements or infer sentence-level support.
        fully_covered = not masks and set(basis) <= allowed
        exact_disclosed_synopsis = any(item['text'] == text and title in item['text']
            for item in safe_items)
        if fully_covered or exact_disclosed_synopsis:
            candidates.append(dict(title=title, text=text))
    # Do not arbitrarily choose between historical consolidated versions.
    return candidates[0] if len(candidates) == 1 else None


def recap_status(rows, recap):
    if recap:
        return 'available'
    present = any(isinstance(row.content.get('extraction'), dict)
        and isinstance(row.content['extraction'].get('recap'), dict) for row in rows)
    return 'restricted' if present else 'unavailable'
