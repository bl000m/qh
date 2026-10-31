"""One canonical recap per version: never blocks memorization, never hidden by undisclosed quotes.

Synthetic CV-like PDFs reproduce the real failure shapes offline: page evidence with
telephone, email, date ranges and a confidentiality clause, and a provider recap
declaring the same support twice. No provider HTTP, live storage or private data.
"""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.models import GenerationResult, Message, MessageRole, SourceRevisionRef
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.understanding import recap
from app.understanding.documents import prepare_document, original_citations
from app.understanding.extractor import canonical_json
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import UumExtractionProvider
from tests.test_consolidation import reference_output
from tests.test_context_sovereignty import projected
from tests.test_disclosure import policy

PAGES = [
    'Giulia Rossi — Développeuse Python\nTél. 06 12 34 56 78 — giulia.rossi@example.test\n'
    'Expérience : développeuse backend chez Atlas SA, 01/2019 – 06/2024',
    'Clause de secret professionnel : la salariée respecte la confidentialité.\n'
    'Poste : développeuse, CDI proposé, non signé.',
    'Giulia souhaiterait évoluer vers un rôle d’architecte, sans décision prise.',
]
ITEMS = [  # Clean statement texts; their original evidence carries the risky words.
    ('Giulia Rossi est développeuse Python.', ['Giulia Rossi — Développeuse Python',
        'Tél. 06 12 34 56 78 — giulia.rossi@example.test']),
    ('Giulia Rossi a été développeuse backend chez Atlas SA.',
        ['Expérience : développeuse backend chez Atlas SA, 01/2019 – 06/2024']),
    ('Le contrat proposé comporte une obligation de confidentialité.',
        ['Clause de secret professionnel : la salariée respecte la confidentialité.']),
    ('Le contrat de développeuse en CDI est proposé mais non signé.',
        ['Poste : développeuse, CDI proposé, non signé.']),
    ('Giulia souhaiterait évoluer vers un rôle d’architecte, sans décision.',
        ['Giulia souhaiterait évoluer vers un rôle d’architecte, sans décision prise.']),
]
TEXTS = [text for text, _ in ITEMS]
SUMMARY = dict(title='Parcours professionnel de Giulia Rossi',
    text='Ce contexte présente le parcours de développeuse de Giulia Rossi, un contrat proposé '
        'et ses souhaits d’évolution professionnelle.')


def generate_documents(long=False, support=None, pages=PAGES, items=ITEMS):
    """Offline UUM replay of one PDF per page; `support` overrides the recap's declared refs."""
    texts = [text for text, _ in items]
    scope, version = str(uuid4()), str(uuid4())
    originals, turns, catalogue = [], [], []
    for i, page in enumerate(pages):
        padding = '\n' + ''.join(f'Annexe neutre {n}.\n' for n in range(800)) if long and i == 0 else ''
        doc, source = prepare_document(scope, str(uuid4()), f'document-{i}.pdf', b'%PDF-synthetic', [page + padding])
        originals.append(source); turns.extend(doc['document_turns'])
        catalogue.append(dict(source_revision_id=source['id'], name=doc['name'], turn_ids=[t['id'] for t in doc['document_turns']]))
    schemas = []

    async def respond(request):
        packet = json.loads(request.messages[-1].content)
        schemas.append(request.output_schema)
        if 'statements' in packet:
            refs = {item['text']: item['ref'] for item in packet['statements']}
            declared = support or [refs[t] for t in texts] + [refs[texts[-1]]]  # Real shape: one ref repeated.
            return GenerationResult(message=Message(role=MessageRole.ASSISTANT,
                content=json.dumps(dict(SUMMARY, supporting_refs=declared))))
        available = ''.join(segment['text'] for segment in packet['segments'])
        atomic = dict(format='qh.atomic-understanding/1', items=[dict(text=text, primary_dimension=None,
            evidence=[dict(quote=q) for q in quotes]) for text, quotes in items if all(q in available for q in quotes)])
        statements = support or [*texts, texts[-1]]
        envelope = dict(format=recap.FORMAT, understanding=atomic, recap=dict(SUMMARY, supporting_statements=statements)) \
            if 'understanding' in request.output_schema['properties'] else atomic
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps(reference_output(envelope, packet))))

    delegate = Mock(generate=AsyncMock(side_effect=respond))
    checks = []
    provider = UumExtractionProvider(delegate, consolidate=True, with_recap=True, chunked=True, documents=catalogue,
        observer=lambda rule, passed, *reason: checks.append((rule, passed)))
    _, rows = asyncio.run(propose_selected_conversation(subject_id=str(uuid4()), context_id=scope,
        conversation=dict(id='cv', revision_no=1, acquired_at='2026-10-31T10:00:00Z', metadata={}, turns=turns),
        extraction_key='unified-test', policy=Mock(evaluate=AsyncMock(return_value=SimpleNamespace(allowed=True))),
        provider=provider, descriptor_version=3))
    rows = original_citations(rows, originals)
    bound, published = recap.bind(provider.recap, rows, version)
    return SimpleNamespace(rows=bound, published=published, version=version, provider=provider,
        delegate=delegate, checks=checks, schemas=schemas, originals=originals)


def projected_documents(result=None):
    rows = (result or generate_documents()).rows
    base = projected()[0]
    return [replace(base, revision_id=r['id'], item_id=r['item_id'], content=r['content'],
        provenance=tuple(SourceRevisionRef(source_id=str(uuid4()), revision_id=p) for p in r['provenance'])) for r in rows]


@pytest.mark.parametrize('long', [False, True], ids=['one-call', 'chunked-final-recap'])
def test_duplicate_support_declaration_still_memorizes_items_and_recap(long):
    result = generate_documents(long=long)
    assert result.published and [r['content']['text'] for r in result.rows] == TEXTS
    assert result.checks.count(('uum.recap_exact_statement_support', True)) == 1
    summary = recap.from_version(result.rows, dict(id=result.version, revision_ids=[r['id'] for r in result.rows]))
    assert summary['title'] == SUMMARY['title'] and len(summary['support_revision_ids']) == len(TEXTS)
    assert result.delegate.generate.await_count == (len(result.provider.parts)+1 if long else 1)
    # Bounded provider schemas: no per-document components, regex patterns or statement texts.
    final = json.dumps(result.schemas[-1], ensure_ascii=False)
    assert 'documents' not in final and 'pattern' not in final and TEXTS[0] not in final


@pytest.mark.parametrize('long', [False, True], ids=['one-call', 'chunked-final-recap'])
def test_invalid_recap_publishes_validated_items_without_recap_or_retry(long):
    result = generate_documents(long=long, support=['s999'] if long else ['Une information absente.'])
    assert not result.published and [r['content']['text'] for r in result.rows] == TEXTS
    assert ('uum.recap_exact_statement_support', False) in result.checks
    assert recap.from_version(result.rows, dict(id=result.version, revision_ids=[r['id'] for r in result.rows])) is None
    assert result.delegate.generate.await_count == (len(result.provider.parts)+1 if long else 1)
    # Exact original evidence is still mandatory for every published item.
    assert all(c['quote'] in PAGES[0]+PAGES[1]+PAGES[2] for r in result.rows for c in r['content']['citations'])


@pytest.mark.parametrize('include_quotes', [False, True])
def test_undisclosed_sensitive_citations_do_not_hide_the_canonical_recap(include_quotes):
    rows = projected_documents()
    frozen = deepcopy(rows)
    payload, report = OutboundDisclosureGuard().apply(rows, policy(knowledge_scope='context', include_quotes=include_quotes))
    wire = json.dumps(payload, ensure_ascii=False)
    assert '06 12 34 56 78' not in wire and 'giulia.rossi@example.test' not in wire and rows == frozen
    if include_quotes:
        # Sharing quotations discloses the clause: that support is excluded, so the recap is withheld.
        assert 'recap' not in payload and report['recap_status'] == 'restricted'
        assert {'recognised_high_risk_citation'} == {e['reason'] for e in report['exclusions']}
    else:
        assert payload['recap'] == SUMMARY and report['recap_status'] == 'available'
        assert 'secret' not in wire and 'document_recaps' not in payload


def test_regeneration_from_retained_pdf_sources_publishes_items_even_when_recap_is_invalid():
    from app.understanding.selected import selected_source
    from tests.test_consolidation import fixture

    service, who, scope, repository, ai, batch = fixture()
    intake, originals, turns = [], [], []
    for index, page in enumerate(PAGES):
        document, source = prepare_document(scope, str(uuid4()), f'doc-{index}.pdf', b'%PDF-offline', [page])
        intake.append(document); originals.append(source); turns.extend(document['document_turns'])
    retained = selected_source(scope, dict(id='retained', acquired_at='2026-10-31T10:00:00Z', metadata={}, turns=turns))
    current = dict(id=str(uuid4()), source_revision_id=retained['id'], revision_ids=[str(uuid4()) for _ in TEXTS])
    batch.update(intake=intake, current=current, regenerating=True, pending_count=0)
    frozen = deepcopy(batch)
    service.read = AsyncMock(return_value=dict(understanding=[dict(content=dict(text=t), validation_state='proposed') for t in TEXTS]))
    sources = {r['id']: r for r in [retained, *originals]}
    repository.original = AsyncMock(side_effect=lambda context, revision: deepcopy(sources[revision]))
    support = list(TEXTS)

    async def respond(request):
        atomic = dict(format='qh.atomic-understanding/1', items=[dict(text=text, primary_dimension=None,
            evidence=[dict(quote=q) for q in quotes]) for text, quotes in ITEMS])
        output = dict(format=recap.FORMAT, understanding=atomic, recap=dict(SUMMARY, supporting_statements=support))
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,
            content=json.dumps(reference_output(output, json.loads(request.messages[-1].content)))))

    ai._provider.return_value = Mock(generate=AsyncMock(side_effect=respond))
    published = []

    async def publish(context, operation, intake_ids, source, revisions):
        assert source == retained and intake_ids == [r['id'] for r in intake]
        assert [r['content']['text'] for r in revisions] == TEXTS
        published.append(revisions)
        return dict(current=dict(id=operation, revision_ids=[r['id'] for r in revisions]))

    repository.publish.side_effect = publish
    result = asyncio.run(service.consolidate(who, scope, str(uuid4())))
    assert result['recap']['title'] == SUMMARY['title'] and 'documents' not in result['recap']
    support[0] = TEXTS[0] + ' Inventé.'
    result = asyncio.run(service.consolidate(who, scope, str(uuid4())))
    assert result['recap'] is None and len(published) == 2
    assert 'recap' not in published[1][0]['content']['extraction']
    repository.import_document.assert_not_called(); repository.fail.assert_not_awaited()
    assert batch == frozen and sources[retained['id']] == retained


def test_compact_final_recap_packet_never_resends_original_quotes():
    original = 'ORIGINAL-PDF-ONLY ' + ('Long source paragraph with exact evidence. ' * 200)
    packet = dict(documents=[dict(document_ref='d1', turn_ids=['cv'])], statements=TEXTS[:2],
        evidence=[dict(statement=text, passages=[dict(quote=original, speakers=['unverified PDF'], turn_ids=['cv'])]*3)
            for text in TEXTS[:2]])
    references = recap.FinalRecapReferences(packet)
    assert 'ORIGINAL-PDF-ONLY' not in canonical_json(references.packet)
    assert len(references.packet['provenance']) == 1
    assert references.schema['properties']['supporting_refs']['items']['enum'] == ['s001', 's002']
    expanded = references.expand(json.dumps(dict(SUMMARY, supporting_refs=['s002', 's001', 's002'])))
    assert expanded['supporting_statements'] == [TEXTS[1], TEXTS[0]]
    with pytest.raises(ValueError):
        references.expand(json.dumps(dict(SUMMARY, supporting_refs=['s003'])))


def test_retained_modular_versions_project_their_general_recap_without_document_synopses():
    """Existing RH-shaped data: modular root plus components, no backfill required."""
    rows = projected_documents()
    root = rows[0].content['extraction']['recap']
    root['modular'] = True
    rows[1].content['extraction']['recap_components'] = [dict(root, kind='document',
        title='Synthèse du CV', text='Développeuse Python.', source_revision_id=str(uuid4()), component_index=1)]
    payload, report = OutboundDisclosureGuard().apply(rows, policy(knowledge_scope='context'))
    assert payload['recap'] == SUMMARY and 'document_recaps' not in payload
    assert 'Synthèse du CV' not in json.dumps(payload, ensure_ascii=False)
