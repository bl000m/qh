"""Real disposable SQL/Neo4j and UUM replay; never a real-provider acceptance claim."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
import json

from alembic import command
import psycopg
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.composition import ApplicationServices
from app.api.security import SecurityBindings

from adapters.postgres.consolidation import PostgresConsolidationRepository
from adapters.postgres.semantic_profiles import register_uum_profiles
from app.core.models import GenerationResult, Message, MessageRole, ContextSpaceNotFound, ContextRequest, ContextBrowse
from app.understanding.consolidation import ContextConsolidation
from app.understanding.enrichment import EnrichmentUnavailable
from tests.test_enrichment_pipeline import setup
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain
from tests.test_consolidation import document, consolidation_output, reference_replay


def run(operation):
    return asyncio.run(operation)


def prepare(p, config):
    command.upgrade(config,'0010_context_consolidation')
    register_uum_profiles(p['repo'])
    _,context,policy=setup(p)
    # Real Engine and exact-citation validation; provider is explicitly an offline replay.
    wire=dict(format='qh.atomic-understanding/1',items=[dict(text='Le responsable est Alice.',
        primary_dimension='situation_information',assignment_certainty='asserted',evidence=[dict(quote='Le responsable est Alice.')])])
    provider=Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(consolidation_output(wire))))))
    reference_replay(provider)
    ai=Mock(authorize_consolidation=AsyncMock(),_authorize=AsyncMock(),_provider=Mock(return_value=provider))
    repository=lambda subject:PostgresConsolidationRepository(url=p['repo'].url,subject_id=subject)
    service=ContextConsolidation(context=context,policy=policy,ai=ai,repository_for=repository)
    return service,SimpleNamespace(subject_id=p['repo'].subject_id),repository,provider


def test_atomic_consolidation_persistence_retry_correction_and_owner_isolation(generic,empty_database):
    p=generic;service,who,repositories,provider=prepare(p,empty_database);scope=p['scope'];row=document()
    run(service.append(who.subject_id,scope,row));run(service.append(who.subject_id,scope,row))
    assert run(service.read(who.subject_id,scope))['pending_count']==1
    saved=run(service.consolidate(who,scope));assert saved['current']['version']==1 and saved['pending_count']==0
    drain(p['worker'])
    reopened=ContextConsolidation(context=service.context,policy=service.policy,ai=service.ai,repository_for=repositories)
    state=run(reopened.read(who.subject_id,scope))
    assert state['recap']['version_id']==saved['current']['id']
    assert state['recap']['text'] and saved['current']['has_recap']
    assert state['understanding'][0]['validation_state']=='proposed'
    assert not state['understanding'][0]['is_current_confirmed']
    assert state['understanding'][0]['content']['citations'][0]['quote']==row['text']
    assert run(reopened.consolidate(who,scope))['current']==saved['current']
    assert provider.generate.await_count==1
    async def authenticate(token):
        return who.subject_id if token=='owner' else str(uuid4())
    app=create_app(services=ApplicationServices(context=service.context,policy=service.policy,consolidation=service),
        security=SecurityBindings(authenticate=authenticate,policy=service.policy))
    headers={'Authorization':'Bearer owner'}
    with TestClient(app) as client:
        base='/context-spaces/'+scope+'/workspace'
        exported=client.get(base+'/export',headers=headers)
        assert exported.status_code==200,exported.text
        assert exported.headers['cache-control']=='private, no-store'
        portable=exported.json()
        assert portable['understanding'][0]['validation_state']=='proposed'
        assert portable['understanding'][0]['evidence'][0]['quote']==row['text']
        sibling='/context-spaces/'+p['sibling']+'/workspace'
        imported=dict(document(),kind='context',text=None,context=portable)
        result=client.post(sibling+'/intake',headers=headers,json=imported)
        assert result.status_code==200,result.text
        assert result.json()['current'] is None and result.json()['pending_count']==1
        for suffix in ('','/export'):
            assert client.get(base+suffix,headers={'Authorization':'Bearer other'}).status_code==404
        assert client.post(sibling+'/intake',headers=headers,json=dict(imported,context={**portable,'token':'forbidden'})).status_code==422
    original=provider.generate.return_value
    imported_wire=dict(format='qh.atomic-understanding/1',items=[dict(text='Import non confirmé : Alice est responsable.',
        primary_dimension='situation_information',assignment_certainty='tentative',
        evidence=[dict(quote=json.dumps(portable, ensure_ascii=False, sort_keys=True))])])
    provider.generate.return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(consolidation_output(imported_wire))))
    other=run(service.consolidate(who,p['sibling']))
    from adapters.context.incremental import ProjectionWorker
    drain(ProjectionWorker(p['repo'],p['projector'],(p['sibling'],)))
    assert other['current']['version']==1
    with TestClient(app) as client:
        again=client.get(sibling+'/export',headers=headers)
        assert again.status_code==200,again.text
        assert again.json()['ancestry'][0]['logical_id']==scope
        assert again.json()['ancestry'][0]['understanding'][0]['id']==portable['understanding'][0]['id']
        assert again.json()['ancestry'][0]['understanding'][0]['evidence']==portable['understanding'][0]['evidence']
    provider.generate.return_value=original
    correction=document('Le responsable n’est plus Alice mais Bob.')
    run(service.append(who.subject_id,scope,correction))
    provider.generate.side_effect=TimeoutError('offline failure')
    with pytest.raises(TimeoutError):run(service.consolidate(who,scope))
    failed=run(service.read(who.subject_id,scope))
    assert failed['state']=='failed' and failed['pending_count']==1 and failed['current']==saved['current']
    provider.generate.side_effect=None
    before=p['repo'].read_snapshot((scope,))
    original_save=PostgresConsolidationRepository._save_on
    def failed_publication(repository,connection,**values):
        original_save(repository,connection,**values)
        raise ValueError('offline injected publication failure')
    with patch.object(PostgresConsolidationRepository,'_save_on',failed_publication):
        with pytest.raises(ValueError):run(service.consolidate(who,scope))
    assert p['repo'].read_snapshot((scope,))==before
    assert run(service.read(who.subject_id,scope))['current']==saved['current']
    latest=run(service.consolidate(who,scope));drain(p['worker'])
    assert latest['current']['version']==2 and len(latest['current']['intake_ids'])==2
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) n FROM context_consolidations WHERE context_space_id=%s',(scope,)).fetchone()['n']==2
        with pytest.raises(psycopg.errors.CheckViolation),c.transaction():
            c.execute('UPDATE context_consolidations SET version=10 WHERE id=%s',(saved['current']['id'],))
    for target in (p['foreign'],str(uuid4())):
        with pytest.raises(ContextSpaceNotFound):run(service.read(who.subject_id,target))
        with pytest.raises(ContextSpaceNotFound):run(service.append(who.subject_id,target,row))
    with pytest.raises(ContextSpaceNotFound):run(repositories(str(uuid4())).read(scope))


def test_competing_claims_are_serialized_before_provider_work(generic,empty_database):
    p=generic;service,who,repositories,_=prepare(p,empty_database);scope=p['scope']
    run(service.append(who.subject_id,scope,document()))
    def claim():
        try:return run(repositories(who.subject_id).claim(scope))
        except EnrichmentUnavailable:return None
    with ThreadPoolExecutor(max_workers=2) as pool:values=list(pool.map(lambda _:claim(),range(2)))
    assert sum(v is not None for v in values)==1


@pytest.mark.parametrize('generic', ['0005_retire_legacy_category'], indirect=True)
def test_exact_batch_keeps_graph_checks_and_rejects_cross_space_selection(generic, empty_database, monkeypatch):
    p = generic
    service, who, repositories, provider = prepare(p, empty_database)
    texts = ['Alice dirige le projet.', 'Bob gère le budget.']
    wire = dict(format='qh.atomic-understanding/1', items=[dict(text=text,
        primary_dimension='situation_information', assignment_certainty='asserted',
        evidence=[dict(quote=text)]) for text in texts])
    provider.generate.return_value = GenerationResult(message=Message(
        role=MessageRole.ASSISTANT, content=json.dumps(consolidation_output(wire))))
    versions = {}
    for scope in (p['scope'], p['sibling']):
        run(service.append(who.subject_id, scope, document(' '.join(texts))))
        versions[scope] = run(service.consolidate(who, scope))['current']
        from adapters.context.incremental import ProjectionWorker
        drain(ProjectionWorker(p['repo'], p['projector'], (scope,)))
    state = run(service.read(who.subject_id, p['scope']))
    assert {r['revision_id'] for r in state['understanding']} == set(versions[p['scope']]['revision_ids'])
    assert len(state['understanding']) == 2
    assert provider.generate.await_count == 2  # Only the two explicit memorisations.
    repository = repositories(who.subject_id)
    original = repository.read

    async def contaminated(scope):
        state = await original(scope)
        state['understanding_ids'] += versions[p['sibling']]['revision_ids']
        return state

    with monkeypatch.context() as patch:
        patch.setattr(repository, 'read', contaminated)
        patch.setattr(service, 'repository_for', lambda subject: repository)
        with pytest.raises(EnrichmentUnavailable):
            run(service.read(who.subject_id, p['scope']))
    with p['projector'].driver.session() as session:
        session.run('MATCH (r:QH30Revision {slice_id:$slice, revision_id:$id}) DETACH DELETE r',
            slice=p['projector'].key(p['scope']), id=versions[p['scope']]['revision_ids'][0]).consume()
    from app.core.models import ContextRetrievalUnavailable
    with pytest.raises(ContextRetrievalUnavailable):
        run(service.read(who.subject_id, p['scope']))
    assert provider.generate.await_count == 2


@pytest.mark.parametrize('generic', ['0005_retire_legacy_category'], indirect=True)
def test_explicit_recap_style_refresh_preserves_old_version_and_replays_new_version(generic, empty_database, monkeypatch):
    from app.understanding import recap
    p = generic
    service, who, repositories, provider = prepare(p, empty_database)
    scope = p['scope']
    run(service.append(who.subject_id, scope, document()))
    monkeypatch.setattr(recap, 'PRESENTATION_VERSION', 1)
    old = run(service.consolidate(who, scope))
    drain(p['worker'])
    old_rows = run(service.read(who.subject_id, scope))['understanding']
    monkeypatch.setattr(recap, 'PRESENTATION_VERSION', 2)
    state = run(service.read(who.subject_id, scope))
    assert state['pending_count'] == 0 and state['recap'] and not state['current']['has_recap']
    assert provider.generate.await_count == 1  # Reading never infers.
    new = run(service.consolidate(who, scope))
    drain(p['worker'])
    assert new['current']['version'] == 2 and new['current']['id'] != old['current']['id']
    assert new['current']['has_recap'] and provider.generate.await_count == 2
    again = run(service.consolidate(who, scope))
    assert again['current'] == new['current'] and provider.generate.await_count == 2
    with repositories(who.subject_id).connect() as connection:
        retained = connection.execute('SELECT count(*) n FROM context_consolidations WHERE context_space_id=%s', (scope,)).fetchone()
        assert retained['n'] == 2
    for row in old_rows:
        page = run(service.context.browse(ContextRequest(
            subject_id=who.subject_id, query=ContextBrowse(
                context_id=scope, view='history', revision_id=row['revision_id'], limit=1))))
        assert page.revisions[0].content == row['content']


@pytest.mark.parametrize('generic', ['0005_retire_legacy_category'], indirect=True)
def test_explicit_regeneration_reuses_original_source_and_preserves_previous_on_failure(generic, empty_database):
    p = generic
    service, who, repositories, provider = prepare(p, empty_database)
    scope = p['scope']; original = document()
    run(service.append(who.subject_id, scope, original))
    first = run(service.consolidate(who, scope)); drain(p['worker'])
    def source_count():
        with p['repo'].connect() as c:
            return c.execute('SELECT count(*) n FROM source_revisions WHERE context_space_id=%s', (scope,)).fetchone()['n']
    before = source_count(); operation = str(uuid4())
    second = run(service.consolidate(who, scope, operation)); drain(p['worker'])
    assert second['current']['version'] == 2 and second['current']['source_revision_id'] == first['current']['source_revision_id']
    assert second['current']['intake_ids'] == first['current']['intake_ids'] and second['pending_count'] == 0
    assert not set(second['current']['revision_ids']) & set(first['current']['revision_ids'])
    assert source_count() == before and provider.generate.await_count == 2
    assert run(service.consolidate(who, scope, operation))['current'] == second['current']
    assert provider.generate.await_count == 2
    run(service.append(who.subject_id, scope, document('Nouvelle information encore en attente.')))
    provider.generate.side_effect = ValueError('Synthetic invalid output')
    failed = str(uuid4())
    with pytest.raises(ValueError): run(service.consolidate(who, scope, failed))
    state = run(service.read(who.subject_id, scope))
    assert state['current'] == second['current'] and state['pending_count'] == 1 and source_count() == before
    from app.understanding.enrichment import EnrichmentConflict
    with pytest.raises(EnrichmentConflict): run(service.consolidate(who, scope, failed))
    assert provider.generate.await_count == 3
    provider.generate.side_effect = None
    third = run(service.consolidate(who, scope, str(uuid4()))); drain(p['worker'])
    assert third['current']['version'] == 3 and source_count() == before and third['pending_count'] == 1
    with pytest.raises(EnrichmentConflict): run(service.consolidate(who, scope, failed))
    assert provider.generate.await_count == 4
    with p['repo'].connect() as c:
        assert c.execute('SELECT count(*) n FROM context_consolidations WHERE context_space_id=%s', (scope,)).fetchone()['n'] == 3


@pytest.mark.parametrize('generic', ['0005_retire_legacy_category'], indirect=True)
def test_manual_chat_retry_retains_one_question_and_one_answer_with_durable_failure(generic, empty_database):
    from app.chat.context import ChatProviderUnavailable
    from app.understanding.consolidation import WorkspaceChatFailed
    from app.understanding.enrichment import EnrichmentConflict
    from tests.test_chat_service import request
    p = generic
    service, who, repositories, _ = prepare(p, empty_database)
    scope = p['scope']; question = document('Prépare un planning sur six jours.')
    run(service.append(who.subject_id, scope, question))
    service.ai.respond = AsyncMock(side_effect=ChatProviderUnavailable('Synthetic invalid envelope'))
    failed = str(uuid4())
    with pytest.raises(WorkspaceChatFailed): run(service.respond(who, scope, request(), question['id'], failed))
    state = run(service.read(who.subject_id, scope))
    assert len(state['intake']) == 1 and state['chat_attempts'][0]['state'] == 'failed'
    with pytest.raises(EnrichmentConflict): run(service.respond(who, scope, request(), question['id'], failed))
    assert service.ai.respond.await_count == 1
    service.ai.respond.side_effect = None
    service.ai.respond.return_value = SimpleNamespace(message=Message(role=MessageRole.ASSISTANT, content='Planning en six jours.'),
        model='mistral-small-2603', support_basis='general', insufficient_context=False, partial_coverage=False, references=())
    operation = str(uuid4())
    run(service.respond(who, scope, request(), question['id'], operation))
    state = run(service.read(who.subject_id, scope))
    assert len(state['intake']) == 2 and state['intake'][0]['id'] == question['id']
    assert state['intake'][1]['reply_to'] == question['id'] and state['intake'][1]['attribution']['support_basis'] == 'general'
    assert state['chat_attempts'][0]['state'] == 'completed'
    run(service.respond(who, scope, request(), question['id'], operation))
    assert service.ai.respond.await_count == 2 and len(run(service.read(who.subject_id, scope))['intake']) == 2
    other = document('Autre question.')
    run(service.append(who.subject_id, scope, other))
    repo = repositories(who.subject_id)
    first_attempt, second_attempt = str(uuid4()), str(uuid4())
    run(repo.claim_chat(scope, other['id'], first_attempt))
    with pytest.raises(EnrichmentConflict): run(repo.claim_chat(scope, other['id'], second_attempt))
    run(repo.finish_chat(scope, other['id'], first_attempt))
    run(repo.claim_chat(scope, other['id'], second_attempt))
    run(repo.finish_chat(scope, other['id'], second_attempt))
    with pytest.raises(EnrichmentConflict): run(repo.claim_chat(scope, other['id'], first_attempt))
