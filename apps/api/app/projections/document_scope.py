"""Unified knowledge and retained document-scoped approvals; no canonical writes."""

EMPTY_NOTICE = ("Ce contexte ne contient pas suffisamment d'informations accessibles pour en présenter un résumé. "
    "Les informations non autorisées par le propriétaire restent privées.")
NOTICE_ITEM = dict(reference='R1', text=EMPTY_NOTICE, validation_state='proposed',
    origin_kind='projection_notice', sources=[])


def empty_projection(name):
    # The existing snapshot envelope requires one presentation entry. This fixed
    # notice is not canonical knowledge, has no source/anchor and never reaches AI.
    return dict(format='qh.disclosure/1', name=name, items=[dict(NOTICE_ITEM)], notice=EMPTY_NOTICE)


def is_empty_projection(payload):
    return (payload.get('format') == 'qh.disclosure/1'
        and isinstance(payload.get('name'),str) and 1<=len(payload['name'])<=256
        and payload.get('notice') == EMPTY_NOTICE and payload.get('items') == [NOTICE_ITEM]
        and not payload.get('recap') and not payload.get('document_recaps'))


def document_scope(rows, policy, document_sources):
    # New approvals share the unified understanding. Original download rights
    # never filter knowledge; retain the old rule only for historical policies.
    if policy.knowledge_scope=='context':
        return tuple(rows), []
    selected, excluded = [], []
    unauthorized = set(document_sources) - (set(policy.semantic_documents) & set(policy.original_documents))
    for row in rows:
        sources = {p.revision_id for p in row.provenance}
        sources.update(c.get('source_revision_id') for c in row.content.get('citations', []))
        if sources & unauthorized:
            excluded.append(dict(revision_id=row.revision_id, reason='document_information_not_authorized'))
        else:
            selected.append(row)
    return tuple(selected), excluded


def restrict_snapshot(payload, allowed_references, *, verified_recap=False):
    """Access-time restriction of an immutable snapshot; never expands its contents."""
    if is_empty_projection(payload):
        return payload
    items = {i['reference']:i for i in payload['items'] if i['reference'] in allowed_references}
    while True:
        dangling = [ref for ref,item in items.items() if not set(item.get('relation', {}).values()) <= items.keys()]
        if not dangling:
            break
        for ref in dangling:
            items.pop(ref)
    if not items:
        return empty_projection(payload.get('name', 'Contexte partagé'))
    result = dict(payload, items=list(items.values()))
    # Old introductions were approved before document filtering. Fail closed for
    # their unbound prose, including old introduction-only presentation entries.
    if not verified_recap or len(items) != len(payload['items']):
        result.pop('recap', None)
        result.pop('document_recaps', None)
    return accessible_introduction(result)


def accessible_introduction(payload, *, allow_document_fallback=True):
    """Reuse one already scoped canonical synopsis; never synthesize random excerpts."""
    if is_empty_projection(payload):
        return payload
    result=dict(payload)
    if result.get('recap',{}).get('title')=='Aperçu · extraits autorisés':
        result.pop('recap')  # Withdraw the old presentation, never rewrite its snapshot.
    summaries=result.pop('document_recaps',[])
    if allow_document_fallback and not result.get('recap') and len(summaries)==1:
        result['recap']=dict(summaries[0])
    return result
