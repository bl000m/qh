"""Project existing version-bound recaps without new inference or text assembly."""
from app.understanding.recap import COMPATIBLE_VERSIONS


def projected_recap(rows, anchors, masks, redact, high_risk, safe_items=(), *, require_claim_review=False):
    allowed = {a['revision_id'] for a in anchors}
    candidates = []
    for row in rows:
        extraction = row.content.get('extraction')
        recap = extraction.get('recap') if isinstance(extraction, dict) else None
        if not isinstance(recap, dict) or recap.get('presentation_version') not in COMPATIBLE_VERSIONS or recap.get('modular'):
            continue
        basis, support = recap.get('basis_revision_ids'), recap.get('support_revision_ids')
        title, text = recap.get('title'), recap.get('text')
        if (recap.get('format') != 'qh.context-recap/1' or not isinstance(basis, list)
                or not basis or any(not isinstance(r, str) for r in basis)
                or row.revision_id not in basis
                or not isinstance(support, list) or not support
                or any(not isinstance(r, str) or r not in basis for r in support)
                or not _safe_summary(title,text,redact,high_risk)):
            continue
        # Reviewed recaps use exact claim evidence while retaining the full-basis
        # presence check. Legacy recaps keep their conservative disclosure rules.
        # Never stitch items, truncate statements or infer support during sharing.
        if recap.get('presentation_version')==4:
            if _reviewed_scope(recap,rows,anchors,masks,redact,high_risk):
                candidates.append(dict(title=title,text=text))
            continue
        if require_claim_review:continue
        fully_covered = not masks and set(basis) <= allowed
        exact_disclosed_synopsis = any(item['text'] == text and title in item['text']
            for item in safe_items)
        if fully_covered or exact_disclosed_synopsis:
            candidates.append(dict(title=title, text=text))
    # Do not arbitrarily choose between historical consolidated versions.
    return candidates[0] if len(candidates) == 1 else None

def _reviewed_scope(recap,rows,anchors,masks,redact,high_risk):
    indexed={r.revision_id:r for r in rows}
    support=set(recap['support_revision_ids'])
    allowed={a['revision_id'] for a in anchors}
    aliases={a['reference'] for a in anchors if a['revision_id'] in support}
    return (set(recap['basis_revision_ids'])<=set(indexed) and support<=allowed
        and not any(m['reference'] in aliases for m in masks)
        and _review_safe(recap,indexed,redact,high_risk))


def recap_status(rows, recap):
    if recap:
        return 'available'
    present = any(isinstance(row.content.get('extraction'), dict)
        and (isinstance(row.content['extraction'].get('recap'), dict) or row.content['extraction'].get('recap_components')) for row in rows)
    return 'restricted' if present else 'unavailable'


def projected_components(rows, anchors, masks, redact, high_risk, *, require_claim_review=False):
    """Select independent version-bound components, never compose new prose."""
    from app.understanding.recap import PRESENTATION_VERSION
    components = []
    for row in rows:
        extraction = row.content.get('extraction')
        values = extraction.get('recap_components',[]) if isinstance(extraction,dict) else []
        if not isinstance(values,list) or any(not isinstance(c,dict) for c in values):
            return None, []
        components.extend((row,c) for c in values)
    versions = {c.get('version_id') for _,c in components}
    if len(versions)!=1:
        return None, []
    allowed = {a['revision_id'] for a in anchors}
    masked_refs = {m['reference'] for m in masks}
    masked = {a['revision_id'] for a in anchors if a['reference'] in masked_refs}
    selected, seen = [], set()
    indexed = {r.revision_id:r for r in rows}
    for row,component in components:
        if not _component_valid(row,component,indexed,allowed-masked,redact,high_risk,PRESENTATION_VERSION,require_claim_review):
            continue
        key = (component['kind'],component.get('source_revision_id'))
        if key in seen:
            return None, []  # Conflicting components must not arbitrarily win.
        seen.add(key)
        selected.append(component)
    selected.sort(key=lambda c:c['component_index'])
    general = next(({k:c[k] for k in ('title','text')} for c in selected if c['kind']=='general'),None)
    documents = [{k:c[k] for k in ('title','text')} for c in selected if c['kind']=='document']
    return general, documents


def _component_valid(row, c, indexed, safe, redact, high_risk, version, require_claim_review=False):
    basis, support = c.get('basis_revision_ids'), c.get('support_revision_ids')
    title, text = c.get('title'), c.get('text')
    if (c.get('format')!='qh.context-recap/1' or c.get('presentation_version') not in (3,version)
        or not isinstance(c.get('version_id'),str) or not c['version_id']
        or not isinstance(basis,list) or not basis or any(not isinstance(r,str) for r in basis)
        or not isinstance(support,list) or not support or any(not isinstance(r,str) for r in support)
        or row.revision_id not in support or not set(support)<=set(basis) or not set(support)<=safe
        or any(indexed[ref].content.get('extraction',{}).get('recap_version_id')!=c['version_id'] for ref in support)
        or not isinstance(c.get('component_index'),int) or c['component_index']<0
        or c.get('kind') not in ('general','document')
        or not _safe_summary(title,text,redact,high_risk)):
        return False
    if c.get('presentation_version')==version:
        if not set(basis)<=set(indexed) or not _review_safe(c,indexed,redact,high_risk):return False
        if c['kind']=='general':return c.get('source_revision_id') is None
    elif c['kind']=='general':
        return not require_claim_review and c.get('source_revision_id') is None and set(basis)<=safe
    source = c.get('source_revision_id')
    return isinstance(source,str) and all(any(quote.get('source_revision_id')==source
        for quote in indexed[ref].content.get('citations',[])) for ref in support)


def _safe_summary(title, text, redact, high_risk):
    return (isinstance(title,str) and 1<=len(title.strip())<=120
        and isinstance(text,str) and 1<=len(text.strip())<=1500 and len(text.split())<=100
        and not high_risk.search(title+' '+text) and not redact(title+' '+text)[1]
        and not any(ord(ch)<32 and ch not in '\n\t' for ch in title+text))


def _review_safe(component,indexed,redact,high_risk):
    from app.understanding.recap_review import reviewed_evidence
    try:
        if any(indexed[ref].content.get('extraction',{}).get('recap_version_id')!=component['version_id']
            for ref in component['support_revision_ids']):return False
        for claim in component['claim_review']['claims']:
            for support in claim['supports']:
                sources={p.revision_id for p in indexed[support['revision_id']].provenance}
                if any(e['source_revision_id'] not in sources for e in support['evidence']):return False
        quotes=reviewed_evidence(component,{ref:r.content for ref,r in indexed.items()})
        return all(not high_risk.search(q) and not redact(q)[1]
            and not any(ord(c)<32 and c not in '\n\t' for c in q) for q in quotes)
    except (ValueError,KeyError,TypeError,IndexError):
        return False
