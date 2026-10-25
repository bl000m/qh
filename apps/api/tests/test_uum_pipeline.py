"""UUM on clean disposable SQL/Neo4j; preserved production stack is never selected."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound, GenerationResult, Message, MessageRole, ContextRetrievalUnavailable
from app.core.uum import PRIMARY_DIMENSIONS
from app.context.presence import dimension_presence
from app.understanding.uum import FORMAT
from app.understanding.enrichment import EnrichmentUnavailable
from app.review.service import ReviewService
from adapters.postgres.review import PostgresReviewRepository
from adapters.postgres.semantic_profiles import register_uum_profiles
from tests.test_enrichment import payload
from tests.test_enrichment_pipeline import setup
from tests.test_owner_review import operation
from tests.test_canonical_graph_pipeline import drain
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only


def prepare(p, *, classified=True):
    register_uum_profiles(p['repo'])
    service, context, policy = setup(p); service.uum = True
    data = dict(payload('Je veux dormir sept heures. Je préfère une soirée calme.'), extraction_mode='semantic')
    items = [dict(text='Dormir sept heures', primary_dimension='objectives_intentions', assignment_certainty='asserted', evidence=[{'quote': 'Je veux dormir sept heures.'}]),
             dict(text='Préférer une soirée calme', primary_dimension='constraints_preferences', assignment_certainty='tentative', evidence=[{'quote': 'Je préfère une soirée calme.'}])]
    if not classified:
        for item in items: item['primary_dimension'] = None; item.pop('assignment_certainty')
    wire = dict(format=FORMAT, items=items)
    provider = Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps(wire)))))
    service.semantic_provider = provider
    return service, context, policy, data, wire


def submit(p, service, data, scope=None):
    return asyncio.run(service.enrich(p['repo'].subject_id, scope or p['scope'], data))


def browse(p, **filters):
    return asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,
        query=ContextBrowse(context_id=p['scope'], view=filters.pop('view', 'proposed'), **filters))))


def counts(p):
    with p['repo'].connect() as c:
        return [c.execute('SELECT count(*) n FROM '+name).fetchone()['n'] for name in ('sources','source_revisions','understanding_items','understanding_item_revisions','projection_outbox')]


def test_atomic_v3_exact_provenance_replay_graph_and_presence(generic):
    p=generic; service, context, policy, data, wire=prepare(p)
    result=submit(p,service,data);assert result['provider_mode']=='uum-simulated/3'
    drain(p['worker']); rows=browse(p).revisions
    assert len(rows)==2 and all(r.type_version==3 and r.structural_kind=='item' and r.validation_state=='proposed' for r in rows)
    assert {r.content['primary_dimension']['value'] for r in rows}=={'objectives_intentions','constraints_preferences'}
    assert all(r.current_revision_id is None and r.content['primary_dimension']['review_state']=='proposed' for r in rows)
    assert {r.content['extraction']['original_candidate']['text'] for r in rows}=={i['text'] for i in wire['items']}
    summary=asyncio.run(dimension_presence(context,p['repo'].subject_id,p['scope'],'proposed'))
    assert set(summary['dimensions'])==set(PRIMARY_DIMENSIONS)
    assert summary['dimensions']['objectives_intentions'] and not summary['dimensions']['situation_information']
    assert not summary['unclassified']
    assert len(browse(p,primary_dimension='objectives_intentions',limit=1).revisions)==1
    before=counts(p);assert submit(p,service,data)==dict(result,replayed=True)
    assert counts(p)==before and service.semantic_provider.generate.await_count==1
    # Same real projection worker rebuilds from canonical v3 data, with no provider.
    p['worker'].rebuild(p['scope']); assert len(browse(p).revisions)==2


@pytest.mark.parametrize('bad', ['unknown_dimension','human_state','bad_quote','duplicate_quote','foreign_source','indices','timeout','429'])
def test_invalid_batch_or_provider_failure_never_publishes_valid_siblings(generic,bad):
    p=generic;service,context,policy,data,wire=prepare(p)
    item=wire['items'][-1]
    if bad=='unknown_dimension': item['primary_dimension']='sleep'
    elif bad=='human_state':item['review_state']='accepted'
    elif bad=='bad_quote':item['evidence'][0]['quote']='Invented'
    elif bad=='duplicate_quote':data['turns'][0]['content']+=' Je préfère une soirée calme.'
    elif bad=='foreign_source':item['evidence'][0]['source_revision_id']=str(uuid4())
    elif bad=='indices':item['evidence_refs']=[0]
    if bad in ('timeout','429'):service.semantic_provider.generate.side_effect=TimeoutError(bad)
    else:service.semantic_provider.generate.return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(wire)))
    before=counts(p)
    with pytest.raises((ValueError,EnrichmentUnavailable)):submit(p,service,data)
    assert counts(p)==before and service.semantic_provider.generate.await_count==1


def test_owner_isolation_and_inactive_provider_before_generation(generic):
    p=generic;service,context,policy,data,wire=prepare(p);before=counts(p)
    with pytest.raises(ContextSpaceNotFound):submit(p,service,data,p['foreign'])
    assert service.semantic_provider.generate.await_count==0 and counts(p)==before
    service.semantic_provider=None
    with pytest.raises(EnrichmentUnavailable):submit(p,service,data)
    assert counts(p)==before


def test_review_primary_preserves_history_current_and_assignment_independence(generic):
    p=generic;service,context,policy,data,wire=prepare(p);submit(p,service,data);drain(p['worker'])
    original=browse(p,primary_dimension='objectives_intentions').revisions[0]
    review=ReviewService(context=context,policy=policy,repository=PostgresReviewRepository(url=p['repo'].url))
    def apply(row,action,**kwargs):
        op=operation({'id':row.revision_id},action,current=row.current_revision_id)
        op.update(kwargs)
        result=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],row.revision_id,op));drain(p['worker'])
        return browse(p,view='history',revision_id=result['revision_id']).revisions[0],op,result
    accepted,op,result=apply(original,'review_primary',primary_decision={'state':'accepted'})
    assert accepted.content['text']==original.content['text'] and accepted.provenance==original.provenance
    assert accepted.content['primary_dimension']==dict(original.content['primary_dimension'],review_state='accepted')
    assert accepted.validation_state=='proposed' and accepted.current_revision_id is None
    assert asyncio.run(review.apply(p['repo'].subject_id,p['scope'],original.revision_id,op))==dict(result,replayed=True)
    current,_,_=apply(accepted,'confirm')
    rejected,_,_=apply(current,'review_primary',primary_decision={'state':'rejected'})
    assert rejected.current_revision_id==current.revision_id and rejected.validation_state=='proposed'
    assert browse(p,view='current',primary_dimension='objectives_intentions').revisions[0].revision_id==current.revision_id
    assert browse(p,primary_unclassified=True,latest_pending=True).revisions[0].revision_id==rejected.revision_id
    replacement,_,_=apply(rejected,'review_primary',primary_decision={'state':'proposed','value':'open_questions','evidence_refs':[0]})
    assert replacement.content['primary_dimension']['review_state']=='proposed'
    assert replacement.content['primary_dimension']['certainty']=='tentative'
    assert browse(p,view='history',revision_id=original.revision_id).revisions[0].content==original.content
    corrected,_,_=apply(replacement,'correct',text='A corrected human proposition')
    assert 'primary_dimension' not in corrected.content


def test_unclassified_literal_and_zero_proposals_are_explicit(generic):
    p=generic;service,context,policy,data,wire=prepare(p)
    data.pop('extraction_mode');submit(p,service,data);drain(p['worker'])
    rows=browse(p,primary_unclassified=True).revisions
    assert len(rows)==1 and rows[0].type_version==3 and 'primary_dimension' not in rows[0].content
    assert service.semantic_provider.generate.await_count==0
    data=dict(payload('…'),extraction_mode='semantic')
    service.semantic_provider.generate.return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps({'format':FORMAT,'items':[]})))
    before=counts(p);result=submit(p,service,data)
    assert result['revision_ids']==[] and counts(p)==[before[0]+1,before[1]+1,*before[2:]]


def test_presence_clears_on_graph_outage_and_scope_change(generic):
    p=generic;service,context,policy,data,wire=prepare(p)
    # Even the empty result establishes freshness, not SQL-only absence.
    original=p['projector'].markers
    p['projector'].markers=lambda scopes: (_ for _ in ()).throw(RuntimeError('offline'))
    with pytest.raises(ContextRetrievalUnavailable):asyncio.run(dimension_presence(context,p['repo'].subject_id,p['scope'],'proposed'))
    p['projector'].markers=original
    with pytest.raises(ContextSpaceNotFound):asyncio.run(dimension_presence(context,p['repo'].subject_id,p['foreign'],'proposed'))


def test_primary_filter_intersects_before_limit_and_keyset(generic):
    p=generic;service,context,policy,data,wire=prepare(p);submit(p,service,data);drain(p['worker'])
    row=browse(p,primary_dimension='objectives_intentions').revisions[0]
    snapshot=p['repo'].read_snapshot((p['scope'],))['understanding_item_revisions']
    template=deepcopy(next(r for r in snapshot if r['id']==row.revision_id))
    clones=[]
    for i in range(23):
        clone=deepcopy(template);clone.update(id=str(uuid4()),item_id=str(uuid4()));clone.pop('created_at');clone.pop('current_revision_id');clones.append(clone)
    p['repo'].save(revisions=clones);drain(p['worker'])
    cursor=None;ids=[]
    while True:
        page=browse(p,primary_dimension='objectives_intentions',limit=3,after_revision_id=cursor)
        ids += [r.revision_id for r in page.revisions];cursor=page.next_after_revision_id
        if not cursor:break
    assert len(ids)==24 and len(set(ids))==24


def test_optional_open_metadata_reuses_assignment_review_without_becoming_primary(generic):
    p=generic;service,context,policy,data,wire=prepare(p);submit(p,service,data);drain(p['worker'])
    row=deepcopy(p['repo'].read_snapshot((p['scope'],))['understanding_item_revisions'][0])
    row.update(id=str(uuid4()),item_id=str(uuid4()))
    row.pop('created_at');row.pop('current_revision_id')
    row['content']['descriptors']=[dict(dimension='thematic',value='Sujet ouvert propre au Space',
        certainty='tentative',evidence_refs=[0],review_state='proposed')]
    p['repo'].save(revisions=[row]);drain(p['worker'])
    review=ReviewService(context=context,policy=policy,repository=PostgresReviewRepository(url=p['repo'].url))
    op=operation(row,'review_assignments',assignment_decisions=[{'index':0,'state':'accepted'}])
    receipt=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],row['id'],op));drain(p['worker'])
    result=browse(p,view='history',revision_id=receipt['revision_id']).revisions[0]
    assert result.content['descriptors'][0]['review_state']=='accepted'
    assert result.content['primary_dimension']==row['content']['primary_dimension']
