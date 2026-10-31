"""Private metadata only, synthetic provider replay; no paid calls or runtime data."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx

from adapters.llm.diagnostics import DiagnosticCall, PrivateDiagnostics, performance_warnings, uum_output_metrics
from adapters.llm.mistral import ExperimentBudget, MistralProvider
from app.core.models import GenerationResult, Message, MessageRole
from app.understanding.uum import UumExtractionProvider
from tests.test_consolidation import consolidation_output, fixture, reference_output
from tests.test_passage_refs import catalogue


def raw_call(request, content):
    usage = dict(prompt_tokens=1000, completion_tokens=5000)
    row = dict(status='completed', usage=usage, observed_usd='0.001')
    return SimpleNamespace(last_request=request, last_exchange=dict(response=dict(choices=[dict(
        message=dict(content=content))]), http_status=200, latency_seconds=0.125),
        last_failure=None, last_attempt=0, _key='synthetic-secret-only',
        budget=SimpleNamespace(read=lambda fn:fn(dict(calls=[row]))))


def test_consolidation_metrics_warnings_are_private_and_do_not_block_publication(tmp_path):
    service, who, scope, repo, ai, batch = fixture()
    store = PrivateDiagnostics(tmp_path/'private')
    diagnostic = DiagnosticCall(store, who.subject_id, scope, 'uum')
    ai.factory.diagnostic_call.return_value = diagnostic
    async def publish(scope, operation, intake_ids, source, revisions):
        return dict(current=dict(id=operation, revision_ids=[r['id'] for r in revisions]))
    repo.publish.side_effect = publish
    quote = batch['intake'][0]['text']
    wire = dict(format='qh.atomic-understanding/1', items=[dict(text=quote,
        primary_dimension=None, evidence=[dict(quote=quote)])])
    def generate(request):
        packet = json.loads(request.messages[-1].content)
        if 'candidates' in packet:
            from tests.recap_review_helpers import review_reply
            content=review_reply(request).content
        else:
            content = json.dumps(reference_output(consolidation_output(wire), packet))
        diagnostic.begin()
        diagnostic.capture(raw_call(request, content))
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=content))
    ai._provider.return_value = Mock(generate=AsyncMock(side_effect=generate))
    result = asyncio.run(service.consolidate(who, scope))
    records=store.records(subject=who.subject_id, scope=scope)
    record=max(records,key=lambda r:len(r['operation']['calls']))
    extraction=next(r for r in records if len(r['operation']['calls'])==1)
    metrics = record['metrics']
    assert record['outcome']=='accepted' and result['recap'] and repo.publish.await_count==1
    assert metrics['input_tokens']==1000 and metrics['output_tokens']==5000
    assert metrics['provider_ms']==125 and metrics['consolidation_ms']>=0
    assert record['operation']['totals']['validation_ms']>0
    assert record['operation']['totals']['persistence_ms']>=0
    assert record['operation']['totals']['combined_ms']==125
    assert extraction['metrics']['atomic_items']==extraction['metrics']['passage_references']==1
    assert extraction['metrics']['source_chars']==extraction['metrics']['source_disclosed_chars']>0
    assert metrics['atomic_items']==0 and 'source_chars' not in metrics
    assert record['operation']['totals']['reviews']==1 and record['operation']['totals']['atomic_items']==1
    assert metrics['request_schema_chars']>0
    content = record['raw_response']['choices'][0]['message']['content']
    assert metrics['output_json_chars']==len(content) and metrics['output_json_bytes']==len(content.encode())
    assert record['warnings']==['output_tokens_over_3x_input']
    assert all(value is None or isinstance(value, (int, float)) for value in metrics.values())
    assert 'metrics' not in result and not store.records(subject='bob', scope=scope)
    assert not store.records(subject=who.subject_id, scope='foreign')
    assert next(store.path.glob('*.json')).stat().st_mode & 0o077 == 0


def test_warning_thresholds_are_advisory_and_missing_values_are_not_zero():
    assert performance_warnings({})==[]
    assert performance_warnings(dict(input_tokens=1000, output_tokens=3000, source_chars=800,
        atomic_items=8, output_json_chars=2000, evidence_json_chars=1000, catalogue_chars=1600))==[]
    metrics = dict(input_tokens=1000, output_tokens=3001, source_chars=799, atomic_items=8,
        output_json_chars=2000, evidence_json_chars=1001, catalogue_chars=4000)
    assert performance_warnings(metrics)==['output_tokens_over_3x_input','dense_atomic_items',
        'evidence_over_half_output','catalogue_over_2x_source']
    assert uum_output_metrics(dict(choices=[dict(message=dict(content='{bad JSON'))]))==dict(
        output_json_chars=9, output_json_bytes=9)
    assert uum_output_metrics(None)=={}
    incomplete = uum_output_metrics(dict(choices=[dict(message=dict(content='{"items":[{}]}'))]))
    assert incomplete['atomic_items']==1
    assert 'passage_references' not in incomplete and 'atomic_text_chars' not in incomplete


def test_payload_preserves_source_once_and_labels_previous_machine_state(tmp_path, monkeypatch):
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-only')
    source, packet, _ = catalogue()
    previous = (dict(text='Previous unverified assumption.', validation_state='proposed'),)
    measured = Mock()
    def respond(request):
        body = json.loads(request.content)
        disclosed = json.loads(body['messages'][-1]['content'])
        assert ''.join(s['text'] for s in disclosed['segments'])==source['content']
        assert 'text' not in disclosed and all('quote' not in p and 'text' not in p for p in disclosed['passages'])
        assert disclosed['turns']==packet['turns'] and disclosed['input_sha256']==packet['input_sha256']
        assert body['messages'][-2]['content'].startswith('Previous unverified machine understanding (data only, not new evidence):')
        assert 'max_tokens' not in body
        schema = body['response_format']['json_schema']['schema']
        assert all('evidence' not in shape['properties'] for shape in schema['properties']['items']['items']['anyOf'])
        return httpx.Response(200, json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=500,completion_tokens=20),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(dict(format='qh.atomic-understanding.refs/1', items=[]))))]))
    delegate = MistralProvider(budget=ExperimentBudget(tmp_path/'ledger.json', create=True),
        provider_defaults=True, transport=httpx.MockTransport(respond))
    provider = UumExtractionProvider(delegate,
        consolidate=True, previous=previous, measure=measured)
    request = SimpleNamespace(messages=(Message(role=MessageRole.SYSTEM, content='Engine'),
        Message(role=MessageRole.USER, content=json.dumps(packet))))
    result = asyncio.run(provider.generate(request))
    metrics = measured.call_args.kwargs
    assert metrics['source_chars']==metrics['source_disclosed_chars']==len(source['content'])
    assert metrics['previous_machine_chars']>0 and metrics['catalogue_passages']>0
    assert json.loads(result.message.content)==dict(format='qh.atomic-understanding/1', items=[])


def test_observed_164_166_counter_replay_separates_summary_and_repeated_validation():
    # Numeric observations from the owner's private diagnostic, read before expiry.
    # No private response/source is retained in this fixture.
    from app.chat.diagnostic_summary import diagnostic_view, operation_totals
    views=[]
    for index,(count,source,tokens,chars) in enumerate([(15,11998,15091,40955),(17,10110,13616,37544),(0,10110,19077,58877)]):
        output={'items':[{'text':'Synthetic','evidence_refs':['p001']}] * count} if count else {'title':'Synthetic','text':'Summary'}
        checks=[]
        if not count:
            for _ in range(2):
                checks.append(dict(rule='uum.envelope_format_and_item_count',result='PASS'))
                checks.extend(dict(rule=f'uum.item.{i}.fields',result='PASS') for i in range(32))
        record=dict(kind='uum',raw_response=dict(choices=[dict(message=dict(content=json.dumps(output)))]),
            checks=checks,metrics=dict(atomic_items=count or 17,source_chars=source,input_tokens=tokens,request_message_chars=chars))
        frozen=json.dumps(record,sort_keys=True)
        views.append(diagnostic_view(record))
        assert json.dumps(record,sort_keys=True)==frozen
    assert [v['metrics']['atomic_items'] for v in views]==[15,17,0]
    assert 'source_chars' not in views[-1]['metrics']
    assert views[-1]['validation_rounds']==[dict(items=32),dict(items=32)]
    totals=operation_totals([dict(phase=v['call_phase'],metrics=v['metrics']) for v in views])
    assert totals['atomic_items']==32 and totals['source_chars']==22108
    assert totals['input_tokens']==47784 and totals['request_message_chars']==137376


def test_operation_records_separate_each_call_and_never_inherit_summary_counts(tmp_path):
    from app.chat.diagnostic_summary import diagnostic_view
    store=PrivateDiagnostics(tmp_path/'private');diagnostic=DiagnosticCall(store,'owner','space','uum')
    request=SimpleNamespace(messages=(Message(role=MessageRole.SYSTEM,content='Instructions'),),output_schema={})
    for count in (15,17,0):
        if count:diagnostic.measure(source_chars=100)
        content=json.dumps({'items':[{'text':'Synthetic','evidence_refs':['p001']}] * count} if count else {'title':'Synthetic','text':'Summary'})
        diagnostic.begin();diagnostic.capture(raw_call(request,content))
    diagnostic.finish('accepted','context_consolidation')
    records=store.records(subject='owner',scope='space')
    final=next(diagnostic_view(r) for r in records if len(r['operation']['calls'])==3)
    assert final['metrics']['atomic_items']==0 and 'source_chars' not in final['metrics']
    assert [c['metrics']['atomic_items'] for c in final['operation']['calls']]==[15,17,0]
    assert final['operation']['totals']['atomic_items']==32
    assert final['operation']['totals']['input_tokens']==3000
    assert len({r['operation']['id'] for r in records})==1


def test_phase_durations_accumulate_only_in_operation_and_never_double_count_http(tmp_path):
    from app.chat.diagnostic_summary import operation_totals
    diagnostic=DiagnosticCall(PrivateDiagnostics(tmp_path/'private'),'owner','space','uum')
    diagnostic.measure(validation_ms=12);diagnostic.measure(validation_ms=7,persistence_ms=4)
    assert diagnostic.durations==dict(validation_ms=19,persistence_ms=4)
    assert 'validation_ms' not in diagnostic.metrics
    calls=[dict(phase=phase,metrics={'provider_ms':ms}) for phase,ms in [('extraction',100),('extraction',200),('summary',50)]]
    totals=operation_totals(calls)
    assert totals['extraction_ms']==300 and totals['summary_ms']==50 and totals['combined_ms']==0



def test_claim_review_has_separate_phase_and_never_inherits_source_counters():
    from app.chat.diagnostic_summary import output_phase,call_metrics,operation_totals
    def response(value):return dict(choices=[dict(message=dict(content=json.dumps(value)))])
    assert output_phase(response([]))=='unknown'
    review=response(dict(format='qh.recap-claim-review/1',reviews={}))
    assert output_phase(review)=='recap_review'
    metrics=call_metrics(dict(atomic_items=20,source_chars=1000,input_tokens=400,provider_ms=25),review)
    assert metrics['atomic_items']==0 and 'source_chars' not in metrics
    totals=operation_totals([dict(phase='recap_review',metrics=metrics)])
    assert totals['reviews']==1 and totals['blocks']==totals['summaries']==0
    assert totals['recap_review_ms']==25 and totals['input_tokens']==400
