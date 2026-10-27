"""Actual isolated SQL + Neo4j: automatic scope, safe payload and immutable history."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import json

from alembic import command
import psycopg
import pytest

from adapters.postgres.disclosure import PostgresDisclosureRepository
from adapters.postgres.semantic_profiles import uum_definitions
from app.projections.disclosure import DisclosureDecisionRequired, TEXT_REVIEW
from app.projections.disclosure_service import DisclosureService
from app.projections.drafts import ProjectionConflict, ProjectionNotFound, ProjectionUnavailable, RevisionKey
from tests.test_disclosure import policy
from tests.test_projection_engine_pipeline import application
from tests.test_projection_drafts_sql import drafts as drafts, refs
from tests.test_generic_semantics import generic as generic, revision
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from tests.test_canonical_graph_pipeline import drain
from tests.test_projection_drafts import run, uid


@pytest.fixture
def disclosure(drafts,empty_database):
    p=drafts
    command.upgrade(empty_database,'0008_approved_disclosure')
    repository=PostgresDisclosureRepository(url=p['repo'].url,projector=p['projector'])
    p.update(disclosures=repository,disclosure=DisclosureService(drafts=application(p),repository=repository))
    drain(p['worker'])
    return p


def prepare(p,**changes):
    return run(p['disclosure'].prepare(p['repo'].subject_id,p['scope'],policy(**changes)))


def approve(p,preview,**changes):
    return run(p['disclosure'].approve(p['repo'].subject_id,p['scope'],preview.id,preview.fingerprint,
        **({'exceptions':(TEXT_REVIEW,)} | changes)))


def count(p,table):
    with p['repo'].connect() as c:return c.execute('SELECT count(*) AS n FROM '+table).fetchone()['n']


def test_empty_current_no_false_empty_snapshot_and_single_bulk_proposal_inclusion(disclosure):
    p=disclosure;before=p['repo'].read_snapshot((p['scope'],))
    preview=prepare(p)
    assert preview.report['status']=='no_disclosable_items' and not preview.payload['items']
    assert len(preview.report['exclusions'])==2
    with pytest.raises(ProjectionNotFound):approve(p,preview)
    assert count(p,'approved_snapshots')==0
    preview=prepare(p,include_proposed=True)
    assert len(preview.payload['items'])==2
    with pytest.raises(DisclosureDecisionRequired):approve(p,preview,exceptions=())
    snapshot=approve(p,preview)
    assert len(snapshot.payload['items'])==2
    assert all(r['validation_state']=='proposed' for r in snapshot.payload['items'])
    assert p['repo'].read_snapshot((p['scope'],))==before
    assert count(p,'approved_snapshot_revisions')==2


def test_minimized_snapshot_is_durable_never_rehydrates_originals(disclosure,monkeypatch):
    p=disclosure;p['repo'].register_types(uum_definitions())
    row=revision(p,'Plan workshop with alice@example.test +33 6 12 34 56 78')
    row['type_version']=3
    row['content']['primary_dimension']=dict(value='objectives_intentions',certainty='asserted',
        evidence_refs=[0],review_state='proposed')
    row['content']['citations']=[dict(source_revision_id=p['source']['id'],quote='Choose a pilot.')]
    row['content']['properties']={'never':'PRIVATE PROPERTY'}
    p['repo'].save(revisions=[row]);drain(p['worker'])
    # Restricting optional exact pairs is advanced; ordinary flow needed none.
    preview=prepare(p,include_proposed=True,include_quotes=True,excluded=refs(p))
    assert len(preview.payload['items'])==1
    snapshot=approve(p,preview)
    wire=json.dumps(snapshot.payload)
    for canary in ('alice@example.test','+33 6 12 34 56 78','PRIVATE PROPERTY',p['source']['content'],row['id']):
        assert canary not in wire
    assert snapshot.payload['items'][0]['citations'][0]['quote']=='Choose a pilot.'
    assert snapshot.payload['items'][0]['primary_dimension']['review_state']=='proposed'
    def no_originals(*a,**kw):raise AssertionError('Snapshot must never hydrate originals')
    monkeypatch.setattr(type(p['repo']),'read_snapshot',no_originals)
    reopened=PostgresDisclosureRepository(url=p['repo'].url,projector=p['projector'])
    assert run(reopened.snapshot(p['repo'].subject_id,p['scope'],snapshot.id))==snapshot
    mutated=snapshot.payload;mutated['items'][0]['text']='MUTATION'
    assert snapshot.payload['items'][0]['text']!='MUTATION'


def test_sensitive_items_excluded_and_exceptions_do_not_override_blocked_content(disclosure):
    p=disclosure;row=revision(p,'Diagnostic de cancer PRIVATE CANARY')
    p['repo'].save(revisions=[row]);drain(p['worker'])
    preview=prepare(p,include_proposed=True)
    assert any(r['reason']=='recognised_high_risk' for r in preview.report['exclusions'])
    assert 'PRIVATE CANARY' not in json.dumps(preview.payload)
    snapshot=approve(p,preview)
    assert all(a['revision_id']!=row['id'] for a in preview.report['anchors'])
    assert 'PRIVATE CANARY' not in json.dumps(asdict(snapshot),default=str)


@pytest.mark.parametrize('scope',['foreign','sibling'])
def test_other_owner_or_space_cannot_read_preview_approve_or_read_snapshot(disclosure,scope):
    p=disclosure;preview=prepare(p,include_proposed=True);snapshot=approve(p,preview)
    for subject,target in ((uid(),p['scope']),(p['repo'].subject_id,p[scope])):
        for operation in (
            p['disclosure'].preview(subject,target,preview.id),
            p['disclosure'].approve(subject,target,preview.id,preview.fingerprint,exceptions=(TEXT_REVIEW,)),
            p['disclosure'].snapshot(subject,target,snapshot.id),
        ):
            with pytest.raises(ProjectionNotFound):run(operation)
    assert count(p,'approved_snapshots')==1


@pytest.mark.parametrize('stage',['empty','prepare','approve'])
def test_stale_graph_never_releases_or_materializes_even_empty_scope(disclosure,stage):
    p=disclosure
    preview=prepare(p,include_proposed=True) if stage=='approve' else None
    p['repo'].save(revisions=[revision(p,'Pending canonical change')])
    with pytest.raises(ProjectionUnavailable):
        if preview:approve(p,preview)
        else:prepare(p,include_proposed=stage!='empty')
    assert count(p,'approved_snapshots')==0


def test_graph_tampering_cannot_supply_or_expand_payload(disclosure):
    p=disclosure;key=refs(p)[0]
    with p['projector'].driver.session() as session:
        session.run('MATCH (r:QH30Revision {slice_id:$scope,revision_id:$revision}) SET r.text=$text',
            scope=p['projector'].key(p['scope']),revision=key.revision_id,text='PRIVATE GRAPH INJECTION').consume()
    with pytest.raises(ProjectionUnavailable):prepare(p,include_proposed=True)
    assert count(p,'disclosure_previews')==0


def test_context_change_requires_new_preview_but_old_snapshot_does_not_expand(disclosure):
    p=disclosure;preview=prepare(p,include_proposed=True);snapshot=approve(p,preview)
    p['repo'].save(revisions=[revision(p,'NEW PRIVATE CONTENT')]);drain(p['worker'])
    with pytest.raises(ProjectionConflict):approve(p,preview)
    current=run(p['disclosure'].snapshot(p['repo'].subject_id,p['scope'],snapshot.id))
    assert current==snapshot and 'NEW PRIVATE CONTENT' not in json.dumps(current.payload)
    assert count(p,'approved_snapshots')==1


def test_expiry_hash_tampering_and_draft_edits_block_approval(disclosure):
    p=disclosure;preview=prepare(p,include_proposed=True)
    with pytest.raises(ProjectionConflict):
        run(p['disclosure'].approve(p['repo'].subject_id,p['scope'],preview.id,'0'*64,exceptions=(TEXT_REVIEW,)))
    p['disclosure'].clock=lambda:preview.created_at+timedelta(minutes=16)
    with pytest.raises(ProjectionConflict):approve(p,preview)
    p['disclosure'].clock=lambda:datetime.now(timezone.utc)
    draft=run(p['disclosure'].drafts.read(p['repo'].subject_id,p['scope'],preview.draft_id))
    run(p['disclosure'].drafts.replace(p['repo'].subject_id,p['scope'],draft.id,1,
        replace(draft.spec,purpose='Changed audience purpose')))
    with pytest.raises(ProjectionConflict):approve(p,preview)
    assert count(p,'approved_snapshots')==0


def test_parallel_approval_is_idempotent_and_snapshots_are_sql_immutable(disclosure):
    p=disclosure;preview=prepare(p,include_proposed=True)
    with ThreadPoolExecutor(2) as pool:
        snapshots=list(pool.map(lambda _:approve(p,preview),range(2)))
    assert snapshots[0]==snapshots[1] and count(p,'approved_snapshots')==1
    for table in ('approved_snapshots','approved_snapshot_revisions','disclosure_previews'):
        for statement in (f'DELETE FROM {table}',f'UPDATE {table} SET context_space_id=context_space_id'):
            with p['repo'].connect() as c, pytest.raises(psycopg.errors.CheckViolation):c.execute(statement)
    # Include the referencing tables so FK preflight reaches the immutable TRUNCATE trigger.
    with p['repo'].connect() as c, pytest.raises(psycopg.errors.CheckViolation):
        c.execute('TRUNCATE disclosure_previews,approved_snapshots,approved_snapshot_revisions')
    assert count(p,'approved_snapshots')==1 and count(p,'approved_snapshot_revisions')==2


def test_bounded_selection_refuses_partial_scope(disclosure):
    p=disclosure;p['repo'].save(revisions=[revision(p,f'Bounded fixture {i}') for i in range(99)])
    drain(p['worker'])
    with pytest.raises(ProjectionUnavailable,match='100-revision'):prepare(p,include_proposed=True)
    assert count(p,'disclosure_previews')==count(p,'approved_snapshots')==0


def test_only_current_confirmed_and_latest_pending_are_eligible(disclosure):
    p=disclosure;a=p['rows'][0]
    confirmed={**a,'id':uid(),'revision_no':2,'based_on_revision_id':a['id'],
        'validation_state':'confirmed','validated_by':p['repo'].subject_id,
        'validated_at':datetime.now(timezone.utc).isoformat()}
    p['repo'].save(revisions=[confirmed])
    pending={**a,'id':uid(),'revision_no':3,'based_on_revision_id':confirmed['id']}
    p['repo'].save(revisions=[pending]);drain(p['worker'])
    with p['repo'].connect() as c:
        c.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s',(confirmed['id'],a['item_id']))
    drain(p['worker'])
    preview=prepare(p)
    assert [r['revision_id'] for r in preview.report['anchors']]==[confirmed['id']]
    all_preview=prepare(p,include_proposed=True)
    anchors={r['revision_id'] for r in all_preview.report['anchors']}
    assert confirmed['id'] in anchors and pending['id'] in anchors and a['id'] not in anchors


def test_additive_snapshot_schema_keeps_canonical_rows_and_old_triggers(drafts,empty_database):
    p=drafts;before=p['repo'].read_snapshot((p['scope'],))
    with p['repo'].connect() as c:
        triggers=c.execute("SELECT tgname,pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE NOT tgisinternal ORDER BY tgname,def").fetchall()
    command.upgrade(empty_database,'0008_approved_disclosure')
    assert p['repo'].read_snapshot((p['scope'],))==before
    with p['repo'].connect() as c:
        after=c.execute("SELECT tgname,pg_get_triggerdef(oid) AS def FROM pg_trigger WHERE NOT tgisinternal AND tgrelid NOT IN "
            "('disclosure_previews'::regclass,'approved_snapshots'::regclass,'approved_snapshot_revisions'::regclass) ORDER BY tgname,def").fetchall()
        assert after==triggers


@pytest.mark.parametrize('generic', ['0005_retire_legacy_category'], indirect=True)
def test_subject_recap_materializes_without_sources_and_guest_read_keeps_explicit_quote_policy(disclosure, monkeypatch):
    from adapters.postgres.guest import PostgresGuestRepository
    from app.core.models import GuestAccess
    from app.projections.guest_payload import recipient_payload
    from app.understanding import recap
    p = disclosure
    p['repo'].register_types(uum_definitions())
    rows = [revision(p, text) for text in ('Obiettivi del laboratorio informatico.', 'Esercizi pratici e strumenti digitali.')]
    for row in rows:
        row['type_version'] = 3
        row['content']['extraction'] = {}
        row['content']['citations'] = [dict(source_revision_id=p['source']['id'], quote='Choose a pilot.')]
    summary = dict(title='Organizzazione di un laboratorio informatico',
        text='Proposta di laboratorio informatico con obiettivi, esercizi pratici e strumenti digitali.',
        supporting_statements=[r['content']['text'] for r in rows], provider_output_sha256='synthetic')
    rows = recap.bind(summary, rows, uid())
    p['repo'].save(revisions=rows)
    drain(p['worker'])
    preview = prepare(p, include_proposed=True)
    assert preview.payload['recap']['title'] == summary['title']
    assert 'Choose a pilot.' not in json.dumps(preview.payload)
    snapshot = approve(p, preview)
    grant = GuestAccess(session_id=uid(), invitation_id=uid(), context_id=p['scope'], snapshot_id=snapshot.id,
        rights=('READ',), expires_at=policy().expires_at)
    # This check exercises the changed SQL payload/policy read; authentication
    # itself is covered separately by guest policy and HTTP denial cases.
    repository = PostgresGuestRepository(url=p['repo'].url)
    monkeypatch.setattr(repository, '_active', lambda *args, **kwargs: grant)
    def no_originals(*args, **kwargs): raise AssertionError('Guest payload must never hydrate originals')
    monkeypatch.setattr(type(p['repo']), 'read_snapshot', no_originals)
    stored = run(repository.payload(grant, 'READ'))
    assert not stored.include_quotes
    assert recipient_payload(stored.payload, include_quotes=stored.include_quotes) == snapshot.payload
    # Materialized approval remains readable without canonical/source hydration.
    assert run(p['disclosure'].snapshot(p['repo'].subject_id, p['scope'], snapshot.id)).payload == snapshot.payload
