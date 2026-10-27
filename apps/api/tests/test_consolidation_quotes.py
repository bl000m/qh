"""Synthetic workshop replay through schema, offline HTTP and the unchanged Engine."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest

from adapters.llm.mistral import ExperimentBudget, MistralProvider
from app.understanding.citations import CitationResolutionError
from app.understanding.quote_schema import exact_quote_schema
from app.understanding.selected import propose_selected_conversation, selected_source
from app.understanding.uum import OUTPUT_SCHEMA, UumExtractionProvider
from tests.test_consolidation import consolidation_output


def workshop(count=30):
    question = 'Propose un atelier de découverte.'
    lines = [f'{i}. **Étape {i}** : activité originale {i} pour l’atelier.' for i in range(1, count+1)]
    conversation = dict(id='workshop', revision_no=1, acquired_at='2026-10-27T10:00:00Z', metadata={},
        turns=[dict(id='question-1', speaker='user', text=question),
               dict(id='question-2', speaker='user', text=question),
               dict(id='answer', speaker='assistant (unverified dialogue)', text='\r\n'.join(lines))])
    return question, lines, conversation


@pytest.mark.parametrize('count', [30, 130])
def test_quote_choices_are_exact_unique_original_passages_without_source_mutation(count):
    question, lines, conversation = workshop(count)
    original = selected_source(str(uuid4()), conversation)
    packet = dict(source_revision_id=original['id'], text=original['content'], turns=original['origin']['turns'])
    frozen, schema_before = deepcopy(packet), deepcopy(OUTPUT_SCHEMA)
    constrained = exact_quote_schema(OUTPUT_SCHEMA, packet)
    choices = constrained['properties']['items']['items']['anyOf'][0]['properties']['evidence']['items']['properties']['quote']['enum']
    assert question not in choices  # Two identical turns: never choose one arbitrarily.
    assert all(line in choices for line in lines)
    assert '\r\n'.join(lines) in choices  # Full context remains available.
    assert '\n'.join([lines[5], lines[7], lines[9]]) not in choices
    assert lines[5].replace('**', '') not in choices
    assert packet == frozen and OUTPUT_SCHEMA == schema_before


@pytest.mark.parametrize('bad_quote', [None, 'collage', 'repeated', 'altered'])
def test_consolidation_quote_schema_and_final_validation_offline(tmp_path, monkeypatch, bad_quote):
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-only')
    question, lines, conversation = workshop()
    evidence = [dict(quote=lines[i]) for i in (5, 7, 9)]
    if bad_quote == 'collage': evidence = [dict(quote='\n'.join(e['quote'] for e in evidence))]
    elif bad_quote == 'repeated': evidence = [dict(quote=question)]
    elif bad_quote == 'altered': evidence = [dict(quote=lines[5].replace('**', ''))]
    atomic = dict(format='qh.atomic-understanding/1', items=[dict(
        text='La proposition de l’assistant inclut les activités 6, 8 et 10.',
        primary_dimension=None, evidence=evidence)])
    output = consolidation_output(atomic)
    frozen = deepcopy(output)
    sent = []

    def respond(request):
        body = json.loads(request.content)
        sent.append(body)
        assert 'max_tokens' not in body and body['model'] == 'mistral-small-2603'
        schema = body['response_format']['json_schema']['schema']['properties']['understanding']
        for shape in schema['properties']['items']['items']['anyOf']:
            choices = shape['properties']['evidence']['items']['properties']['quote']['enum']
            assert question not in choices and all(lines[i] in choices for i in (5, 7, 9))
            if bad_quote:
                assert evidence[0]['quote'] not in choices
        # Simulate even a provider violating the constrained schema: the Engine
        # must still reject, with no quote splitting/repair or automatic retry.
        return httpx.Response(200, json=dict(model='mistral-small-2603',
            usage=dict(prompt_tokens=1000, completion_tokens=500), choices=[dict(
                finish_reason='stop', message=dict(content=json.dumps(output)))]))

    delegate = MistralProvider(budget=ExperimentBudget(tmp_path/'ledger.json', create=True),
        transport=httpx.MockTransport(respond), provider_defaults=True)
    provider = UumExtractionProvider(delegate, consolidate=True, with_recap=True)
    policy = Mock(evaluate=AsyncMock(return_value=type('Decision', (), dict(allowed=True))()))
    call = propose_selected_conversation(subject_id=str(uuid4()), context_id=str(uuid4()),
        conversation=conversation, extraction_key='workshop-test', policy=policy,
        provider=provider, descriptor_version=3)
    if bad_quote:
        with pytest.raises(CitationResolutionError): asyncio.run(call)
    else:
        source, rows = asyncio.run(call)
        assert len(rows) == 1 and rows[0]['validation_state'] == 'proposed'
        citations = rows[0]['content']['citations']
        assert [c['quote'] for c in citations] == [lines[i] for i in (5, 7, 9)]
        assert all(source['content'][c['start']:c['end']] == c['quote'] for c in citations)
    assert len(sent) == 1 and output == frozen


def test_repeated_only_source_fails_before_provider_generation():
    question, _, conversation = workshop()
    conversation['turns'] = conversation['turns'][:2]
    original = selected_source(str(uuid4()), conversation)
    packet = dict(source_revision_id=original['id'], text=original['content'], turns=original['origin']['turns'])
    with pytest.raises(ValueError, match='No unique original quotation'):
        exact_quote_schema(OUTPUT_SCHEMA, packet)
    assert question in original['content']  # No deduplication or deletion of intake.
