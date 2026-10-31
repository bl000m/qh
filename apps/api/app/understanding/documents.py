"""Original document intake and exact page provenance; no second extraction engine."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib

from app.understanding.selected import selected_source

MAX_PDF_BYTES = 3 * 1024 * 1024


class DocumentInvalid(ValueError):
    pass


def prepare_document(scope, operation, name, data, pages, display_name=None):
    if not name.lower().endswith('.pdf') or len(name)>256 or any(c in name for c in ('/', '\\', '\r', '\n', '\0')):
        raise DocumentInvalid('Nom de fichier PDF invalide.')
    if display_name is not None:
        display_name=display_name.strip()
        if not 1<=len(display_name)<=256 or any(ord(c)<32 for c in display_name):
            raise DocumentInvalid('Le nom du document doit contenir entre 1 et 256 caractères, sans caractères de contrôle.')
    turns=[dict(id=f'{operation}:page:{i}', speaker=f'document {name}, page {i} (unverified source)', text=text)
           for i,text in enumerate(pages,1)]
    source=selected_source(scope, dict(id='document:'+operation, revision_no=1,
        acquired_at=datetime.now(timezone.utc).isoformat(), turns=[t for t in turns if t['text'].strip()],
        metadata=dict(filename=name, media_type='application/pdf', sha256=hashlib.sha256(data).hexdigest(),
            pages=len(pages), extraction='pypdf/1', empty_pages=[i for i,t in enumerate(pages,1) if not t.strip()])))
    source['source_name']=name
    document=dict(id=operation, kind='document', role='user', name=name,
        text=None, context=None, source_revision_id=source['id'],
        document_turns=turns,size_bytes=len(data))
    if display_name is not None:
        document['display_name']=display_name
    return document,source


def original_citations(revisions, sources):
    """Add exact original-page anchors to already Engine-validated citations."""
    by_turn={turn['turn_id']:(source,turn) for source in sources for turn in source['origin']['turns']}
    rows=deepcopy(revisions)
    for row in rows:
        citations=row['content']['citations']
        for citation in list(citations):
            entry=by_turn.get(citation.get('turn_id'))
            if entry is None:
                continue
            source,turn=entry
            text=source['content'][turn['start']:turn['end']]
            quote=citation['quote']
            if text.count(quote)!=1:
                raise ValueError('Ambiguous original PDF page evidence')
            start=turn['start']+text.index(quote)
            citations.append(dict(citation, source_revision_id=source['id'], start=start, end=start+len(quote)))
            if source['id'] not in row['provenance']:
                row['provenance'].append(source['id'])
    return rows
