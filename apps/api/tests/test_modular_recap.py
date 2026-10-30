"""One Engine, independent canonical summaries, offline requests only."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.models import GenerationResult, Message, MessageRole
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.projections.guest_payload import recipient_payload
from app.understanding import recap
from app.understanding.documents import prepare_document, original_citations
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import UumExtractionProvider
from tests.test_consolidation import reference_output
from tests.test_context_sovereignty import projected
from tests.test_disclosure import policy

TEXTS=['Giulia Rossi décrit son expérience en développement dans son CV.',
    'Le contrat prévoit une activité de développement.',
    'Giulia souhaiterait devenir architecte, sans décision contractuelle.']


def generate_documents(long=False):
    scope,version=str(uuid4()),str(uuid4())
    originals,turns,catalogue=[],[],[]
    for i,text in enumerate(TEXTS):
        padding='\n'+''.join(f'Annexe neutre {n}.\n' for n in range(800)) if long and i==0 else ''
        doc,source=prepare_document(scope,str(uuid4()),f'document-{i}.pdf',b'%PDF-synthetic',[text+padding])
        originals.append(source);turns.extend(doc['document_turns'])
        catalogue.append(dict(source_revision_id=source['id'],name=doc['name'],turn_ids=[t['id'] for t in doc['document_turns']]))
    summary=dict(title='Parcours de Giulia Rossi',text='Parcours professionnel déclaré de Giulia Rossi.',supporting_statements=[TEXTS[0]],
        documents=[dict(document_ref=f'd{i+1}',title=['Expérience déclarée','Conditions du contrat','Orientation envisagée'][i],text=text,supporting_statements=[text]) for i,text in enumerate(TEXTS)])
    packets=[]

    async def respond(request):
        packet=json.loads(request.messages[-1].content);packets.append(packet)
        if 'statements' in packet:
            assert packet['documents'][0]['turn_ids']
            return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(summary)))
        available=''.join(segment['text'] for segment in packet['segments'])
        atomic=dict(format='qh.atomic-understanding/1',items=[dict(text=text,primary_dimension=None,evidence=[dict(quote=text)]) for text in TEXTS if text in available])
        envelope=dict(format=recap.FORMAT,understanding=atomic,recap=summary) if 'understanding' in request.output_schema['properties'] else atomic
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(reference_output(envelope,packet))))

    delegate=Mock(generate=AsyncMock(side_effect=respond))
    provider=UumExtractionProvider(delegate,consolidate=True,with_recap=True,chunked=True,documents=catalogue)
    source,rows=asyncio.run(propose_selected_conversation(subject_id=str(uuid4()),context_id=scope,
        conversation=dict(id='modular',revision_no=1,acquired_at='2026-10-30T10:00:00Z',metadata={},turns=turns),
        extraction_key='modular-test',policy=Mock(evaluate=AsyncMock(return_value=SimpleNamespace(allowed=True))),provider=provider,descriptor_version=3))
    rows=original_citations(rows,originals)
    before=deepcopy(rows)
    bound=recap.bind(provider.recap,rows,version,originals)
    assert rows==before and [r['content']['text'] for r in bound]==TEXTS
    assert delegate.generate.await_count==(len(provider.parts)+1 if long else 1)
    assert all('source_revision_id' not in doc for packet in packets for doc in packet.get('documents',[]))
    return bound,version,originals,provider


def projected_documents():
    rows,_,_,_=generate_documents()
    base=projected()[0]
    return [replace(base,revision_id=r['id'],item_id=r['item_id'],content=r['content']) for r in rows]


@pytest.mark.parametrize('long',[False,True])
def test_same_generation_calls_and_version_bound_source_components(long):
    rows,version,originals,provider=generate_documents(long)
    current=dict(id=version,revision_ids=[r['id'] for r in rows])
    value=recap.from_version(json.loads(json.dumps(rows)),current)
    assert len(value['documents'])==3 and value['text']=='Parcours professionnel déclaré de Giulia Rossi.'
    assert {d['source_revision_id'] for d in value['documents']}=={s['id'] for s in originals}
    for row in rows:
        for component in row['content']['extraction'].get('recap_components',[]):
            assert component['version_id']==version and component['support_revision_ids']
    with pytest.raises(ValueError):recap.from_version(rows,dict(current,id=str(uuid4())))
    corrupt=deepcopy(provider.recap)
    corrupt['documents'][0]['supporting_statements']=[TEXTS[1]]
    with pytest.raises(ValueError,match='same-document'):recap.bind(corrupt,rows,version,originals)
    corrupt=deepcopy(provider.recap);corrupt['documents'].pop()
    with pytest.raises(ValueError,match='Every supported document'):recap.bind(corrupt,rows,version,originals)


@pytest.mark.parametrize('restriction',['excluded','masked','sensitive-summary'])
def test_independent_projection_never_hydrates_or_grants_originals(restriction):
    rows=projected_documents();guard=OutboundDisclosureGuard()
    complete,_=guard.apply(rows,policy(original_documents=()))
    assert len(complete['document_recaps'])==3 and complete['recap']
    if restriction=='excluded':
        rows=rows[:1]+rows[2:]  # Contract carrier excluded before the Guard.
    elif restriction=='masked':
        rows[1].content['text']+=' contact@example.test'
    else:
        rows[1].content['extraction']['recap_components'][0]['text']='Diagnostic médical privé.'
    frozen=deepcopy(rows)
    payload,report=guard.apply(rows,policy(original_documents=()))
    assert payload['recap']==complete['recap']
    assert [c['title'] for c in payload['document_recaps']]==['Expérience déclarée','Orientation envisagée']
    assert 'contractuelle' in payload['document_recaps'][1]['text']
    assert report['recap_status']=='available' and rows==frozen
    assert recipient_payload(payload)==payload
    # Download rights do not broaden, narrow or otherwise alter semantic selection.
    assert guard.apply(rows,policy(original_documents=(str(uuid4()),)))[0]==payload
    assert 'source_revision_id' not in json.dumps(payload)
    if restriction=='masked':
        only_documents=deepcopy(rows);only_documents[0].content['text']+=' private@example.test'
        limited=guard.apply(only_documents,policy())[0]
        assert 'recap' not in limited
        assert [c['title'] for c in limited['document_recaps']]==['Orientation envisagée']
    bad=deepcopy(payload);bad['document_recaps'][0]['source_revision_id']=str(uuid4())
    from app.projections.guest import GuestUnavailable
    with pytest.raises(GuestUnavailable):recipient_payload(bad)
    for row in rows:
        for component in row.content['extraction'].get('recap_components',[]):component['version_id']='stale'
    assert 'document_recaps' not in guard.apply(rows,policy())[0]


def test_compatible_legacy_recap_still_reads_without_modular_backfill():
    rows=projected();rows[0].content['extraction']['recap']['presentation_version']=2
    value=OutboundDisclosureGuard().apply(rows,policy())[0]
    assert value['recap'] and 'document_recaps' not in value
