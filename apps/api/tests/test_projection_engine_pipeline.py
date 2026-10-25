"""Real canonical and native graph enforcement; reuse existing isolated fixtures."""
from dataclasses import asdict
import json

import pytest

from adapters.context.projection_drafts import NativeDraftResolver
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.security import PostgresSecurityReader
from app.policy.owner import OwnerPolicyService
from app.policy.services import projection_authorizer
from app.projections.drafts import ProjectionNotFound, ProjectionUnavailable
from app.projections.engine import ProjectionDraftService
from tests.test_projection_drafts import run, spec, uid
from tests.test_projection_drafts_sql import drafts as drafts, refs
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain


def application(p):
    policy=OwnerPolicyService(owner_for=PostgresSecurityReader(url=p['repo'].url).owner_for)
    def repository(subject):
        return CanonicalRepository(url=p['repo'].url,subject_id=subject)
    resolver=NativeDraftResolver(repository_for=repository,projector=p['projector'])
    return ProjectionDraftService(repository=p['drafts'],authorize=projection_authorizer(policy),resolver=resolver)


def create(p,service,**changes):
    return run(service.create(p['repo'].subject_id,p['scope'],spec(included=refs(p),**changes)))


def resolve(p,service,draft,**changes):
    return run(service.resolve(p['repo'].subject_id,p['scope'],draft.id,draft.version,**changes))


def test_selected_revisions_only_no_source_body_or_unselected_hydration(drafts,monkeypatch):
    p=drafts;service=application(p);a,b=refs(p)
    draft=create(p,service,excluded=(b,));drain(p['worker'])
    original=CanonicalRepository.read_snapshot;calls=[]
    def bounded(repository,scopes,revision_ids=None,**kwargs):
        assert tuple(scopes)==(p['scope'],) and set(revision_ids)=={a.revision_id}
        assert kwargs=={'source_metadata_only':True}
        calls.append(tuple(revision_ids))
        snapshot=original(repository,scopes,revision_ids,**kwargs)
        assert all(set(s)=={'id','source_id','context_space_id'} for s in snapshot['source_revisions'])
        return snapshot
    monkeypatch.setattr(CanonicalRepository,'read_snapshot',bounded)
    result=resolve(p,service,draft)
    assert len(calls)==1
    assert [r.revision_id for r in result.revisions]==[a.revision_id]
    wire=json.dumps(asdict(result),default=str)
    assert 'Private constraint' not in wire and b.revision_id not in wire
    assert p['source']['content'] not in wire
    assert all(field not in wire for field in ('current_revision_id','based_on_revision_id','validated_by','locator'))
    assert result.revisions[0].validation_state=='proposed'


def test_foreign_owner_and_direct_ids_rejected_before_hydration(drafts,monkeypatch):
    p=drafts;service=application(p);a,b=refs(p);draft=create(p,service,excluded=(b,));drain(p['worker'])
    def no_content(*args,**kwargs):raise AssertionError('Private content must not be loaded')
    monkeypatch.setattr(CanonicalRepository,'read_snapshot',no_content)
    for subject,scope in ((uid(),p['scope']),(p['repo'].subject_id,p['foreign'])):
        with pytest.raises(ProjectionNotFound):run(service.resolve(subject,scope,draft.id,1))
    with pytest.raises(ProjectionNotFound):resolve(p,service,draft,requested=(b,))


def test_uum_v3_proposed_content_survives_exact_projection_without_source_disclosure(drafts,monkeypatch):
    from adapters.postgres.semantic_profiles import uum_definitions
    from app.projections.drafts import RevisionKey
    from tests.test_generic_semantics import revision
    p=drafts
    # Explicit test-only registration on this fixture's disposable 0007 database.
    # No production schema gate or provisioning helper is relaxed.
    p['repo'].register_types(uum_definitions())
    row=revision(p,'UUM proposed pilot');row['type_version']=3
    primary=dict(value='objectives_intentions',certainty='asserted',evidence_refs=[0],review_state='proposed')
    row['content'].update(primary_dimension=primary,citations=[dict(source_revision_id=p['source']['id'],quote='Choose a pilot.')])
    p['repo'].save(revisions=[row]);drain(p['worker'])
    service=application(p);key=RevisionKey(item_id=row['item_id'],revision_id=row['id'])
    draft=run(service.create(p['repo'].subject_id,p['scope'],spec(included=(key,),excluded=refs(p))))
    original=CanonicalRepository.read_snapshot;before=original(p['repo'],(p['scope'],));calls=[]
    def selected(repository,scopes,revision_ids=None,**kwargs):
        assert tuple(scopes)==(p['scope'],) and tuple(revision_ids)==(row['id'],)
        assert kwargs=={'source_metadata_only':True}
        snapshot=original(repository,scopes,revision_ids,**kwargs)
        assert all(set(s)=={'id','source_id','context_space_id'} for s in snapshot['source_revisions'])
        calls.append(revision_ids);return snapshot
    monkeypatch.setattr(CanonicalRepository,'read_snapshot',selected)
    result=resolve(p,service,draft);assert len(calls)==1 and len(result.revisions)==1
    exported=result.revisions[0]
    assert exported.type_version==3 and exported.validation_state=='proposed'
    assert exported.content==row['content'] and exported.content['primary_dimension']==primary
    wire=json.dumps(asdict(result),default=str)
    assert p['source']['content'] not in wire and all(k.revision_id not in wire for k in refs(p))
    with pytest.raises(ProjectionNotFound):resolve(p,service,draft,requested=refs(p))
    assert len(calls)==1 and original(p['repo'],(p['scope'],))==before


@pytest.mark.parametrize('failure',['pending','missing','tampered'])
def test_native_graph_is_required_and_cannot_supply_extra_content(drafts,failure):
    p=drafts;service=application(p);a,b=refs(p);draft=create(p,service,excluded=(b,))
    if failure!='pending':
        drain(p['worker'])
        with p['projector'].driver.session() as session:
            clause='DETACH DELETE r' if failure=='missing' else "SET r.text='PRIVATE GRAPH INJECTION'"
            session.run('MATCH (r:QH30Revision {slice_id:$scope,revision_id:$id}) '+clause,
                scope=p['projector'].key(p['scope']),id=a.revision_id).consume()
    with pytest.raises(ProjectionUnavailable) as error:resolve(p,service,draft)
    assert 'PRIVATE' not in str(error.value)
