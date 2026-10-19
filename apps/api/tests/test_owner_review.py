"""Owner review on disposable SQL/Neo4j only; no live demo mutation."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from adapters.postgres.review import PostgresReviewRepository
from adapters.postgres.security import PostgresSecurityReader
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.core.models import ContextBrowse, ContextRequest
from app.context.service import ManagedContextService
from adapters.postgres.spaces import PostgresContextSpaceRepository
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.review.service import ReviewService, ReviewConflict
from tests.test_generic_semantics import generic as generic, revision
from tests.test_canonical_graph_pipeline import drain
from tests.test_native_context import real_engine as real_engine
from tests.test_migrations import empty_database as empty_database
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only


def prepared(p):
    base = revision(p, 'An uncertain pilot', descriptors=['hypothesis'])
    p['repo'].save(sources=(p['source'],), revisions=(base,))
    drain(p['worker'])
    return base


def operation(base, action, current=None, latest=None, **extra):
    return dict(operation_id=str(uuid4()), action=action,
        expected_latest_revision_id=latest or base['id'], expected_current_revision_id=current, text=None, **extra)


def repo(p): return PostgresReviewRepository(url=p['repo'].url)


def apply(p, base, op):
    return asyncio.run(repo(p).apply(p['repo'].subject_id, p['scope'], base['id'], op))


def test_confirm_atomic_pointer_origin_provenance_and_replay(generic):
    p=generic; base=prepared(p); op=operation(base, 'confirm')
    result=apply(p,base,op)
    with p['repo'].connect() as c:
        current=c.execute('SELECT current_revision_id FROM understanding_items WHERE id=%s',(base['item_id'],)).fetchone()['current_revision_id']
        row=c.execute('SELECT * FROM understanding_item_revisions WHERE id=%s',(result['revision_id'],)).fetchone()
        assert str(current)==result['revision_id'] and row['validation_state']=='confirmed'
        assert row['origin_kind']=='ai' and str(row['validated_by'])==p['repo'].subject_id
        assert row['content']['text']==base['content']['text']
        assert str(row['based_on_revision_id'])==base['id']
        assert c.execute('SELECT source_revision_id FROM item_revision_provenance WHERE item_revision_id=%s',(result['revision_id'],)).fetchone()['source_revision_id'] is not None
        assert c.execute('SELECT count(*) AS n FROM projection_outbox WHERE revision_id=%s',(result['revision_id'],)).fetchone()['n']==2
    assert apply(p,base,op)==dict(result,replayed=True)
    with pytest.raises(ReviewConflict):apply(p,base,dict(op,action='reject'))
    drain(p['worker'])
    page=asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,query=ContextBrowse(context_id=p['scope'],view='current'))))
    assert [r.revision_id for r in page.revisions]==[result['revision_id']]
    # Original proposed history remains; inbox instead excludes reviewed proposal.
    assert asyncio.run(repo(p).pending(p['repo'].subject_id,p['scope'],20,None))==[]
    page=asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,query=ContextBrowse(context_id=p['scope'],view='proposed'))))
    assert [r.revision_id for r in page.revisions]==[base['id']]


def test_correction_then_rejection_preserves_current_and_immutable_original(generic):
    p=generic;base=prepared(p); confirmed=apply(p,base,operation(base,'confirm'));drain(p['worker'])
    target=dict(base,id=confirmed['revision_id'])
    op=operation(target,'correct',current=target['id']);op['text']='A human correction, still uncertain'
    corrected=apply(p,target,op);drain(p['worker'])
    corrected_base=dict(base,id=corrected['revision_id'])
    rejected=apply(p,corrected_base,operation(corrected_base,'reject',current=target['id']));drain(p['worker'])
    with p['repo'].connect() as c:
        assert str(c.execute('SELECT current_revision_id FROM understanding_items WHERE id=%s',(base['item_id'],)).fetchone()['current_revision_id'])==target['id']
        original=c.execute('SELECT content,validation_state FROM understanding_item_revisions WHERE id=%s',(base['id'],)).fetchone()
        assert original==dict(content=base['content'],validation_state='proposed')
        row=c.execute('SELECT origin_kind,validation_state,validated_by FROM understanding_item_revisions WHERE id=%s',(corrected['revision_id'],)).fetchone()
        assert row==dict(origin_kind='human',validation_state='proposed',validated_by=None)
        assert c.execute('SELECT validation_state FROM understanding_item_revisions WHERE id=%s',(rejected['revision_id'],)).fetchone()['validation_state']=='rejected'


def test_competing_review_only_one_commits(generic):
    p=generic;base=prepared(p)
    def run(action):
        try:return apply(p,base,operation(base,action))['action']
        except ReviewConflict:return 'conflict'
    with ThreadPoolExecutor(2) as pool: results=list(pool.map(run,['confirm','reject']))
    assert results.count('conflict')==1
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) AS n FROM understanding_item_revisions WHERE item_id=%s',(base['item_id'],)).fetchone()['n']==2


def test_real_api_authorization_before_payload_access_and_graph_failure(generic):
    p=generic;base=prepared(p); owner=p['repo'].subject_id
    policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=p['repo'].url).owner_for)
    context=ManagedContextService(repository=PostgresContextSpaceRepository(url=p['repo'].url),policy=policy,retrieval_for=lambda subject:p['service'])
    review=ReviewService(context=context,policy=policy,repository=repo(p))
    async def auth(token):return owner if token=='alice' else str(uuid4())
    app=create_app(services=ApplicationServices(context=context,policy=policy,review=review),security=SecurityBindings(authenticate=auth,policy=policy))
    path='/context-spaces/'+p['scope']+'/understanding/'+base['id']+'/review'
    with TestClient(app) as client:
        assert client.get(path).status_code==401
        for method in ('get','post'):
            kwargs={'json':operation(base,'confirm')} if method=='post' else {}
            assert getattr(client,method)(path,headers={'Authorization':'Bearer bob'},**kwargs).status_code==404
        headers={'Authorization':'Bearer alice'}
        state=client.get(path,headers=headers)
        assert state.status_code==200 and state.json()['pending']
        inbox=client.get('/context-spaces/'+p['scope']+'/review',headers=headers)
        assert inbox.status_code==200 and len(inbox.json()['items'])==1
        assert client.post(path,headers=headers,json=dict(operation(base,'confirm'),owner_id=owner)).status_code==422
        op=operation(base,'confirm');op['expected_latest_revision_id']=str(uuid4())
        assert client.post(path,headers=headers,json=op).status_code==409
        # Actual graph namespace becomes unavailable; no SQL-only review bypass.
        with p['projector'].driver.session() as session:
            session.run('MATCH (r:QH30Revision {slice_id:$key,revision_id:$id}) DETACH DELETE r', key=p['projector'].key(p['scope']), id=base['id']).consume()
        assert client.post(path,headers=headers,json=operation(base,'confirm')).status_code==503
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) AS n FROM understanding_item_revisions').fetchone()['n']==1


def test_relation_anchors_temporal_bounds_and_partial_failure_are_preserved(generic):
    p=generic
    left=revision(p,'Left');right=revision(p,'Right',shape='entity')
    relation=revision(p,'Left was stated by Right',shape='relation')
    relation['relation']=dict(source_item_id=left['item_id'],source_revision_id=left['id'],target_item_id=right['item_id'],target_revision_id=right['id'],predicate='stated_by')
    relation['fact_from']='2026-10-19T00:00:00+00:00'
    p['repo'].save(sources=(p['source'],),revisions=(left,right,relation));drain(p['worker'])
    result=apply(p,relation,operation(relation,'confirm'));drain(p['worker'])
    with p['repo'].connect() as c:
        old=c.execute('SELECT * FROM relation_revision_details WHERE item_revision_id=%s',(relation['id'],)).fetchone()
        new=c.execute('SELECT * FROM relation_revision_details WHERE item_revision_id=%s',(result['revision_id'],)).fetchone()
        assert {k:v for k,v in old.items() if k!='item_revision_id'}=={k:v for k,v in new.items() if k!='item_revision_id'}
        assert c.execute('SELECT fact_from FROM item_revision_types WHERE item_revision_id=%s',(result['revision_id'],)).fetchone()['fact_from'].isoformat()==relation['fact_from']
    # A restrictive immutable profile that disallows review receipt metadata fails
    # atomically; neither weakening the schema nor dropping provenance is allowed.
    p['repo'].register_types([dict(type_id='test.strict.review',version=1,structural_kind='item',property_schema={'type':'object','properties':{'text':{'type':'string'}},'required':['text'],'additionalProperties':False})])
    strict=revision(p,'Strict payload');strict['type_id']='test.strict.review'
    p['repo'].save(revisions=(strict,));drain(p['worker'])
    with pytest.raises(ReviewConflict):apply(p,strict,operation(strict,'confirm'))
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) AS n FROM understanding_item_revisions WHERE item_id=%s',(strict['item_id'],)).fetchone()['n']==1
        assert c.execute('SELECT current_revision_id FROM understanding_items WHERE id=%s',(strict['item_id'],)).fetchone()['current_revision_id'] is None


def test_stale_sql_ownership_and_pending_projection_fail_closed(generic):
    p=generic;base=prepared(p)
    foreign_owner=None
    with p['repo'].connect() as c:
        foreign_owner=str(c.execute('SELECT owner_id FROM context_spaces WHERE id=%s',(p['foreign'],)).fetchone()['owner_id'])
    with pytest.raises(PermissionError):
        asyncio.run(repo(p).apply(foreign_owner,p['scope'],base['id'],operation(base,'confirm')))
    later=revision(p,'Another pending publication');p['repo'].save(revisions=(later,))
    from app.core.models import ContextRetrievalUnavailable
    with pytest.raises(ContextRetrievalUnavailable):apply(p,base,operation(base,'confirm'))
