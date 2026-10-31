"""One disposable SQL/Neo4j replay of a retained unsafe approval, never VPS data."""
from copy import deepcopy
from dataclasses import replace
import json
from uuid import uuid4

from alembic import command
import pytest

from adapters.postgres.disclosure import PostgresDisclosureRepository
from adapters.postgres.guest import PostgresGuestRepository
from adapters.postgres.projection_drafts import PostgresDraftRepository
from app.projections.disclosure import TEXT_REVIEW
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.projections.disclosure_service import DisclosureService
from app.projections.document_scope import is_empty_projection
from tests.test_disclosure import policy
from tests.test_projection_engine_pipeline import application
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain
from tests.test_projection_drafts import run


@pytest.mark.parametrize('generic',['0005_retire_legacy_category'],indirect=True)
def test_document_scope_and_retained_approval_are_restricted_without_rewrite(generic,empty_database):
    p=generic;repo=p['repo'];scope=p['scope'];owner=repo.subject_id
    command.upgrade(empty_database,'0012_space_deletion')
    p['drafts']=PostgresDraftRepository(url=repo.url)
    sources=[]
    for label in ('CV','Contract'):
        source=deepcopy(p['source']);source.update(id=str(uuid4()),source_id=str(uuid4()),content=label+' evidence')
        source['origin']['metadata']={'media_type':'application/pdf'};sources.append(source)
    cv,contract=sources;rows=[]
    for text,supports in [('CV-ALLOWED',[cv['id']]),('CONTRACT-PRIVATE',[contract['id']]),('MIXED-PRIVATE',[cv['id'],contract['id']])]:
        row=revision(p,text);row['provenance']=supports;rows.append(row)
    relation=revision(p,'RELATION-PRIVATE',shape='relation');relation['provenance']=[cv['id']]
    relation['relation']=dict(source_item_id=rows[0]['item_id'],source_revision_id=rows[0]['id'],
        target_item_id=rows[1]['item_id'],target_revision_id=rows[1]['id'],predicate='synthetic_link')
    rows.append(relation);repo.save(sources=sources,revisions=rows);drain(p['worker'])
    repository=PostgresDisclosureRepository(url=repo.url,projector=p['projector'])
    service=DisclosureService(drafts=application(p),repository=repository)
    frozen=repo.read_snapshot((scope,))
    empty=run(service.prepare(owner,scope,policy()))
    assert is_empty_projection(empty.payload) and not empty.report['anchors']
    snapshot=run(service.approve(owner,scope,empty.id,empty.fingerprint,exceptions=()))
    assert snapshot.payload==empty.payload
    cv_policy=policy(semantic_documents=(cv['id'],),original_documents=(cv['id'],))
    preview=run(service.prepare(owner,scope,cv_policy))
    assert [item['text'] for item in preview.payload['items']]==['Generic CV-ALLOWED']
    # Reconstruct a retained approval made before source authorization was enforced.
    full=run(service.drafts.resolve(owner,scope,preview.draft_id,1)).revisions
    unsafe,report=OutboundDisclosureGuard().apply(full,cv_policy)
    unsafe['recap']={'title':'Previously approved','text':'CONTRACT-PRIVATE'}
    legacy=replace(preview,id=str(uuid4()),payload_json=json.dumps(unsafe),report_json=json.dumps(report))
    from app.projections.disclosure import preview_fingerprint
    legacy=replace(legacy,fingerprint=preview_fingerprint(legacy));legacy=run(repository.prepare(legacy))
    retained=run(repository.approve(legacy,(TEXT_REVIEW,)))
    guest=PostgresGuestRepository(url=repo.url)
    invite=run(guest.create(owner,scope,retained.id,'d'*64))
    challenge,session=str(uuid4()),str(uuid4())
    with repo.connect() as c:
        c.execute("INSERT INTO guest_challenges(id,invitation_id,code_hash,expires_at) VALUES(%s,%s,%s,clock_timestamp()+interval '1 hour')",(challenge,invite['id'],'e'*64))
        c.execute("INSERT INTO guest_sessions(id,invitation_id,challenge_id,token_hash,expires_at) VALUES(%s,%s,%s,%s,clock_timestamp()+interval '1 hour')",(session,invite['id'],challenge,'f'*64))
    grant=run(guest.authenticate('f'*64));restricted=run(guest.payload(grant,'READ')).payload
    assert [i['text'] for i in restricted['items']]==['Generic CV-ALLOWED']
    assert 'recap' not in restricted and 'PRIVATE' not in str(restricted)
    assert run(repository.snapshot(owner,scope,retained.id))==retained
    assert repo.read_snapshot((scope,))==frozen
    run(guest.revoke(owner,scope,invite['id']));assert run(guest.authenticate('f'*64)) is None
