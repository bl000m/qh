"""Focused offline replay: recap presentation never replaces detailed knowledge."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.models import GenerationResult, Message, MessageRole, ContextResult
from app.understanding.extractor import UnderstandingExtractor
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import UumExtractionProvider
from app.understanding import recap
from app.chat.context import build_context, decode_answer, ChatContextUnavailable, ChatInputInvalid
from app.chat.references import expand_model_context
from tests.test_chat_context import revision
from tests.test_consolidation import consolidation_output, reference_replay


def recipe():
    details=['Pour quatre personnes, prévoir 320 g de riz Carnaroli et 1,2 litre de bouillon.',
        'Après la tostatura, ajouter progressivement le bouillon, puis terminer par la mantecatura.',
        'Les variantes proposées sont aux champignons, au safran ou au radicchio.']
    atomic=dict(format='qh.atomic-understanding/1',items=[dict(text=t,primary_dimension='situation_information',
        assignment_certainty='asserted',evidence=[dict(quote=t)]) for t in details])
    output=consolidation_output(atomic)
    output['recap']=dict(title='Préparation d’un risotto',
        text='Ce contexte contient une recette de risotto pour quatre personnes, avec les ingrédients et les étapes de préparation. Il présente également trois variantes et les techniques permettant une cuisson progressive et une finition crémeuse.',
        supporting_statements=details)
    return details,output


def test_one_engine_call_retains_full_details_exact_evidence_and_version_bound_recap():
    details,output=recipe();frozen=deepcopy(output)
    delegate=Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(output)))))
    reference_replay(delegate)
    provider=UumExtractionProvider(delegate,consolidate=True,with_recap=True)
    policy=Mock(evaluate=AsyncMock(return_value=type('Decision',(),dict(allowed=True))()))
    scope,subject,version=str(uuid4()),str(uuid4()),str(uuid4())
    conversation=dict(id='recipe',revision_no=1,acquired_at='2026-10-27T10:00:00Z',metadata={},
        turns=[dict(id=str(uuid4()),speaker='assistant (unverified dialogue)',text='\n\n'.join(details))])
    source,rows=asyncio.run(propose_selected_conversation(subject_id=subject,context_id=scope,
        conversation=conversation,extraction_key='recap-test',policy=policy,provider=provider,descriptor_version=3))
    original_hash=UnderstandingExtractor.source_hash(source)
    bound=recap.bind(provider.recap,rows,version)
    summary=recap.from_version([dict(content=r['content']) for r in bound],dict(id=version,revision_ids=[r['id'] for r in bound]))
    assert summary['title']=='Préparation d’un risotto' and len(summary['text'].split())<=100
    assert '320 g' not in summary['text'] and '320 g' in bound[0]['content']['text']
    assert [r['content']['text'] for r in bound]==details and len(bound)==3
    for row,expected in zip(bound,details):
        quote=row['content']['citations'][0]
        assert source['content'][quote['start']:quote['end']]==quote['quote']==expected
        assert row['validation_state']=='proposed'
    assert UnderstandingExtractor.source_hash(source)==original_hash and output==frozen
    assert 'recap' not in rows[0]['content']['extraction']  # No mutation of the Engine result.
    assert delegate.generate.await_count==1
    system=delegate.generate.call_args.args[0].messages[0].content
    assert 'not a transcript' in system and 'never to understanding.items' in system
    assert 'assistant explanations as user preferences' in system


@pytest.mark.parametrize('change',['too_long','invented_support','duplicate_support','wrong_version'])
def test_bad_recap_is_rejected_without_repair_or_foreign_version_reuse(change):
    _,output=recipe()
    if change=='too_long':output['recap']['text']='mot '*101
    elif change=='invented_support':output['recap']['supporting_statements']=['Une information absente.']
    elif change=='duplicate_support':output['recap']['supporting_statements']*=2
    if change!='wrong_version':
        with pytest.raises(ValueError):recap.decode(json.dumps(output))
    else:
        _,summary=recap.decode(json.dumps(output))
        rows=[dict(id=str(uuid4()),content=dict(text=i['text'],extraction={})) for i in output['understanding']['items']]
        bound=recap.bind(summary,rows,str(uuid4()))
        with pytest.raises(ValueError):recap.from_version(bound,dict(id=str(uuid4()),revision_ids=[r['id'] for r in rows]))


def test_recap_word_limit_does_not_limit_detailed_statements():
    _,output=recipe()
    long_detail=' '.join('détail'+str(i) for i in range(250))
    output['understanding']['items'].append(dict(text=long_detail,primary_dimension=None,evidence=[dict(quote=long_detail)]))
    atomic,_=recap.decode(json.dumps(output))
    assert atomic['items'][-1]['text']==long_detail


def test_chat_can_cite_details_beyond_the_old_40_item_and_8kb_limits():
    rows=tuple(revision(revision_id='detail-'+str(i),item_id='item-'+str(i),
        content={'text':('Détail mémorisé '+str(i)+'. ')*40}) for i in range(60))
    messages=(Message(role=MessageRole.USER,content='Donne-moi les détails mémorisés.'),)
    context=build_context(context_id='space',revisions=rows,messages=messages,
        extended_dialogue=True,consolidated=True)
    assert context.revisions==rows and not context.partial and context.context_bytes>8000
    packet=json.loads(context.request.messages[1].content)
    sent=expand_model_context(packet,max_revisions=100)
    assert len(sent)==60 and sent[-1]['content']['text']==rows[-1].content['text']
    alias=next(k for k,v in packet['allowed_reference_aliases'].items() if v==rows[-1].revision_id)
    result=Message(role=MessageRole.ASSISTANT,content=json.dumps(dict(answer=rows[-1].content['text'],
        reference_aliases=[alias],support_basis='canonical',insufficient_context=False)))
    assert decode_answer(result,context)[1]==(rows[-1],)
    foreign=replace(rows[-1],context_space_id='other-space')
    with pytest.raises(ChatContextUnavailable):build_context(context_id='space',revisions=(foreign,),messages=messages,consolidated=True)
    too_big=replace(rows[-1],content={'text':'x'*1_000_001})
    with pytest.raises(ChatInputInvalid):build_context(context_id='space',revisions=(too_big,),messages=messages,consolidated=True,extended_dialogue=True)
    assert 'do not fill gaps using general knowledge' in context.request.messages[0].content


def test_retrieval_hydrates_every_exact_consolidated_detail():
    from app.chat.implementation import ContextualChatService
    from tests.test_chat_service import request
    rows=[revision(revision_id=str(i),item_id='item'+str(i)) for i in range(60)]
    async def browse(req):
        return ContextResult(hits=(),revisions=(next(r for r in rows if r.revision_id==req.query.revision_id),))
    context=Mock(browse=AsyncMock(side_effect=browse))
    service=ContextualChatService(context=context,policy=Mock(),provider=Mock(),model='offline')
    collected,partial=asyncio.run(service._collect(replace(request(),consolidated_revision_ids=tuple(r.revision_id for r in rows))))
    assert collected==tuple(rows) and not partial and context.browse.await_count==60


def test_recap_instruction_distinguishes_statement_text_from_original_evidence():
    details, output = recipe()
    original_quote = 'Try **Carnaroli** rice.'
    output['understanding']['items'][0]['evidence'] = [dict(quote=original_quote)]
    request = build_context(context_id='space', revisions=(), messages=(
        Message(role=MessageRole.USER, content='Recipe?'),)).request
    # The Engine supplies the authorized source packet; no provider HTTP is used.
    request = replace(request, messages=(request.messages[0], Message(role=MessageRole.USER,
        content=json.dumps(dict(source_revision_id='source', input_sha256='hash', text=original_quote, turns=[dict(turn_id='turn', start=0, end=len(original_quote))])))))
    delegate = Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(
        role=MessageRole.ASSISTANT, content=json.dumps(output)))))
    reference_replay(delegate)
    observer = Mock()
    provider = UumExtractionProvider(delegate, consolidate=True, with_recap=True, observer=observer)
    asyncio.run(provider.generate(request))
    observer.assert_any_call('uum.authorized_passage_references', True)
    observer.assert_any_call('uum.recap_exact_statement_support', True)
    sent = delegate.generate.call_args.args[0]
    assert 'NEVER "Try **Carnaroli** rice."' in sent.messages[0].content
    field = sent.output_schema['properties']['recap']['anyOf'][0]['properties']['supporting_statements']
    assert 'never evidence[].quote' in field['description']
    assert 'not its evidence quote' in field['items']['description']
    assert provider.recap['supporting_statements'] == details

    # Reproduce the real failure shape without retaining the private response:
    # an exact source quote is still invalid in a statement-support declaration.
    output['recap']['supporting_statements'][0] = original_quote
    delegate.generate.return_value = GenerationResult(message=Message(
        role=MessageRole.ASSISTANT, content=json.dumps(output)))
    observer.reset_mock()
    with pytest.raises(ValueError, match='Exact unambiguous detailed recap support required'):
        asyncio.run(provider.generate(request))
    observer.assert_any_call('uum.recap_exact_statement_support', False,
        'Invalid recap envelope or exact detailed statement support')
    assert original_quote not in str(observer.call_args)
    assert delegate.generate.await_count == 2  # One per explicit request, no retry.


def test_italian_subject_recap_stays_short_while_chat_receives_all_30_steps():
    details = [f'{i}. Attività {i}: preparare e verificare il materiale {i}.' for i in range(1, 31)]
    output = consolidation_output(dict(format='qh.atomic-understanding/1', items=[
        dict(text=t, primary_dimension=None, evidence=[dict(quote=t)]) for t in details]))
    output['recap'].update(title='Organizzazione di un laboratorio informatico',
        text='Linee guida proposte per organizzare un laboratorio informatico, con trenta attività pratiche e verifiche del materiale. La procedura dettagliata resta disponibile per la preparazione e lo svolgimento del laboratorio.')
    atomic, summary = recap.decode(json.dumps(output))
    assert len(summary['text'].split()) < 40  # No artificial minimum.
    for length in (100, 101):
        candidate = deepcopy(output); candidate['recap']['text'] = 'parola '*length
        if length == 100: recap.decode(json.dumps(candidate))
        else:
            with pytest.raises(ValueError): recap.decode(json.dumps(candidate))
    rows = tuple(revision(revision_id=str(i), item_id='item'+str(i), content=dict(text=item['text']))
        for i, item in enumerate(atomic['items']))
    context = build_context(context_id='space', revisions=rows, consolidated=True, extended_dialogue=True,
        messages=(Message(role=MessageRole.USER, content='Dammi tutti i 30 passaggi completi.'),))
    packet = json.loads(context.request.messages[1].content)
    assert [r['content']['text'] for r in expand_model_context(packet, max_revisions=100)] == details
    assert 'main language of the ORIGINAL' in recap.INSTRUCTIONS
    assert 'Never narrate the exchange' in recap.INSTRUCTIONS


@pytest.mark.parametrize('attributed', [False, True], ids=['workshop-final-content', 'essential-personal-attribution'])
def test_recap_final_content_and_essential_attribution_offline(attributed):
    actions = ['Definire gli obiettivi.', 'Preparare i materiali.',
        *[f'Preparare e verificare l’attività pratica {i}.' for i in range(3, 29)],
        'Valutare i risultati.', 'Pianificare il follow-up.']
    steps = '\n'.join(f'{i}. {action}' for i, action in enumerate(actions, 1))
    if attributed:
        original = 'Giulia: Preferirei un laboratorio in presenza, ma non ho ancora deciso se partecipare.'
        detailed = 'Giulia preferirebbe un laboratorio in presenza; la sua partecipazione non è decisa.'
        title = 'Preferenza di Giulia per il laboratorio'
        summary = 'Giulia preferirebbe un laboratorio in presenza, ma non ha ancora deciso se partecipare.'
    else:
        original = 'Linee guida per progettare e condurre un atelier informatico:\n'+steps
        detailed = 'L’assistente propone linee guida per un atelier informatico in 30 passaggi:\n'+steps
        title = 'Organizzazione di un atelier informatico'
        summary = ('Questo contesto contiene le linee guida per progettare e condurre un atelier informatico '
            'in 30 passaggi, dalla definizione degli obiettivi e preparazione dei materiali fino alle '
            'attività pratiche, alla valutazione dei risultati e al follow-up.')
    output = dict(format=recap.FORMAT, understanding=dict(format='qh.atomic-understanding/1', items=[
        dict(text=detailed, primary_dimension=None, evidence=[dict(quote=original)])]),
        recap=dict(title=title, text=summary, supporting_statements=[detailed]))
    frozen = deepcopy(output)
    delegate = Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(
        role=MessageRole.ASSISTANT, content=json.dumps(output)))))
    reference_replay(delegate)
    provider = UumExtractionProvider(delegate, consolidate=True, with_recap=True)
    conversation = dict(id='final-content', revision_no=1, acquired_at='2026-10-27T10:00:00Z', metadata={},
        turns=[dict(id='request', speaker='user', text='Puoi aiutarmi a preparare un laboratorio?'),
            dict(id='content', speaker='user' if attributed else 'assistant (unverified dialogue)', text=original)])
    conversation_before = deepcopy(conversation)
    policy = Mock(evaluate=AsyncMock(return_value=type('Decision', (), dict(allowed=True))()))
    source, rows = asyncio.run(propose_selected_conversation(subject_id=str(uuid4()), context_id=str(uuid4()),
        conversation=conversation, extraction_key='recap-final-content', policy=policy, provider=provider, descriptor_version=3))
    # Replays check the request and unchanged acceptance/preservation path. They
    # do not establish how a real model will follow the semantic instructions.
    instructions = delegate.generate.call_args.args[0].messages[0].content
    assert 'final reusable result' in instructions and 'not the process that produced it' in instructions
    assert 'Ideally 1-3 short sentences' in instructions and 'No target word count or minimum' in instructions
    assert 'ONLY when indispensable to meaning' in instructions
    assert provider.recap['title'] == title and provider.recap['text'] == summary
    assert provider.recap['supporting_statements'] == [detailed]
    assert rows[0]['content']['text'] == detailed and rows[0]['validation_state'] == 'proposed'
    citation = rows[0]['content']['citations'][0]
    assert citation['quote'] == source['content'][citation['start']:citation['end']] == original
    assert output == frozen and conversation == conversation_before and delegate.generate.await_count == 1
