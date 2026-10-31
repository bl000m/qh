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


def generate_documents(long=False, invalid_support=False):
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
            schema = request.output_schema
            assert schema['properties']['supporting_refs']['items']['enum'] == ['s001','s002','s003']
            documents_schema = schema['properties']['documents']
            assert documents_schema['required'] == ['d1','d2','d3']
            for index, component in enumerate(documents_schema['properties'].values()):
                assert component['properties']['supporting_refs']['items']['enum'] == [f's{index+1:03d}']
            if invalid_support:
                summary['documents'][0]['supporting_statements'] = [TEXTS[0].replace('décrit', 'decrit')]
            refs = {item['text']:item['ref'] for item in packet['statements']}
            def component(value):
                return dict(title=value['title'],text=value['text'],
                    supporting_refs=[refs.get(text,text) for text in value['supporting_statements']])
            wire = dict(component(summary), documents={d['document_ref']:component(d) for d in summary['documents']})
            return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(wire)))
        available=''.join(segment['text'] for segment in packet['segments'])
        atomic=dict(format='qh.atomic-understanding/1',items=[dict(text=text,primary_dimension=None,evidence=[dict(quote=text)]) for text in TEXTS if text in available])
        envelope=dict(format=recap.FORMAT,understanding=atomic,recap=summary) if 'understanding' in request.output_schema['properties'] else atomic
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(reference_output(envelope,packet))))

    delegate=Mock(generate=AsyncMock(side_effect=respond))
    checks=[]
    provider=UumExtractionProvider(delegate,consolidate=True,with_recap=True,chunked=True,documents=catalogue,
        observer=lambda rule, passed, *reason: checks.append((rule,passed)))
    try:
        source,rows=asyncio.run(propose_selected_conversation(subject_id=str(uuid4()),context_id=scope,
            conversation=dict(id='modular',revision_no=1,acquired_at='2026-10-30T10:00:00Z',metadata={},turns=turns),
            extraction_key='modular-test',policy=Mock(evaluate=AsyncMock(return_value=SimpleNamespace(allowed=True))),provider=provider,descriptor_version=3))
    except ValueError:
        assert invalid_support
        assert checks[-1] == ('uum.recap_exact_statement_support', False)
        assert delegate.generate.await_count == len(provider.parts)+1
        raise
    assert checks.count(('uum.recap_exact_statement_support', True)) == 1
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
    # The general prose requires its complete unmasked basis as well.
    assert ('recap' in payload)==(restriction=='sensitive-summary')
    if 'recap' in payload:
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


def test_chunked_final_recap_rejects_altered_support_without_retry():
    # Real failure pattern: one altered accent invalidates an otherwise valid summary.
    with pytest.raises(ValueError, match='Exact unambiguous detailed recap support'):
        generate_documents(long=True, invalid_support=True)


def test_final_schema_excludes_foreign_and_mixed_document_supports():
    packet = dict(documents=[dict(document_ref='d1',turn_ids=['cv']),
        dict(document_ref='d2',turn_ids=['contract']),dict(document_ref='d3',turn_ids=['empty'])],
        statements=['CV meaning.', 'Contract meaning.', 'Combined meaning.', 'Dialogue meaning.'],
        evidence=[dict(statement=text, passages=[dict(turn_ids=turns)]) for text,turns in [
            ('CV meaning.', ['cv']), ('Contract meaning.', ['contract']),
            ('Combined meaning.', ['cv','contract']), ('Dialogue meaning.', ['chat'])]])
    schema = recap.final_summary_schema(packet)
    assert schema['properties']['supporting_statements']['items']['enum'] == packet['statements']
    documents = schema['properties']['documents']
    assert documents['minItems'] == documents['maxItems'] == 2
    assert [c['properties']['supporting_statements']['items']['enum']
        for c in documents['items']['anyOf']] == [['CV meaning.'], ['Contract meaning.']]
    packet['documents'] = []
    assert 'documents' not in recap.final_summary_schema(packet)['properties']


def test_final_recap_references_preserve_exact_text_and_reject_foreign_support():
    packet = dict(documents=[dict(document_ref='d1',turn_ids=['cv']),
        dict(document_ref='d2',turn_ids=['contract'])], statements=['CV **exact**.', 'Contract é.'],
        evidence=[dict(statement=text,passages=[dict(turn_ids=[turn])])
            for text,turn in [('CV **exact**.','cv'),('Contract é.','contract')]])
    protocol = recap.FinalRecapReferences(packet)
    def component(ref):
        return dict(title='Proposed',text='Proposed synopsis.',supporting_refs=[ref])
    wire = dict(component('s001'),documents=dict(d1=component('s001'),d2=component('s002')))
    result = protocol.expand(json.dumps(wire))
    assert result['supporting_statements'] == ['CV **exact**.']
    assert result['documents'][1]['supporting_statements'] == ['Contract é.']
    frozen = deepcopy(wire)
    for refs in [['s002'], ['s001','s001'], ['unknown'], ['CV **exact**.']]:
        wire['documents']['d1']['supporting_refs'] = refs
        with pytest.raises(ValueError,match='Exact unambiguous'):
            protocol.expand(json.dumps(wire))
    wire = deepcopy(frozen)
    del wire['documents']['d2']
    with pytest.raises(ValueError,match='Invalid extraction object fields'):
        protocol.expand(json.dumps(wire))


def test_general_generation_cannot_select_a_support_that_the_guard_would_mask():
    from app.projections.disclosure_guard import introductory_support
    statements=['Parcours professionnel déclaré.', 'Contact au +33 6 12 34 56 78.']
    packet=dict(documents=[],statements=statements,evidence=[])
    protocol=recap.FinalRecapReferences(packet,general_support_allowed=introductory_support)
    assert protocol.schema['properties']['supporting_refs']['items']['enum']==['s001']
    assert [s['text'] for s in protocol.packet['statements']]==statements
    value=dict(title='Parcours',text='Présentation du parcours professionnel.',supporting_refs=['s002'])
    with pytest.raises(ValueError,match='Exact unambiguous'):
        protocol.expand(json.dumps(value))
    value['supporting_refs']=['s001']
    assert protocol.expand(json.dumps(value))['supporting_statements']==[statements[0]]


def test_regenerate_modular_recaps_from_retained_pdf_sources_without_reimport():
    from app.understanding.selected import selected_source
    from tests.test_consolidation import fixture

    service, who, scope, repository, ai, batch = fixture()
    intake, originals, turns = [], [], []
    for index, text in enumerate(TEXTS):
        document, source = prepare_document(scope, str(uuid4()), f'doc-{index}.pdf', b'%PDF-offline', [text])
        intake.append(document)
        originals.append(source)
        turns.extend(document['document_turns'])
    retained = selected_source(scope, dict(id='retained', acquired_at='2026-10-30T10:00:00Z', metadata={}, turns=turns))
    current = dict(id=str(uuid4()), source_revision_id=retained['id'], revision_ids=[str(uuid4()) for _ in TEXTS])
    batch.update(intake=intake, current=current, regenerating=True, pending_count=0)
    frozen = deepcopy(batch)
    service.read = AsyncMock(return_value=dict(understanding=[dict(content=dict(text=t), validation_state='proposed') for t in TEXTS]))
    sources = {r['id']: r for r in [retained, *originals]}
    repository.original = AsyncMock(side_effect=lambda context, revision: deepcopy(sources[revision]))
    summary = dict(title='Parcours professionnel', text='Expérience, contrat et orientation envisagée.',
        supporting_statements=[TEXTS[0]], documents=[dict(document_ref=f'd{i+1}', title=f'Document {i+1}',
            text=text, supporting_statements=[text]) for i, text in enumerate(TEXTS)])

    async def respond(request):
        packet = json.loads(request.messages[-1].content)
        atomic = dict(format='qh.atomic-understanding/1', items=[dict(text=t, primary_dimension=None,
            evidence=[dict(quote=t)]) for t in TEXTS])
        output = dict(format=recap.FORMAT, understanding=atomic, recap=summary)
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps(reference_output(output, packet))))

    delegate = Mock(generate=AsyncMock(side_effect=respond))
    ai._provider.return_value = delegate

    async def publish(context, operation, intake_ids, source, revisions):
        assert source == retained and intake_ids == [r['id'] for r in intake]
        assert [r['content']['text'] for r in revisions] == TEXTS
        assert len({r['item_id'] for r in revisions}) == len(TEXTS)
        for row, original in zip(revisions, originals):
            assert any(c['source_revision_id'] == original['id'] for c in row['content']['citations'])
        return dict(current=dict(id=operation, revision_ids=[r['id'] for r in revisions]))

    repository.publish.side_effect = publish
    result = asyncio.run(service.consolidate(who, scope, str(uuid4())))
    assert len(result['recap']['documents']) == 3 and delegate.generate.await_count == 1
    repository.import_document.assert_not_called()
    assert batch == frozen and sources[retained['id']] == retained
    # A failed explicit regeneration must never publish an unvalidated replacement.
    repository.publish.reset_mock()
    summary['documents'][0]['supporting_statements'] = [TEXTS[0] + ' Invented.']
    with pytest.raises(ValueError, match='Exact unambiguous'):
        asyncio.run(service.consolidate(who, scope, str(uuid4())))
    repository.publish.assert_not_awaited()
    repository.fail.assert_awaited_once()
    assert batch == frozen and delegate.generate.await_count == 2


def test_compact_summary_removes_only_source_quotes_and_duplicate_provenance(monkeypatch):
    from app.understanding.extractor import canonical_json
    original='ORIGINAL-PDF-ONLY '+('Long source paragraph with exact evidence. '*200)
    packet=dict(documents=[dict(document_ref='d1',turn_ids=['cv']),dict(document_ref='d2',turn_ids=['contract'])],
        statements=['Camille maîtrise Python.','Camille envisage Rust, sans décision.','Le contrat est proposé, pas signé.'],
        evidence=[dict(statement=text,passages=[dict(quote=original,speakers=[speaker],turn_ids=[turn])]*3)
            for text,speaker,turn in [('Camille maîtrise Python.','CV non vérifié','cv'),
                ('Camille envisage Rust, sans décision.','CV non vérifié','cv'),
                ('Le contrat est proposé, pas signé.','Projet de contrat','contract')]])
    frozen=deepcopy(packet);compact=recap.FinalRecapReferences(packet)
    def legacy(payload,identifiers):
        result=deepcopy(payload)
        for item in result['evidence']:item['statement_ref']=identifiers[item.pop('statement')]
        return result
    with monkeypatch.context() as patch:
        patch.setattr(recap,'compact_summary_provenance',legacy)
        before=recap.FinalRecapReferences(packet)
    assert compact.schema==before.schema and packet==frozen
    assert compact.packet['statements']==before.packet['statements']
    assert len(compact.packet['provenance'])==2
    assert [row['provenance_refs'] for row in compact.packet['evidence']]==[['e001'],['e001'],['e002']]
    assert 'ORIGINAL-PDF-ONLY' not in canonical_json(compact.packet)
    assert len(canonical_json(compact.packet))<len(canonical_json(before.packet))/10
    def component(ref):return dict(title='Contexte proposé',text='Compréhension proposée, incertitude préservée.',supporting_refs=[ref])
    wire=dict(component('s001'),documents=dict(d1=component('s002'),d2=component('s003')))
    assert compact.expand(json.dumps(wire))==before.expand(json.dumps(wire))


def test_general_recap_keeps_all_declared_supports_above_two_with_existing_bounds():
    statements=['Projet Atlas proposé.', 'Décision Lumen adoptée.', 'Contrainte Neptune déclarée.']
    protocol=recap.FinalRecapReferences(dict(documents=[],statements=statements,evidence=[]))
    assert protocol.schema['properties']['supporting_refs']['maxItems']==len(statements)
    assert recap.summary_schema()['properties']['supporting_statements']['maxItems']==100
    value=dict(title='Projet et décisions',text='Présentation du projet, des décisions et des contraintes.',
        supporting_refs=['s001','s002','s003'])
    assert protocol.expand(json.dumps(value))['supporting_statements']==statements
    for refs in (['s001','s001'],['s001','unknown']):
        with pytest.raises(ValueError,match='Exact unambiguous'):
            protocol.expand(json.dumps(dict(value,supporting_refs=refs)))
