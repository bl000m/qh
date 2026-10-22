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
    ('dialogue', (), True, (), False),
    ('insufficient', (), False, (), False),
    ('mixed', ('R1',), True, (revision(),), False),
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
def test_declaration_cannot_manufacture_user_dialogue(basis, ids):
    context = built((revision(),))
    no_dialogue = replace(context, request=replace(context.request, messages=context.request.messages[:2]))
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(output(basis, ids), no_dialogue)


def test_missing_basis_is_not_heuristically_inferred():
    message = output('dialogue')
    value = json.loads(message.content); del value['support_basis']
    with pytest.raises(ChatProviderUnavailable):
        decode_answer(replace(message, content=json.dumps(value)), built())


def test_empty_space_rich_dialogue_accepted_without_knowledge_or_source_write(tmp_path, monkeypatch):
    # Domain-neutral synthetic CI fixture. The medical reproduction stays private.
    text = 'Dossier fictif : objectif explicite, historique déclaré et trois questions non résolues. Résume uniquement ces informations.'
    raw = dict(model='mistral-small-2603', usage=dict(prompt_tokens=1079, completion_tokens=536),
        choices=[dict(finish_reason='stop', message=dict(content=output('dialogue').content))])
    ai, who, context, _, calls, ledger, _, repository = setup(tmp_path, monkeypatch,
        lambda _: httpx.Response(200, json=raw))
    before = context.values[:]
    result = asyncio.run(ai.respond(who, request(messages=(Message(role=MessageRole.USER, content=text),))))
    assert result.support_basis == 'dialogue' and not result.insufficient_context
    assert not result.references and not result.provided_revisions
    assert context.values == before == [] and repository.calls == 0 and not repository.saved
    record, = asyncio.run(ai.diagnostics(who, request()))['items']
    assert record['raw_response'] == raw and record['outcome'] == 'accepted'
    assert all(c['result'] == 'PASS' for c in record['checks'])
    assert len(calls) == 1 and len(json.loads(ledger.read_text())['calls']) == 1
