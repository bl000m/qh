"""Lossless internal compaction, collisions, budgets and canonical state; offline."""
from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from app.chat.context import ChatContextUnavailable, MAX_CONTEXT_BYTES, MAX_INPUT_BOUND
from app.chat.references import encode_model_context as compact_context, expand_model_context as expand_context
from app.core.models import CanonicalSource, RevisionRelation, RevisionTime
from tests.test_chat_context import built, revision


def source(**changes):
    return CanonicalSource(**(dict(source_id='source', source_revision_id='source-r1',
        revision_no=1, origin={'kind':'conversation','turns':[{'speaker':'Alex','text':'Été 🌿'}]}) | changes))


def with_source(**changes):
    return revision(provenance=(source(),), **changes)


def json_records(rows):
    return json.loads(json.dumps([asdict(row) for row in rows], ensure_ascii=False))


def test_full_canonical_roundtrip_shared_source_mixed_state_time_and_relation():
    first=with_source()
    second=with_source(revision_id='relation',item_id='relation-item',structural_kind='relation',
        type_id='qh.generic.relation',validation_state='proposed',validated_by=None,validated_at=None,
        current_revision_id=None,is_current_confirmed=False,
        temporal=RevisionTime(fact_from='2026-10-18T08:00:00Z',fact_to=None,valid_from=None,valid_to=None),
        relation=RevisionRelation(predicate='reported_by',source_item_id='item',source_revision_id='revision',
                                  target_item_id='entity',target_revision_id='entity-r1'),
        content={'text':'Hypothèse, pas une décision. 🌿','descriptors':[{'value':'hypothesis','certainty':'tentative'}],
                 'citations':[{'source_revision_id':'source-r1','start':0,'end':5,'quote':'Été 🌿'}]})
    rows=(first,second);context=built(rows,include_proposed=True)
    packet=json.loads(context.request.messages[1].content)
    assert len(packet['sources'])==1
    assert expand_context(packet)==json_records(rows)
    assert packet['revisions'][0]['validation_state']=='confirmed'
    assert packet['revisions'][1]['validation_state']=='proposed'
    assert 'validation_state' not in packet['common_metadata']
    assert context.revisions==rows and not context.partial
    assert context.context_bytes==len(context.request.messages[1].content.encode('utf-8'))
    assert context.input_bound<=MAX_INPUT_BOUND


@pytest.mark.parametrize('change',[
    {'source_id':'different'}, {'origin':{'kind':'different'}}, {'revision_no':2},
])
def test_same_source_revision_with_conflicting_content_is_rejected(change):
    rows=(with_source(), revision(revision_id='second',provenance=(source(**change),)))
    with pytest.raises(ChatContextUnavailable):built(rows)


def test_json_boolean_numeric_collision_cannot_silently_change_source_content():
    a=revision(provenance=(source(origin={'value':True}),))
    b=revision(revision_id='second',provenance=(source(origin={'value':1}),))
    with pytest.raises(ChatContextUnavailable):built((a,b))


def test_source_identity_number_cannot_have_two_revision_ids():
    rows=(with_source(), revision(revision_id='second',provenance=(source(source_revision_id='other-r1'),)))
    with pytest.raises(ChatContextUnavailable):built(rows)


def test_collision_in_budget_excluded_record_still_fails_closed():
    huge=revision(revision_id='huge',content={'text':'𐍈'*10000},
                  provenance=(source(origin={'kind':'conflict'}),))
    with pytest.raises(ChatContextUnavailable):built((with_source(),huge))


def test_duplicate_provenance_is_rejected_not_deduplicated_lossily():
    with pytest.raises(ChatContextUnavailable):built((revision(provenance=(source(),source())),))


def test_foreign_scope_cannot_hide_behind_shared_metadata_or_shared_source():
    with pytest.raises(ChatContextUnavailable):built((with_source(),with_source(context_space_id='foreign',revision_id='other')))


def test_excluded_record_does_not_disclose_its_distinct_source():
    huge=revision(revision_id='huge',content={'text':'𐍈'*10000},provenance=(source(source_id='huge-source',source_revision_id='huge-r1'),))
    context=built((with_source(),huge))
    packet=json.loads(context.request.messages[1].content)
    assert context.partial and context.revisions==(with_source(),)
    assert set(packet['sources'])=={'source-r1'}
    assert expand_context(packet)==json_records(context.revisions)
    assert context.context_bytes<=MAX_CONTEXT_BYTES


@pytest.mark.parametrize('value',[float('nan'),float('inf'),{1,2}])
def test_invalid_extension_json_fails_closed(value):
    with pytest.raises(ChatContextUnavailable):built((revision(content={'text':'x','extension':value}),))


@pytest.mark.parametrize('mode',['scope','missing_source','extra_source','source_key','overlap','missing_field','duplicate_id'])
def test_malformed_compact_context_rejected(mode):
    packet=json.loads(built((with_source(),)).request.messages[1].content)
    if mode=='scope':packet['context_space_id']='foreign'
    elif mode=='missing_source':packet['sources'].clear()
    elif mode=='extra_source':packet['sources']['unused']=asdict(source(source_revision_id='unused',source_id='extra'))
    elif mode=='source_key':packet['sources']['source-r1']['source_revision_id']='forged'
    elif mode=='overlap':packet['revisions'][0]['context_space_id']='space'
    elif mode=='missing_field':packet['revisions'][0].pop('content')
    elif mode=='duplicate_id':packet['revisions'].append(deepcopy(packet['revisions'][0]))
    with pytest.raises(ValueError):expand_context(packet)


def test_empty_and_exact_byte_boundary_and_partial_flag():
    empty=json.loads(built().request.messages[1].content)
    assert expand_context(empty)==[] and not empty['sources']
    row=with_source(content={'text':''})
    initial=json_records((row,))
    overhead=len(compact_context('space',initial,partial=False).encode())
    exact=replace(row,content={'text':'x'*(MAX_CONTEXT_BYTES-overhead)})
    context=built((exact,))
    assert context.context_bytes==MAX_CONTEXT_BYTES and context.revisions==(exact,) and not context.partial
    excluded=built((replace(exact,content={'text':exact.content['text']+'x'}),))
    assert excluded.partial and not excluded.revisions
    assert not json.loads(excluded.request.messages[1].content)['sources']


def test_formatter_is_deterministic_and_does_not_mutate_canonical_metadata():
    row=with_source();before=deepcopy(asdict(row))
    first=built((row,));second=built((row,))
    assert first==second and asdict(row)==before
