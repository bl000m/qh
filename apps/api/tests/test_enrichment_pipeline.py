"""QH-39 real SQL/outbox/graph/review; exclusively disposable fixtures."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.llm.offline import LiteralSegmentProvider, FixtureUnderstandingProvider
from adapters.postgres.enrichment import PostgresEnrichmentRepository
from adapters.postgres.review import PostgresReviewRepository
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.spaces import PostgresContextSpaceRepository
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.context.service import ManagedContextService
from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound, ContextRetrievalUnavailable
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.review.service import ReviewService
from app.understanding.enrichment import ConversationEnrichment, EnrichmentConflict
from app.understanding.extractor import UnderstandingExtractor
from tests.test_enrichment import payload
from tests.test_generic_semantics import generic as generic
from tests.test_canonical_graph_pipeline import drain
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_understanding_pipeline import counts


def setup(p, provider=None):
    policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=p['repo'].url).owner_for)
    context=ManagedContextService(repository=PostgresContextSpaceRepository(url=p['repo'].url),
        policy=policy,retrieval_for=lambda subject:p['service'])
    def repository(subject):
        return PostgresEnrichmentRepository(url=p['repo'].url,subject_id=subject)
    enrich=ConversationEnrichment(context=context,policy=policy,repository_for=repository,
        provider=provider or LiteralSegmentProvider())
    return enrich,context,policy


def submit(p,service,data):
    return asyncio.run(service.enrich(p['repo'].subject_id,p['scope'],data))


def browse(p,view):
    return asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,
        query=ContextBrowse(context_id=p['scope'],view=view))))


def test_atomic_publish_reopen_review_and_derived_graph_rebuild(generic):
    p=generic;service,context,policy=setup(p);data=payload('Notre décision reste un essai, pas un achat. 🌱')
    result=submit(p,service,data)
    assert len(result['revision_ids'])==1
    with p['repo'].connect() as c:
        row=c.execute('SELECT * FROM understanding_item_revisions WHERE id=%s',(result['revision_ids'][0],)).fetchone()
        assert row['validation_state']=='proposed' and row['validated_by'] is None
        assert c.execute('SELECT current_revision_id FROM understanding_items WHERE id=%s',(row['item_id'],)).fetchone()['current_revision_id'] is None
        source=c.execute('SELECT content,origin FROM source_revisions WHERE id=%s',(result['source_revision_id'],)).fetchone()
        assert source['origin']['metadata']['submitted_by']==p['repo'].subject_id
        ref=row['content']['citations'][0]
        assert source['content'][ref['start']:ref['end']]==ref['quote']==data['turns'][0]['content']
    drain(p['worker'])
    assert [r.revision_id for r in browse(p,'proposed').revisions]==result['revision_ids']
    assert not browse(p,'current').revisions
    # New service/repository object represents a reopened session/process. Replay
    # derives the durable receipt from canonical source/provenance, no memory cache.
    provider=Mock(generate=AsyncMock(side_effect=AssertionError('no inference on replay')))
    reopened,_,_=setup(p,provider)
    assert submit(p,reopened,data)==dict(result,replayed=True)
    provider.generate.assert_not_awaited()
    changed=deepcopy(data);changed['turns'][0]['content']='Changed immutable segment'
    with pytest.raises(EnrichmentConflict):submit(p,reopened,changed)
    review=ReviewService(context=context,policy=policy,repository=PostgresReviewRepository(url=p['repo'].url))
    revision=result['revision_ids'][0]
    op=dict(operation_id=str(uuid4()),action='confirm',expected_latest_revision_id=revision,
        expected_current_revision_id=None,text=None)
    confirmed=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],revision,op));drain(p['worker'])
    assert [r.revision_id for r in browse(p,'current').revisions]==[confirmed['revision_id']]
    assert len(browse(p,'history').revisions)==2
    # Rebuild the derived namespace from canonical SQL; IDs/evidence survive.
    p['worker'].rebuild(p['scope'])
    assert browse(p,'current').revisions[0].revision_id==confirmed['revision_id']


def test_real_api_owner_before_lookup_unknown_fields_and_no_foreign_disclosure(generic):
    p=generic;provider=Mock(wraps=LiteralSegmentProvider());service,context,policy=setup(p,provider)
    async def auth(token):return p['repo'].subject_id if token=='alice' else str(uuid4())
    app=create_app(services=ApplicationServices(context=context,policy=policy,enrichment=service),
        security=SecurityBindings(authenticate=auth,policy=policy))
    data=payload();path='/context-spaces/'+p['scope']+'/enrichments'
    with TestClient(app) as client:
        assert client.post(path,json=data).status_code==401
        for scope in (p['scope'],str(uuid4())):
            assert client.post('/context-spaces/'+scope+'/enrichments',headers={'Authorization':'Bearer bob'},json=data).status_code==404
        provider.generate.assert_not_called()
        headers={'Authorization':'Bearer alice'}
        assert client.post(path,headers=headers,json=dict(data,owner_id=p['repo'].subject_id)).status_code==422
        response=client.post(path,headers=headers,json=data)
        assert response.status_code==200 and response.headers['Cache-Control']=='private, no-store'
    drain(p['worker'])
    with pytest.raises(ContextSpaceNotFound):
        asyncio.run(service.enrich(str(uuid4()),p['scope'],data))


def test_failed_batch_and_database_constraints_leave_no_source_or_outbox(generic):
    p=generic;service,_,_=setup(p);data=payload()
    # Prepare using the SAME Engine, then intentionally violate a deferred SQL
    # profile binding to prove the actual transaction rolls back source + items.
    conversation=dict(id='synthetic-invalid',revision_no=1,acquired_at='2026-10-19T00:00:00Z',
        turns=[dict(id=data['turns'][0]['id'],speaker='user (owner-declared)',text='Bounded test.')],metadata={})
    engine=UnderstandingExtractor(repository=p['repo'],policy=p['service'].policy,provider=LiteralSegmentProvider())
    source,rows=asyncio.run(engine.propose_conversation(subject_id=p['repo'].subject_id,
        context_id=p['scope'],conversation=conversation,extraction_key='test'))
    rows[0]['type_id']='unregistered.invalid'
    repo=PostgresEnrichmentRepository(url=p['repo'].url,subject_id=p['repo'].subject_id)
    before=counts(p['repo'])
    with pytest.raises(EnrichmentConflict):
        asyncio.run(repo.publish(p['scope'],source,rows,'fingerprint'))
    assert counts(p['repo'])==before


def test_concurrent_duplicate_publication_is_single_immutable_batch(generic):
    p=generic;data=payload();service,_,_=setup(p)
    source,rows=asyncio.run(UnderstandingExtractor(repository=p['repo'],policy=p['service'].policy,
        provider=LiteralSegmentProvider()).propose_conversation(subject_id=p['repo'].subject_id,
        context_id=p['scope'],extraction_key='qh39-selected-segment/1-resolved',
        conversation=dict(id='same-segment',revision_no=1,acquired_at='2026-10-19T00:00:00Z',
            turns=[dict(id=data['turns'][0]['id'],speaker='user (owner-declared)',text='Unique decision.')],
            metadata=dict(submission_kind='owner_selected_browser_segment',submitted_by=p['repo'].subject_id,request_sha256='same'))))
    def publish(_):
        repo=PostgresEnrichmentRepository(url=p['repo'].url,subject_id=p['repo'].subject_id)
        return asyncio.run(repo.publish(p['scope'],source,rows,'same'))
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(publish,range(2)))
    assert sorted(r['replayed'] for r in results)==[False,True]
    assert results[0]['revision_ids']==results[1]['revision_ids']
    assert counts(p['repo'])['source_revisions']==1 and counts(p['repo'])['understanding_item_revisions']==1


def test_provider_structured_relations_citations_and_empty_results_use_same_engine(generic):
    p=generic;data=payload('Mina propose un pilote à Jo.')
    turn=data['turns'][0]['id'];quote=data['turns'][0]['content']
    def item(local,shape,text):return dict(local_id=local,shape=shape,text=text,
        evidence=[dict(turn_id=turn,quote=quote)])
    left=item('proposal','item','Mina propose un pilote à Jo.');right=item('person','entity','Mina')
    relation=item('rel','relation','Proposition déclarée par Mina.')
    relation['relation']=dict(source='proposal',target='person',predicate='stated_by')
    service,_,_=setup(p,FixtureUnderstandingProvider([left,right,relation]))
    result=submit(p,service,data);drain(p['worker'])
    revisions=browse(p,'proposed').revisions;assert len(revisions)==3
    r=next(r for r in revisions if r.relation)
    assert r.relation.source_revision_id in result['revision_ids'] and r.relation.target_revision_id in result['revision_ids']
    assert all(r.provenance[0].source_revision_id==result['source_revision_id'] for r in revisions)
    other=payload('Selected assistant utterance');other['turns'][0]['role']='assistant'
    empty,_,_=setup(p);receipt=submit(p,empty,other)
    assert receipt['revision_ids']==[] and counts(p['repo'])['source_revisions']==2


def test_stale_graph_and_missing_scope_do_not_publish(generic):
    p=generic;service,_,_=setup(p);result=submit(p,service,payload('A new unprojected claim.'))
    before=counts(p['repo'])
    with pytest.raises(ContextRetrievalUnavailable):submit(p,service,payload('Another claim while stale.'))
    assert counts(p['repo'])==before
    drain(p['worker'])
    with p['projector'].driver.session() as session:
        session.run('MATCH (r:QH30Revision {slice_id:$key,revision_id:$id}) DETACH DELETE r',
            key=p['projector'].key(p['scope']),id=result['revision_ids'][0]).consume()
    with pytest.raises(ContextRetrievalUnavailable):submit(p,service,payload('Must not bypass damaged graph.'))
    assert counts(p['repo'])==before
