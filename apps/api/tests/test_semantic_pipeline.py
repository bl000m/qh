"""QH-51 atomic semantic proposals on real disposable SQL/Neo4j, never live QH."""
import asyncio
from copy import deepcopy
from unittest.mock import Mock
from uuid import uuid4

import pytest

from adapters.llm.offline import FixtureUnderstandingProvider
from adapters.postgres.semantic_profiles import register_semantic_profiles, generic_definitions
from app.core.models import ContextBrowse, ContextRequest, ContextSpaceNotFound
from app.understanding.enrichment import EnrichmentUnavailable
from tests.test_enrichment import payload
from tests.test_enrichment_pipeline import setup
from tests.test_generic_semantics import generic as generic
from tests.test_canonical_graph_pipeline import drain
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only

CASES = (
    ('Je veux dormir sept heures et garder une soirée calme.',
     [('Retrouver sept heures de sommeil', ['Sommeil', 'Habitudes de vie'], 'objectif'),
      ('Préserver une soirée calme', ['Habitudes de vie'], 'décision')]),
    ('Nous voulons isoler les données personnelles. La livraison dépend d’un audit.',
     [('Isoler les données personnelles de l’API', ['Architecture', 'Protection des données'], 'objectif'),
      ('Soumettre la livraison à un audit', ['Livraison'], 'contrainte')]),
)


def semantic(p, case):
    text, atoms = CASES[case]
    data = dict(payload(text), extraction_mode='semantic')
    items = [dict(local_id=str(index), shape='item', text=meaning,
        descriptors=[*[dict(dimension='thematic',value=t,certainty='tentative',evidence_refs=[0]) for t in themes],
            dict(dimension='semantic_role',value=role,certainty='asserted',evidence_refs=[0])],
        evidence=[dict(turn_id=data['turns'][0]['id'], quote=text)])
        for index,(meaning,themes,role) in enumerate(atoms)]
    service, context, policy = setup(p)
    service.semantic_provider = FixtureUnderstandingProvider(items)
    return service, data


def submit(p, service, data, scope=None):
    return asyncio.run(service.enrich(p['repo'].subject_id,scope or p['scope'],data))


def browse(p, **filters):
    return asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,
        query=ContextBrowse(context_id=p['scope'],view='proposed',**filters))))


def counts(p):
    with p['repo'].connect() as c:
        return [c.execute('SELECT count(*) AS n FROM '+name).fetchone()['n'] for name in
                ('sources','source_revisions','understanding_items','understanding_item_revisions','projection_outbox')]


@pytest.mark.parametrize('case', [0,1])
def test_real_semantic_atomicity_evidence_profiles_reopen_and_replay(generic, case):
    p=generic;before_profiles=deepcopy(generic_definitions());register_semantic_profiles(p['repo'])
    assert generic_definitions()==before_profiles
    service, data=semantic(p,case);result=submit(p,service,data)
    assert len(result['revision_ids'])==2 and result['provider_mode']=='semantic-simulated/2'
    calls=service.semantic_provider.calls
    drain(p['worker']);rows=browse(p,latest_pending=True).revisions
    assert len(rows)==2 and all(r.validation_state=='proposed' and r.type_version==2 and r.validated_by is None for r in rows)
    with p['repo'].connect() as c:
        source=c.execute('SELECT content,origin FROM source_revisions WHERE id=%s',(result['source_revision_id'],)).fetchone()
    for row in rows:
        assert row.content['text']!=data['turns'][0]['content']
        for d in row.content['descriptors']:
            for index in d['evidence_refs']:
                cite=row.content['citations'][index]
                assert cite['source_revision_id']==result['source_revision_id']
                assert source['content'][cite['start']:cite['end']]==cite['quote']==data['turns'][0]['content']
    first=CASES[case][1][0][1]
    for theme in first:
        page=browse(p,descriptor_dimension='thematic',descriptor=theme,include_tentative=True,latest_pending=True)
        assert any(r.content['text']==CASES[case][1][0][0] for r in page.revisions)
    assert not browse(p,descriptor_dimension='thematic',descriptor='objectif',include_tentative=True).revisions
    assert len(browse(p,descriptor_dimension='semantic_role',descriptor='objectif').revisions)==1
    prior=counts(p);assert submit(p,service,data)==dict(result,replayed=True)
    assert counts(p)==prior and service.semantic_provider.calls==calls
    # A reopened service returns the durable receipt, without re-extracting.
    reopened,_=semantic(p,case);assert submit(p,reopened,data)==dict(result,replayed=True)
    assert reopened.semantic_provider.calls==0


def test_foreign_scope_and_inactive_semantic_mode_never_call_or_fall_back(generic):
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0);prior=counts(p)
    service.provider=Mock(generate=Mock(side_effect=AssertionError('Literal fallback forbidden')))
    with pytest.raises(ContextSpaceNotFound):submit(p,service,data,p['foreign'])
    assert service.semantic_provider.calls==0 and counts(p)==prior
    service.semantic_provider=None
    with pytest.raises(EnrichmentUnavailable):submit(p,service,data)
    assert counts(p)==prior


@pytest.mark.parametrize('bad', ['evidence','dimension','index','review_spoof','duplicates'])
def test_invalid_sibling_leaves_no_partial_source_batch_or_outbox(generic, bad):
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    item=service.semantic_provider.items[-1]
    if bad=='evidence':item['evidence'][0]['quote']='A false invented quotation'
    elif bad=='dimension':item['descriptors'][0]['dimension']='objective'
    elif bad=='index':item['descriptors'][0]['evidence_refs']=[99]
    elif bad=='review_spoof':item['descriptors'][0]['review_state']='accepted'
    else:item['descriptors'].append(dict(item['descriptors'][0],certainty='asserted'))
    prior=counts(p)
    with pytest.raises(ValueError):submit(p,service,data)
    assert counts(p)==prior and service.semantic_provider.calls==1


def test_dimension_and_pending_filters_intersect_before_limit_and_keyset(generic):
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    submit(p,service,data);drain(p['worker'])
    page=browse(p,limit=1,descriptor_dimension='thematic',include_tentative=True,latest_pending=True)
    assert len(page.revisions)==1 and page.next_after_revision_id
    next_page=browse(p,limit=1,after_revision_id=page.next_after_revision_id,
                    descriptor_dimension='thematic',include_tentative=True,latest_pending=True)
    assert len(next_page.revisions)==1 and not next_page.next_after_revision_id
    assert next_page.revisions[0].revision_id!=page.revisions[0].revision_id
    assert not browse(p,descriptor_dimension='semantic_role',descriptor='Habitudes de vie',include_tentative=True).revisions


def test_selective_review_preserves_text_certainty_source_and_independent_confirmation(generic):
    from adapters.postgres.review import PostgresReviewRepository
    from app.review.service import ReviewService, ReviewConflict
    from tests.test_owner_review import operation
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    result=submit(p,service,data);drain(p['worker'])
    row=next(r for r in browse(p).revisions if len(r.content['descriptors'])==3)
    review=ReviewService(context=service.context,policy=service.policy,repository=PostgresReviewRepository(url=p['repo'].url))
    op=operation({'id':row.revision_id},'review_assignments',assignment_decisions=[dict(index=0,state='rejected')])
    receipt=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],row.revision_id,op));drain(p['worker'])
    updated=next(r for r in browse(p,latest_pending=True).revisions if r.item_id==row.item_id)
    assert updated.revision_id==receipt['revision_id'] and updated.validation_state=='proposed'
    assert updated.content['text']==row.content['text'] and updated.provenance==row.provenance
    assert updated.content['descriptors'][0]==dict(row.content['descriptors'][0],review_state='rejected')
    assert updated.content['descriptors'][1:]==row.content['descriptors'][1:]
    assert updated.current_revision_id is None and updated.validated_by is None and updated.origin_kind=='ai'
    assert not browse(p,descriptor='Sommeil',descriptor_dimension='thematic',include_tentative=True,latest_pending=True).revisions
    assert asyncio.run(review.apply(p['repo'].subject_id,p['scope'],row.revision_id,op))==dict(receipt,replayed=True)
    changed=dict(op,operation_id=str(uuid4()))
    with pytest.raises(ReviewConflict):asyncio.run(review.apply(p['repo'].subject_id,p['scope'],row.revision_id,changed))
    confirmed_op=operation({'id':updated.revision_id},'confirm')
    confirmed=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],updated.revision_id,confirmed_op));drain(p['worker'])
    current=asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,query=ContextBrowse(context_id=p['scope'],view='current')))).revisions[0]
    assert current.revision_id==confirmed['revision_id'] and current.validation_state=='confirmed'
    assert current.content['descriptors'][1]['review_state']=='proposed'  # Not accepted by item confirmation.
    op2=operation({'id':current.revision_id},'review_assignments',current=current.revision_id,assignment_decisions=[dict(index=1,state='accepted')])
    later=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],current.revision_id,op2));drain(p['worker'])
    assert next(r for r in browse(p,latest_pending=True).revisions if r.item_id==row.item_id).current_revision_id==current.revision_id
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) AS n FROM sources').fetchone()['n']==1
        assert c.execute('SELECT content FROM understanding_item_revisions WHERE id=%s',(row.revision_id,)).fetchone()['content']==row.content


def test_conservative_name_candidate_requires_exact_owned_name_and_explicit_review(generic):
    from adapters.postgres.review import PostgresReviewRepository
    from app.review.service import ReviewService
    from tests.test_owner_review import operation
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0);submit(p,service,data);drain(p['worker'])
    second=dict(payload('Je conserve cet objectif de sommeil.'),extraction_mode='semantic')
    item=dict(local_id='new',shape='item',text='Conserver cet objectif',descriptors=[dict(dimension='thematic',value='Repos nocturne',certainty='tentative',evidence_refs=[0],name_candidate='Sommeil')],evidence=[dict(turn_id=second['turns'][0]['id'],quote=second['turns'][0]['content'])])
    service.semantic_provider=FixtureUnderstandingProvider([item]);result=submit(p,service,second);drain(p['worker'])
    assert not browse(p,descriptor_dimension='thematic',descriptor='Repos nocturne',include_tentative=True).revisions
    review=ReviewService(context=service.context,policy=service.policy,repository=PostgresReviewRepository(url=p['repo'].url))
    op=operation({'id':result['revision_ids'][0]},'review_assignments',assignment_decisions=[dict(index=0,state='accepted',reuse_value='Sommeil')])
    receipt=asyncio.run(review.apply(p['repo'].subject_id,p['scope'],result['revision_ids'][0],op));drain(p['worker'])
    row=next(r for r in browse(p,descriptor_dimension='thematic',descriptor='Sommeil',include_tentative=True,latest_pending=True).revisions if r.revision_id==receipt['revision_id'])
    assert row.content['descriptors'][0]['value']=='Sommeil' and 'name_candidate' not in row.content['descriptors'][0]
    assert row.content['descriptors'][0]['certainty']=='tentative' and row.validation_state=='proposed'
    third=dict(payload('Je conserve cet objectif de sommeil.'),extraction_mode='semantic')
    service.semantic_provider=FixtureUnderstandingProvider([dict(item,descriptors=[dict(item['descriptors'][0],name_candidate='Foreign-only theme')],evidence=[dict(turn_id=third['turns'][0]['id'],quote=third['turns'][0]['content'])])])
    prior=counts(p)
    with pytest.raises(ValueError):submit(p,service,third)
    assert counts(p)==prior


@pytest.mark.parametrize('failure', [TimeoutError('timeout'),RuntimeError('429'),ValueError('invalid JSON')])
def test_semantic_provider_failure_is_single_attempt_no_literal_fallback_or_writes(generic, failure):
    from app.understanding.enrichment import EnrichmentUnavailable
    from unittest.mock import AsyncMock
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    service.semantic_provider=Mock(generate=AsyncMock(side_effect=failure))
    service.provider=Mock(generate=AsyncMock(side_effect=AssertionError('No fallback')))
    prior=counts(p)
    with pytest.raises((EnrichmentUnavailable,ValueError)):submit(p,service,data)
    assert counts(p)==prior and service.semantic_provider.generate.await_count==1
    assert service.provider.generate.await_count==0


def test_repository_guard_rejects_semantic_index_outside_citations_atomically(generic):
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0);submit(p,service,data);drain(p['worker'])
    rows=p['repo'].read_snapshot((p['scope'],))['understanding_item_revisions']
    siblings=[]
    for row in rows:
        clone=deepcopy(row);clone.update(id=str(uuid4()),item_id=str(uuid4()),revision_no=1)
        clone.pop('created_at',None);clone.pop('current_revision_id',None);siblings.append(clone)
    siblings[-1]['content']['descriptors'][0]['evidence_refs']=[99]
    prior=counts(p)
    with pytest.raises(ValueError):p['repo'].save(revisions=siblings)
    assert counts(p)==prior


def test_semantic_api_caps_query_review_and_foreign_owner_fail_closed(generic):
    from fastapi.testclient import TestClient
    from app.api.security import SecurityBindings
    from app.composition import ApplicationServices
    from app.main import create_app
    from app.review.service import ReviewService
    from adapters.postgres.review import PostgresReviewRepository
    from tests.test_owner_review import operation
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    result=submit(p,service,data);drain(p['worker']);owner=p['repo'].subject_id
    review=ReviewService(context=service.context,policy=service.policy,repository=PostgresReviewRepository(url=p['repo'].url))
    async def auth(token):return owner if token=='alice' else str(uuid4())
    app=create_app(services=ApplicationServices(context=service.context,policy=service.policy,enrichment=service,review=review),security=SecurityBindings(authenticate=auth,policy=service.policy))
    base='/context-spaces/'+p['scope'];headers={'Authorization':'Bearer alice'}
    with TestClient(app) as client:
        assert client.get(base+'/enrichments/capabilities',headers=headers).json()==dict(literal=True,semantic=True,provider_mode='semantic-simulated/2',external_disclosure=False)
        for path in ['/enrichments/capabilities','/understanding?view=proposed&descriptor_dimension=thematic&include_tentative=true&latest_pending=true']:
            assert client.get(base+path,headers={'Authorization':'Bearer bob'}).status_code==404
        selected=client.get(base+'/understanding?view=proposed&descriptor_dimension=thematic&descriptor=Sommeil&include_tentative=true&latest_pending=true&limit=1',headers=headers)
        assert selected.status_code==200 and len(selected.json()['items'])==1
        row=selected.json()['items'][0];op=operation({'id':row['revision_id']},'review_assignments',assignment_decisions=[dict(index=0,state='rejected')])
        path=base+'/understanding/'+row['revision_id']+'/review'
        prior=counts(p)
        assert client.post(path,headers={'Authorization':'Bearer bob'},json=op).status_code==404
        assert client.post(path,headers=headers,json=dict(op,actor_id=owner)).status_code==422
        bad=dict(op,assignment_decisions=[dict(index=True,state='accepted')]);assert client.post(path,headers=headers,json=bad).status_code==422
        assert counts(p)==prior
        response=client.post(path,headers=headers,json=op);assert response.status_code==200
        assert response.json()['action']=='review_assignments'


def test_graph_unavailable_prevents_semantic_disclosure_even_for_empty_vocabulary(generic):
    from app.core.models import ContextRetrievalUnavailable
    from unittest.mock import AsyncMock
    p=generic;register_semantic_profiles(p['repo']);service,data=semantic(p,0)
    service.context.browse=AsyncMock(side_effect=ContextRetrievalUnavailable('unavailable'))
    prior=counts(p)
    with pytest.raises(ContextRetrievalUnavailable):submit(p,service,data)
    assert service.semantic_provider.calls==0 and counts(p)==prior


def test_two_space_fixture_evaluation_separates_semantics_themes_evidence_and_vocabulary(generic):
    import json
    from adapters.context.incremental import ProjectionWorker
    from tests.semantic_fixtures import ExactSemanticFixtureProvider, WELLBEING, PROFESSIONAL
    p=generic;register_semantic_profiles(p['repo']);service,context,policy=setup(p)
    provider=ExactSemanticFixtureProvider();service.semantic_provider=provider
    worker=ProjectionWorker(p['repo'],p['projector'],(p['scope'],p['sibling']))
    gold={
        'Retrouver sept heures de sommeil':({'Sommeil','Habitudes de vie'},'objectif'),
        'Choisir une marche douce après le déjeuner':({'Activité physique','Habitudes de vie'},'décision'),
        'Réduire les écrans pourrait faciliter l’endormissement':({'Sommeil','Habitudes de vie'},'hypothèse'),
        'Examiner l’effet de la marche sur l’énergie':({'Activité physique','Énergie'},'question ouverte'),
        'Isoler les données personnelles par service':({'Architecture','Protection des données'},'objectif'),
        'Choisir PostgreSQL comme stockage canonique':({'Architecture','Données persistantes'},'décision'),
        'Subordonner la livraison à un audit de sécurité':({'Livraison','Protection des données'},'contrainte'),
        'Déterminer le niveau de disponibilité à garantir':({'Fiabilité'},'question ouverte'),
    }
    rows=[];scope_themes=[]
    for scope,texts in [(p['scope'],WELLBEING),(p['sibling'],PROFESSIONAL)]:
        submit(p,service,dict(payload(*texts),extraction_mode='semantic'),scope);drain(worker)
        page=asyncio.run(p['service'].browse(ContextRequest(subject_id=p['repo'].subject_id,query=ContextBrowse(context_id=scope,view='proposed',latest_pending=True))))
        rows.extend(page.revisions)
        scope_themes.append({d['value'] for r in page.revisions for d in r.content['descriptors'] if d['dimension']=='thematic'})
    assert scope_themes[0].isdisjoint(scope_themes[1])
    assert provider.requests[0]['known_themes']==provider.requests[1]['known_themes']==[]
    matched=role_matches=themes_generated=themes_correct=evidence_matches=0
    for row in rows:
        reference=gold[row.content['text']];matched+=1
        themes={d['value'] for d in row.content['descriptors'] if d['dimension']=='thematic'}
        roles={d['value'] for d in row.content['descriptors'] if d['dimension']=='semantic_role'}
        themes_generated+=len(themes);themes_correct+=len(themes&reference[0]);role_matches+=reference[1] in roles
        sources=p['repo'].read_sources((row.context_space_id,),(row.provenance[0].source_revision_id,))
        for cite in row.content['citations']:
            evidence_matches+=sources[0]['content'][cite['start']:cite['end']]==cite['quote']
    metrics=dict(mode='hand_authored_fixture_conformance_not_model_quality',atomic_reference_matches=matched,atomic_reference_count=len(gold),role_matches=role_matches,
        theme_correct_assignments=themes_correct,theme_generated_assignments=themes_generated,theme_reference_assignments=sum(len(g[0]) for g in gold.values()),
        exact_evidence_matches=evidence_matches,evidence_count=sum(len(r.content['citations']) for r in rows),distinct_space_themes=True,foreign_vocabulary_disclosed=False,
        real_provider_semantic_quality='NOT TESTED',name_reuse_quality='NOT TESTED on a real provider; explicit same-Space reuse/foreign-name rejection tested separately')
    assert matched==role_matches==8 and themes_correct==15 and themes_generated==16 and evidence_matches==8
    print('QH51_METRICS '+json.dumps(metrics,sort_keys=True))
