"""Offline desired-output replay and prompt contract; not a live model quality test."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.models import GenerationResult, Message, MessageRole
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import UumExtractionProvider
from tests.test_consolidation import consolidation_output, reference_replay


@pytest.mark.parametrize('declared', [False, True])
def test_question_is_not_a_personal_fact_and_assistant_advice_is_not_adoption(declared):
    question = ('Guadagno 2000 euro al mese e ho due figli. Quanto posso risparmiare?' if declared
        else 'quanto posso risparmiare con 2000 euro al mese e due figli ?')
    advice = 'È consigliabile accumulare un fondo emergenza pari a 3–6 mesi di spese prima di investire.'
    illustration = 'Esempio ipotetico: risparmiare 100 euro, non una decisione presa.'
    conversation = dict(id='synthetic-saving', revision_no=1, acquired_at='2026-10-28T10:00:00Z', metadata={},
        turns=[dict(id='question', speaker='user (owner-declared)', text=question),
            dict(id='answer', speaker='assistant (unverified dialogue)', text=advice+'\n'+illustration)])
    scenario = ('L’utente dichiara 2000 euro mensili e due figli.' if declared else
        'Scenario della domanda: 2000 euro mensili e due figli; reddito e situazione familiare non confermati.')
    items = [dict(text=scenario, primary_dimension='situation_information' if declared else 'hypotheses_uncertainties',
        assignment_certainty='asserted' if declared else 'tentative', evidence=[dict(quote=question)]),
        dict(text='Quanto si potrebbe risparmiare nello scenario indicato? Spese effettive non precisate.',
            primary_dimension='open_questions', assignment_certainty='asserted', evidence=[dict(quote=question)]),
        dict(text='L’assistente propone un esempio ipotetico non verificato di risparmio di 100 euro, non adottato dall’utente.',
            primary_dimension='hypotheses_uncertainties', assignment_certainty='tentative', evidence=[dict(quote=illustration)])]
    output = consolidation_output(dict(format='qh.atomic-understanding/1', items=items))
    frozen = deepcopy(conversation)
    delegate = Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(
        role=MessageRole.ASSISTANT, content=json.dumps(output)))))
    reference_replay(delegate)
    policy = Mock(evaluate=AsyncMock(return_value=type('Decision', (), dict(allowed=True))()))
    source, rows = asyncio.run(propose_selected_conversation(subject_id=str(uuid4()), context_id=str(uuid4()),
        conversation=conversation, extraction_key='fidelity-offline', policy=policy,
        provider=UumExtractionProvider(delegate, consolidate=True, with_recap=True), descriptor_version=3))
    sent = delegate.generate.call_args.args[0]
    prompt = sent.messages[0].content
    assert 'Questions are not declarations' in prompt
    assert 'unsolicited generic assistant recommendations' in prompt
    assert 'explicitly\ndescribe it as an unverified assistant suggestion' in prompt
    assert 'shortest listed unique passage sufficient' in prompt
    assert "A personal question's conditional scenario is not a declared personal situation" in prompt
    packet = json.loads(sent.messages[-1].content)
    assert [t['speaker'] for t in packet['turns']] == [t['speaker'] for t in conversation['turns']]
    assert len(rows) == 3 and conversation == frozen
    assert [r['content']['text'] for r in rows] == [i['text'] for i in items]
    assert rows[0]['content']['primary_dimension']['certainty'] == ('asserted' if declared else 'tentative')
    for row in rows:
        assert row['validation_state'] == 'proposed' and row.get('validated_by') is None
        assert row['content']['primary_dimension']['review_state'] == 'proposed'
        for citation in row['content']['citations']:
            assert citation['source_revision_id'] == source['id']
            assert source['content'][citation['start']:citation['end']] == citation['quote']
            assert citation['turn_id'] == ('answer' if row is rows[2] else 'question')
    assert advice in source['content']  # Source intact; filler need not become an atomic item.
    assert len({c['source_revision_id'] for r in rows for c in r['content']['citations']}) == 1
    delegate.generate.assert_awaited_once()
