"""Project existing version-bound recaps without new inference or text assembly."""
from app.understanding.recap import COMPATIBLE_VERSIONS


def projected_recap(rows, anchors, masks, redact, high_risk, safe_items=()):
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
        # Resolve declared supports to the exact canonical version. Presence of
        # unrelated basis items does not mean their content supports the summary.
        if recap.get('presentation_version') in (3,4):
            if _support_scope(recap,rows,anchors,masks):
                candidates.append(dict(title=title,text=text))
            continue
        fully_covered = not masks and set(basis) <= allowed
        exact_disclosed_synopsis = any(item['text'] == text and title in item['text']
            for item in safe_items)
        if fully_covered or exact_disclosed_synopsis:
            candidates.append(dict(title=title, text=text))
    # Do not arbitrarily choose between historical consolidated versions.
    return candidates[0] if len(candidates) == 1 else None

def _support_scope(recap,rows,anchors,masks):
    indexed={r.revision_id:r for r in rows}
    support=set(recap['support_revision_ids'])
    allowed={a['revision_id'] for a in anchors}
    aliases={a['reference'] for a in anchors if a['revision_id'] in support}
    return (set(recap['basis_revision_ids'])<=set(indexed) and support<=allowed
        and not any(m['reference'] in aliases for m in masks)
        and _canonical_supports(recap,indexed))


def recap_status(rows, recap):
    if recap:
        return 'available'
    present = any(isinstance(row.content.get('extraction'), dict)
        and (isinstance(row.content['extraction'].get('recap'), dict) or row.content['extraction'].get('recap_components')) for row in rows)
    return 'restricted' if present else 'unavailable'


def projected_components(rows, anchors, masks, redact, high_risk):
    """Select independent version-bound components, never compose new prose."""
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
        if not _component_valid(row,component,indexed,allowed-masked,redact,high_risk):
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


def _component_valid(row, c, indexed, safe, redact, high_risk):
    basis, support = c.get('basis_revision_ids'), c.get('support_revision_ids')
    title, text = c.get('title'), c.get('text')
    if (c.get('format')!='qh.context-recap/1' or c.get('presentation_version') not in (3,4)
        or not isinstance(c.get('version_id'),str) or not c['version_id']
        or not isinstance(basis,list) or not basis or any(not isinstance(r,str) for r in basis)
        or not isinstance(support,list) or not support or any(not isinstance(r,str) for r in support)
        or row.revision_id not in support or not set(support)<=set(basis) or not set(support)<=safe
        or any(indexed[ref].content.get('extraction',{}).get('recap_version_id')!=c['version_id'] for ref in support)
        or not isinstance(c.get('component_index'),int) or c['component_index']<0
        or c.get('kind') not in ('general','document')
        or not _safe_summary(title,text,redact,high_risk)):
        return False
    if not set(basis)<=set(indexed) or not _canonical_supports(c,indexed):return False
    if c['kind']=='general':return c.get('source_revision_id') is None
    source = c.get('source_revision_id')
    return isinstance(source,str) and all(any(quote.get('source_revision_id')==source
        for quote in indexed[ref].content.get('citations',[])) for ref in support)


def _safe_summary(title, text, redact, high_risk):
    return (isinstance(title,str) and 1<=len(title.strip())<=120
        and isinstance(text,str) and 1<=len(text.strip())<=1500 and len(text.split())<=100
        and not high_risk.search(title+' '+text) and not redact(title+' '+text)[1]
        and not any(ord(ch)<32 and ch not in '\n\t' for ch in title+text))


def _canonical_supports(component,indexed):
    # Apply the existing original-citation/provenance Guard even when quotations
    # are hidden in the UI. Broad evidence is never trimmed automatically.
    from app.projections.disclosure_guard import OutboundDisclosureGuard
    try:
        if any(indexed[ref].content.get('extraction',{}).get('recap_version_id')!=component['version_id']
            for ref in component['support_revision_ids']):return False
        for ref in component['support_revision_ids']:
            row=indexed[ref]
            quotes,reason,masks=OutboundDisclosureGuard._quotes(row.content,row,
                {p.revision_id:p.revision_id for p in row.provenance})
            if reason or masks or not quotes or any(ord(c)<32 and c not in '\n\t' for q in quotes for c in q['quote']):return False
        return True
    except (ValueError,KeyError,TypeError,IndexError,AttributeError):
        return False
