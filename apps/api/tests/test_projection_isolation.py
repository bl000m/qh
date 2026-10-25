"""QH-16 adversarial native/SQL/OIDC checks; no public route or paid provider."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
from uuid import UUID

from alembic import command
from fastapi import Depends
from fastapi.testclient import TestClient
import httpx
import jwt
import pytest

from adapters.oidc import OIDCAuthenticator
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.security import PostgresSecurityReader
from app.api.context_spaces import call
from app.api.security import SecurityBindings, authenticated_subject
from app.composition import ApplicationServices
from app.core.models import GenerationRequest, Message, MessageRole
from app.main import create_app
from app.policy.owner import OwnerPolicyService
from app.policy.services import projection_authorizer
from app.projections.drafts import ProjectionConflict, ProjectionNotFound, ProjectionUnavailable, RevisionKey
from tests.fakes import FakeContextEngine, FakeContextService, FakeLLMProvider, GENERATION, RESULT
from tests.test_canonical_graph_pipeline import drain
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_oidc_security import KEY, SETTINGS, token
from tests.test_projection_drafts import run, spec, uid
from tests.test_projection_drafts_sql import drafts as drafts, refs
from tests.test_projection_engine_pipeline import application, create, resolve


def test_pinned_revision_survives_new_revision_confirmation_and_rebuild(drafts):
    p=drafts;service=application(p);a,b=refs(p);draft=create(p,service,excluded=(b,));drain(p['worker'])
    new=deepcopy(p['rows'][0]);new.update(id=uid(),revision_no=2,based_on_revision_id=a.revision_id)
    new['content']={'text':'PRIVATE LATER CONTENT'}
    p['repo'].save(revisions=[new]);drain(p['worker'])
    # Human confirmation is another immutable revision; pointer must not change scope.
    confirmed=deepcopy(new);confirmed.update(id=uid(),revision_no=3,based_on_revision_id=new['id'],
        validation_state='confirmed',validated_by=p['repo'].subject_id,validated_at='2026-10-20T00:00:00Z')
    p['repo'].save(revisions=[confirmed]);drain(p['worker'])
    with p['repo'].connect() as c:
        c.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s',(confirmed['id'],a.item_id))
    # Current pointer is deliberately outside selected content and graph assertion fingerprint.
    p['worker'].rebuild(p['scope'])
    value=resolve(p,service,draft)
    wire=json.dumps(asdict(value),default=str)
    assert [r.revision_id for r in value.revisions]==[a.revision_id]
    assert 'PRIVATE LATER CONTENT' not in wire and new['id'] not in wire and confirmed['id'] not in wire
    assert value.revisions[0].validation_state=='proposed'
    with pytest.raises(ProjectionNotFound):resolve(p,service,draft,requested=(RevisionKey(item_id=a.item_id,revision_id=new['id']),))


def test_relation_requires_exact_explicit_endpoints_and_never_expands(drafts,monkeypatch):
    p=drafts;service=application(p);a,b=refs(p)
    rel=revision(p,'Relationship with private endpoint',shape='relation')
    rel['relation']=dict(source_item_id=a.item_id,source_revision_id=a.revision_id,
        target_item_id=b.item_id,target_revision_id=b.revision_id,predicate='related_to')
    p['repo'].save(revisions=[rel]);drain(p['worker'])
    r=RevisionKey(item_id=rel['item_id'],revision_id=rel['id'])
    partial=run(service.create(p['repo'].subject_id,p['scope'],spec(included=(a,r))))
    with monkeypatch.context() as patch:
        patch.setattr(CanonicalRepository,'read_snapshot',lambda *a,**k:pytest.fail('No relation or endpoint content before explicit scope'))
        with pytest.raises(ProjectionNotFound):resolve(p,service,partial)
    full=run(service.create(p['repo'].subject_id,p['scope'],spec(included=(a,b,r))))
    assert {x.revision_id for x in resolve(p,service,full).revisions}=={a.revision_id,b.revision_id,r.revision_id}
    with pytest.raises(ProjectionNotFound):resolve(p,service,full,requested=(r,))
    # Existing graph relationship to the excluded endpoint cannot expand a plain-item selection.
    selected=create(p,service,excluded=(b,))
    assert [x.revision_id for x in resolve(p,service,selected).revisions]==[a.revision_id]


@pytest.mark.parametrize('change',['draft','owner','expiry','canonical'])
def test_inflight_changes_never_disclose_a_result(drafts,monkeypatch,change):
    from datetime import datetime, timezone
    p=drafts;service=application(p);draft=create(p,service);drain(p['worker'])
    original=service.resolver.resolve
    async def racing(*args):
        result=await original(*args)
        if change=='draft':
            run_spec=replace(draft.spec,purpose='Changed while resolving')
            await p['drafts'].replace(p['repo'].subject_id,p['scope'],draft.id,1,run_spec)
        elif change=='owner':
            with p['repo'].connect() as c:c.execute("UPDATE context_spaces SET status='inactive' WHERE id=%s",(p['scope'],))
        elif change=='expiry':
            service.clock=lambda:datetime.max.replace(tzinfo=timezone.utc)
        return result
    if change=='expiry':
        from datetime import timedelta
        draft=run(service.replace(p['repo'].subject_id,p['scope'],draft.id,1,
            replace(draft.spec,expires_at=datetime.now(timezone.utc)+timedelta(minutes=1))))
    if change=='canonical':
        read=CanonicalRepository.read_snapshot
        def publish(repository,*args,**kwargs):
            result=read(repository,*args,**kwargs)
            p['repo'].save(revisions=[revision(p,'Concurrent canonical change')])
            return result
        monkeypatch.setattr(CanonicalRepository,'read_snapshot',publish)
    else:
        monkeypatch.setattr(service.resolver,'resolve',racing)
    with pytest.raises((ProjectionConflict,ProjectionNotFound,ProjectionUnavailable)):
        resolve(p,service,draft)


def test_signed_oidc_private_probe_and_provider_order_reuse_existing_boundaries(drafts):
    p=drafts;service=application(p);a,b=refs(p);draft=create(p,service,excluded=(b,));drain(p['worker'])
    reader=PostgresSecurityReader(url=p['repo'].url)
    with p['repo'].connect() as c:
        bob=str(c.execute('SELECT owner_id FROM context_spaces WHERE id=%s',(p['foreign'],)).fetchone()['owner_id'])
        for external,subject in (('external-alice',p['repo'].subject_id),('external-bob',bob)):
            c.execute('INSERT INTO user_identities(issuer,subject,user_id) VALUES (%s,%s,%s)',(SETTINGS.issuer,external,subject))
    key=jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key(),as_dict=True)
    auth=OIDCAuthenticator(settings=SETTINGS,resolve_identity=reader.resolve_identity,
        transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'keys':[dict(key,kid='current',use='sig',alg='RS256')]})))
    policy=OwnerPolicyService(owner_for=reader.owner_for)
    service.authorize=projection_authorizer(policy)
    app=create_app(services=ApplicationServices(context=FakeContextService(FakeContextEngine(RESULT)),policy=policy),
        security=SecurityBindings(authenticate=auth.authenticate,policy=policy))
    provider=FakeLLMProvider(GENERATION)
    # This test-only consumer proves sequencing with the existing HTTP/OIDC mapper.
    # No public route, production provider binding or disclosure grant is created.
    @app.get('/test/projection/{scope}/{draft_id}/{item_id}/{revision_id}')
    async def probe(scope:UUID,draft_id:UUID,item_id:UUID,revision_id:UUID,subject=Depends(authenticated_subject)):
        filtered=await call(service.resolve(subject,str(scope),str(draft_id),1,
            (RevisionKey(item_id=str(item_id),revision_id=str(revision_id)),)))
        payload=json.dumps(asdict(filtered),default=str)
        await provider.generate(GenerationRequest(messages=(Message(role=MessageRole.USER,content=payload),)))
        return asdict(filtered)
    def path(pair,draft_id=draft.id,scope=p['scope']):return f'/test/projection/{scope}/{draft_id}/{pair.item_id}/{pair.revision_id}'
    with TestClient(app) as client:
        assert client.get(path(a)).status_code==401
        alice={'Authorization':'Bearer '+token()};bob_header={'Authorization':'Bearer '+token(sub='external-bob')}
        assert client.get(path(a),headers=bob_header).status_code==404
        denied=client.get(path(b),headers=alice)
        missing=client.get(path(a,draft_id=uid()),headers=alice)
        assert denied.status_code==missing.status_code==404 and denied.json()==missing.json()
        assert provider.requests==[]
        good=client.get(path(a),headers=alice)
        assert good.status_code==200 and len(provider.requests)==1
        payload=provider.requests[0].messages[0].content
        assert 'Private constraint' not in payload and b.revision_id not in payload
        assert good.json()['revisions'][0]['revision_id']==a.revision_id
        assert client.get(path(a),headers={'Authorization':'Bearer '+token(sub='unmapped')}).status_code==401


def test_additive_migration_preserves_canonical_payload_and_existing_triggers(generic,empty_database):
    p=generic
    command.upgrade(empty_database,'0006_owner_organization')
    p['repo'].save(sources=[p['source']],revisions=[revision(p,'Preserved canonical')])
    before=p['repo'].read_snapshot((p['scope'],))
    with p['repo'].connect() as c:
        triggers=c.execute("SELECT tgname,pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE NOT tgisinternal ORDER BY tgname,def").fetchall()
    command.upgrade(empty_database,'0007_projection_drafts')
    assert p['repo'].read_snapshot((p['scope'],))==before
    with p['repo'].connect() as c:
        after=c.execute("SELECT tgname,pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE NOT tgisinternal AND tgname<>'qh_projection_draft_identity' ORDER BY tgname,def").fetchall()
        assert triggers==after
        assert c.execute('SELECT count(*) AS n FROM projection_drafts').fetchone()['n']==0


@pytest.mark.parametrize('target',['sibling','foreign'])
def test_valid_revision_in_other_space_never_enters_draft(drafts,monkeypatch,target):
    p=drafts;service=application(p);scope=p[target]
    with p['repo'].connect() as c:
        owner=str(c.execute('SELECT owner_id FROM context_spaces WHERE id=%s',(scope,)).fetchone()['owner_id'])
    foreign=CanonicalRepository(url=p['repo'].url,subject_id=owner)
    source=deepcopy(p['source']);source.update(id=uid(),source_id=uid(),context_space_id=scope)
    row=revision(p,'PRIVATE OTHER SPACE');row.update(context_space_id=scope,provenance=[source['id']])
    foreign.save(sources=[source],revisions=[row])
    pair=RevisionKey(item_id=row['item_id'],revision_id=row['id'])
    def no_content(*a,**k):pytest.fail('Must deny using minimal identity metadata')
    monkeypatch.setattr(CanonicalRepository,'read_snapshot',no_content)
    with pytest.raises(ProjectionNotFound) as error:
        run(service.create(p['repo'].subject_id,p['scope'],spec(included=(pair,))))
    assert row['id'] not in str(error.value) and 'PRIVATE' not in str(error.value)
