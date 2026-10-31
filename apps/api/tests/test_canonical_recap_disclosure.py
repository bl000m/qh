"""The shared recap is the persisted canonical recap: no filtering, rewriting or inference."""
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import pytest

from app.projections.disclosure_guard import OutboundDisclosureGuard
from tests.test_disclosure import policy
from tests.test_unified_recap import projected_documents


def root(rows):
    return next(r.content['extraction']['recap'] for r in rows if r.content['extraction'].get('recap'))


@pytest.mark.parametrize('change',['sensitive-support','sensitive-recap','support-quote','masked-text'])
def test_recap_is_shared_exactly_as_persisted_whatever_its_wording(change):
    rows=projected_documents()
    recap=root(rows)
    support=next(r for r in rows if r.revision_id==recap['support_revision_ids'][0])
    if change=='sensitive-support':support.content['text']='Diagnostic medical prive.'
    elif change=='sensitive-recap':recap['text']='Diagnostic medical prive.'
    elif change=='support-quote':support.content['citations'][0]['quote']='Tél. 06 12 34 56 78'
    else:recap['title']+=' 06 12 34 56 78'
    frozen=deepcopy(rows)
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert payload['recap']=={'title':recap['title'],'text':recap['text']} and report['recap_status']=='available'
    assert 'Tél.' not in str(payload['items']) and rows==frozen


@pytest.mark.parametrize('failure',['foreign-support','wrong-version','missing-basis','rejected-supports'])
def test_unverifiable_provenance_still_withholds_the_recap(failure):
    rows=projected_documents()
    recap=root(rows)
    if failure=='foreign-support':recap['support_revision_ids']=[str(uuid4())]
    elif failure=='wrong-version':recap['format']='qh.context-recap/0'
    elif failure=='missing-basis':rows=[rows[0],*rows[2:]]
    else:
        rows=[replace(r,validation_state='rejected') if r.revision_id in recap['support_revision_ids'] else r for r in rows]
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert 'recap' not in payload and report['recap_status']=='restricted'
