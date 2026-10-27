"""Approved response support contract; synthetic inputs, never a semantic oracle."""
import asyncio
from dataclasses import replace
import json

import httpx
import pytest

from app.chat.context import decode_answer, ChatProviderUnavailable
from app.core.models import Message, MessageRole
from tests.test_chat_context import built, revision
from tests.test_chat_service import request
from tests.test_development_ai import setup


def output(basis, aliases=(), insufficient=False):
    return Message(role=MessageRole.ASSISTANT, content=json.dumps(dict(
        answer='Synthèse des informations explicitement envoyées.',
        reference_aliases=list(aliases), support_basis=basis, insufficient_context=insufficient)))


@pytest.mark.parametrize('basis,ids,insufficient,rows,valid', [
    ('dialogue', (), False, (), True),
    ('dialogue', (), False, (revision(),), True),  # Available is not the same as cited.
    ('canonical', ('R1',), False, (revision(),), True),
    ('mixed', ('R1',), False, (revision(),), True),
    ('insufficient', (), True, (), True),
    ('insufficient', ('R1',), True, (revision(),), True),
    ('canonical', (), False, (), False),
    ('mixed', (), False, (), False),
    ('dialogue', ('R1',), False, (revision(),), False),
    ('canonical', ('R999',), False, (revision(),), False),
    ('canonical', ('R1', 'R1'), False, (revision(),), False),
    ('dialogue', (), True, (), True),  # Actual owner-reported response: useful but incomplete.
    ('insufficient', (), False, (), True),  # No inferred equivalence with the boolean.
    ('canonical', ('R1',), True, (revision(),), True),
    ('mixed', ('R1',), True, (revision(),), True),
    ('canonical', (), True, (), False),
    ('mixed', (), True, (), False),
    ('dialogue', ('R1',), True, (revision(),), False),
    ('invented-basis', (), False, (), False),
])
def test_support_declaration_must_match_actual_sent_context(basis, ids, insufficient, rows, valid):
    context = built(rows)
    if valid:
        answer, references, flag, checked_basis = decode_answer(output(basis, ids, insufficient), context)
        assert answer and checked_basis == basis and flag is insufficient
        assert len(references) == len(ids)
    else:
        with pytest.raises(ChatProviderUnavailable):
            decode_answer(output(basis, ids, insufficient), context)


@pytest.mark.parametrize('basis,ids', [('dialogue', ()), ('mixed', ('R1',))])
@pytest.mark.parametrize('insufficient', [False, True])
def test_declaration_cannot_manufacture_user_dialogue(basis, ids, insufficient):
    context = built((revision(),))
    no_dialogue = replace(context, request=replace(context.request, messages=context.request.messages[:2]))
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(output(basis, ids, insufficient), no_dialogue)


def test_missing_basis_is_not_heuristically_inferred():
    message = output('dialogue')
    value = json.loads(message.content); del value['support_basis']
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(replace(message, content=json.dumps(value)), built())


@pytest.mark.parametrize('insufficient', [False, True])
def test_empty_space_rich_dialogue_accepted_without_knowledge_or_source_write(tmp_path, monkeypatch, insufficient):
    # Domain-neutral synthetic CI fixture. The medical reproduction stays private.
    text = 'Dossier fictif : objectif explicite, historique déclaré et trois questions non résolues. Résume uniquement ces informations.'
    raw = dict(model='mistral-small-2603', usage=dict(prompt_tokens=968, completion_tokens=445),
        choices=[dict(finish_reason='stop', message=dict(content=output('dialogue', (), insufficient).content))])
    ai, who, context, _, calls, ledger, _, repository = setup(tmp_path, monkeypatch,
        lambda _: httpx.Response(200, json=raw))
    before = context.values[:]
    result = asyncio.run(ai.respond(who, request(messages=(Message(role=MessageRole.USER, content=text),))))
    assert result.support_basis == 'dialogue' and result.insufficient_context is insufficient
    assert not result.references and not result.provided_revisions
    assert context.values == before == [] and repository.calls == 0 and not repository.saved
    record, = asyncio.run(ai.diagnostics(who, request()))['items']
    assert record['raw_response'] == raw and record['outcome'] == 'accepted'
    assert all(c['result'] == 'PASS' for c in record['checks'])
    assert len(calls) == 1 and len(json.loads(ledger.read_text())['calls']) == 1


def test_real_empty_object_alias_failure_stays_rejected_with_precise_private_reason():
    data = json.loads(output('dialogue').content)
    data['reference_aliases'] = {}  # Actual real-provider protocol failure, no repair.
    observed = []
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(Message(role=MessageRole.ASSISTANT, content=json.dumps(data)), built(),
            observer=lambda *args: observed.append(args))
    assert observed[-1][0] == 'chat.reference_and_insufficient_types'
    assert observed[-1][1] is False and 'JSON array' in observed[-1][2]


def test_active_prompt_explicitly_specifies_array_and_boolean_dialogue_example():
    from app.chat.context import SYSTEM
    example = json.loads(SYSTEM.split('Dialogue-only example: ')[1].rstrip('.'))
    assert example['reference_aliases'] == [] and example['support_basis'] == 'dialogue'
    assert example['insufficient_context'] is True
    assert 'JSON array' in SYSTEM and 'NEVER an object' in SYSTEM
    assert decode_answer(Message(role=MessageRole.ASSISTANT, content=json.dumps(example)), built())[3] == 'dialogue'


@pytest.mark.parametrize('rows', [(), (revision(),)])
def test_general_knowledge_has_no_canonical_citations_even_when_space_data_is_available(rows):
    answer, references, insufficient, basis = decode_answer(output('general'), built(rows))
    assert answer and references == () and not insufficient and basis == 'general'
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(output('general', ('R1',)), built((revision(),)))


def test_empty_space_general_question_reaches_approved_provider_with_no_canonical_write(tmp_path, monkeypatch):
    text = 'Proponimi una lista della spesa per fare un risotto'
    content = dict(answer='Per un risotto: riso Carnaroli, brodo, cipolla, burro e Parmigiano.',
        reference_aliases=[], support_basis='general', insufficient_context=False)
    def replay(request):
        sent = json.loads(request.content)
        system = sent['messages'][0]['content']
        assert 'Answer general questions normally even when the Space is empty' in system
        assert 'Use ONLY' not in system and text in str(sent['messages'])
        return httpx.Response(200, json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=40),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(content)))]))
    ai, who, context, _, calls, _, _, repository = setup(tmp_path, monkeypatch, replay)
    result = asyncio.run(ai.respond(who, request(messages=(Message(role=MessageRole.USER,content=text),))))
    assert result.message.content == content['answer'] and result.support_basis == 'general'
    assert not result.insufficient_context and not result.references and not result.provided_revisions
    assert len(calls) == 1 and context.values == [] and repository.calls == 0


def test_general_basis_does_not_expand_guest_snapshot_contract():
    from app.chat.snapshot_answer import decode_snapshot_answer
    with pytest.raises(ValueError):
        decode_snapshot_answer(output('general'), {'items': []})
