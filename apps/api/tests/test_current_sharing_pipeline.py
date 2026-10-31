"""One disposable scenario: memory, legacy/manual knowledge, scope and exclusions."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from adapters.postgres.disclosure import PostgresDisclosureRepository
from adapters.postgres.projection_drafts import PostgresDraftRepository
from app.chat.context import build_context
from app.core.models import Message, MessageRole
from app.projections.disclosure import AccessPolicy, TEXT_REVIEW
from app.projections.disclosure_service import DisclosureService
from app.projections.drafts import RevisionKey, ProjectionConflict
from tests.test_consolidation_pipeline import prepare, run
from tests.test_consolidation import document
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_projection_engine_pipeline import application
from tests.test_canonical_graph_pipeline import drain


@pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)
def test_one_current_understanding_includes_unreviewed_manual_and_old_proposals_without_superseded_versions(generic,empty_database):
    p=generic;service,who,_,provider=prepare(p,empty_database);scope=p['scope']
    run(service.append(who.subject_id,scope,document()))
    first=run(service.consolidate(who,scope));drain(p['worker'])
    first_read=run(service.read(who.subject_id,scope))
    assert first_read['understanding'] and all(r['validation_state']=='proposed' for r in first_read['understanding'])
    second=run(service.consolidate(who,scope,str(uuid4())));drain(p['worker'])
    legacy=revision(p,'Un atelier pourrait aider, hypothèse à vérifier.')
    manual=revision(p,'Choisir un pilote, déclaration explicite.')
    for row in (legacy,manual):row['type_version']=3
    manual['origin_kind']='human'
    p['repo'].save(sources=[p['source']],revisions=[legacy,manual]);drain(p['worker'])
    state=run(service.read(who.subject_id,scope))
    ids={r['revision_id'] for r in state['understanding']}
    assert ids==set(second['current']['revision_ids'])|{legacy['id'],manual['id']}
    assert not ids & set(first['current']['revision_ids'])
    assert all(r['validation_state']=='proposed' and not r['is_current_confirmed'] for r in state['understanding'])
    assert provider.generate.await_count==2  # Reading old/manual knowledge does not re-extract it.
    from tests.test_chat_context import revision as canonical
    from app.core.models import RevisionTime
    rows=tuple(canonical(**{k:v for k,v in r.items() if k!='temporal'},temporal=RevisionTime(**r['temporal'])) for r in state['understanding'])
    context=build_context(context_id=scope,revisions=rows,include_proposed=True,consolidated=True,extended_dialogue=True,
        messages=(Message(role=MessageRole.USER,content='Que contient ce contexte ?'),))
    assert {r.revision_id for r in context.revisions}==ids
    p['drafts']=PostgresDraftRepository(url=p['repo'].url)
    repository=PostgresDisclosureRepository(url=p['repo'].url,projector=p['projector'])
    sharing=DisclosureService(drafts=application(p),repository=repository)
    selection=run(repository.select(who.subject_id,scope))
    assert {r.key.revision_id for r in selection.candidates}==ids
    policy=AccessPolicy(recipient_email='invite@example.test',purpose='Préparer un atelier',rights=('ASK_AI',),
        provider='offline',expires_at=datetime.now(timezone.utc)+timedelta(hours=1),include_proposed=False)
    preview=run(sharing.prepare(who.subject_id,scope,policy))
    assert len(preview.payload['items'])==len(ids)  # Legacy flag no longer gates use.
    assert not any(e['reason']=='unconfirmed' for e in preview.report['exclusions'])
    restricted=run(sharing.prepare(who.subject_id,scope,replace(policy,excluded=(RevisionKey(item_id=legacy['item_id'],revision_id=legacy['id']),))))
    assert legacy['content']['text'] not in str(restricted.payload)
    snapshot=run(sharing.approve(who.subject_id,scope,restricted.id,restricted.fingerprint,exceptions=(TEXT_REVIEW,)))
    assert snapshot.payload==restricted.payload
    with pytest.raises(ProjectionConflict):
        run(sharing.prepare(who.subject_id,scope,replace(policy,expires_at=datetime.now(timezone.utc)-timedelta(seconds=1))))
