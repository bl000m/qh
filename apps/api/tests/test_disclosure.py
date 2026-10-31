"""Offline policy/Guard security cases, not semantic truth or anonymity proofs."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.models import RevisionRelation, SourceRevisionRef
from app.projections.disclosure import AccessPolicy, TEXT_REVIEW
from app.projections.disclosure import ApprovedSnapshot
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.projections.disclosure_service import DisclosureService
from app.projections.drafts import ProjectionUnavailable
from tests.test_projection_engine import setup
from tests.test_projection_drafts import uid
from tests.test_projection_drafts import run


def policy(**changes):
    return AccessPolicy(**(dict(recipient_email='clement@example.test', purpose='Synthetic workshop',
        rights=('READ',), expires_at=datetime.now(timezone.utc)+timedelta(hours=1)) | changes))


@pytest.mark.parametrize('changes', [
    {'recipient_email':'anyone'}, {'recipient_email':'a@b.test\r\nBcc:x@y.test'},
    {'rights':()}, {'rights':('PROPOSE_UPDATE',)}, {'rights':('READ','READ')},
    {'include_proposed':1}, {'include_quotes':'yes'}, {'expires_at':datetime(2030,1,1)},
    {'purpose':''}, {'rights':('ASK_AI',)}, {'provider':'offline'},
    {'rights':('ASK_AI',),'provider':'arbitrary-paid-provider'},
])
def test_access_policy_rejects_ambiguous_grants_and_header_injection(changes):
    with pytest.raises(ValueError):policy(**changes)


def test_proposed_items_are_shared_without_confirmation_and_rejected_ones_never():
    row=setup()[5];guard=OutboundDisclosureGuard()
    before=json.dumps(row.content)
    payload,report=guard.apply((row,),policy())
    assert payload['items'][0]['validation_state']=='proposed'
    assert report['risks']==[TEXT_REVIEW] and 'anonymisation' in report['warning']
    assert row.validation_state=='proposed' and json.dumps(row.content)==before
    payload,report=guard.apply((replace(row,validation_state='rejected'),),policy())
    assert not payload['items'] and report['exclusions'][0]['reason']=='ineligible_state'


def test_text_is_shared_verbatim_while_nested_fields_quotes_and_ids_stay_private():
    source=uid();text='Contact pilot@example.test at +33 6 12 34 56 78 or https://private.example/id, né le 02/03/1981'
    row=replace(setup()[5],validation_state='confirmed',
        content={'text':text,'properties':{'private':'PRIVATE NESTED'}, 'descriptors':[{'value':'PRIVATE DESCRIPTOR'}],
            'citations':[dict(source_revision_id=source,quote='PRIVATE QUOTE')]},
        provenance=(SourceRevisionRef(source_id=uid(),revision_id=source),))
    payload,report=OutboundDisclosureGuard().apply((row,),policy(include_quotes=True))
    wire=json.dumps(payload)
    item=payload['items'][0]
    assert item['text']==text and item['sources']==['S1'] and 'citations' not in item
    for private in ('PRIVATE',source,row.item_id,row.revision_id):
        assert private not in wire
    assert report['masks']==[] and report['anchors'][0]['revision_id']==row.revision_id


@pytest.mark.parametrize('text',['Diagnostic de cancer', 'password: fictional', 'Salaire de 45 000 €'])
def test_owner_shares_sensitive_wording_without_keyword_exclusion(text):
    row=replace(setup()[5],validation_state='confirmed',content={'text':text})
    payload,report=OutboundDisclosureGuard().apply((row,),policy())
    assert payload['items'][0]['text']==text and not report['exclusions']


def test_primary_dimension_does_not_decide_disclosure_and_citations_default_to_omitted():
    row=replace(setup()[5],validation_state='confirmed',content={'text':'Plain fictional objective',
        'primary_dimension':dict(value='objectives_intentions',certainty='tentative',review_state='proposed',
            evidence_refs=[0]),'citations':[{'quote':'PRIVATE QUOTE'}]})
    payload,report=OutboundDisclosureGuard().apply((row,),policy())
    assert payload['items'][0]['primary_dimension']['review_state']=='proposed'
    assert 'PRIVATE QUOTE' not in json.dumps(payload) and report['risks']==[TEXT_REVIEW]


@pytest.mark.parametrize('rejected',[False,True])
def test_relation_endpoints_must_survive_guard_without_automatic_scope_expansion(rejected):
    a=replace(setup()[5],validation_state='confirmed')
    b=replace(a,item_id=uid(),revision_id=uid(),content={'text':'Second statement'},validation_state='rejected' if rejected else 'confirmed')
    relation=replace(a,item_id=uid(),revision_id=uid(),structural_kind='relation',content={'text':'Two statements are related'},
        relation=RevisionRelation(predicate='related_to',source_item_id=a.item_id,source_revision_id=a.revision_id,
            target_item_id=b.item_id,target_revision_id=b.revision_id))
    payload,report=OutboundDisclosureGuard().apply((a,b,relation),policy())
    assert len(payload['items'])==(1 if rejected else 3)
    if rejected:
        assert {r['reason'] for r in report['exclusions']}=={'ineligible_state','endpoint_not_disclosable'}
    else:
        assert payload['items'][2]['relation']=={'source':'R1','target':'R2'}
    assert a.item_id not in json.dumps(payload) and b.revision_id not in json.dumps(payload)


@pytest.mark.parametrize('field',['owner_id','context_id','id'])
def test_snapshot_port_cannot_return_another_owner_space_or_resource(field):
    subject,scope,snapshot_id=uid(),uid(),uid()
    snapshot=ApprovedSnapshot(id=snapshot_id,context_id=scope,owner_id=subject,preview_id=uid(),
        fingerprint='0'*64,payload_json='{}',policy=policy(),approved_at=datetime.now(timezone.utc),exceptions=())
    repository=Mock(snapshot=AsyncMock(return_value=replace(snapshot,**{field:uid()})))
    service=DisclosureService(drafts=Mock(_allow=AsyncMock()),repository=repository)
    with pytest.raises(ProjectionUnavailable):run(service.snapshot(subject,scope,snapshot_id))
