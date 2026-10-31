"""Canonical support resolution, without a semantic reviewer or share-time inference."""
from copy import deepcopy
from uuid import uuid4

import pytest

from app.projections.disclosure_guard import OutboundDisclosureGuard
from tests.test_disclosure import policy
from tests.test_unified_recap import projected_documents


def root(rows):
    return next(r.content['extraction']['recap'] for r in rows if r.content['extraction'].get('recap'))


def test_protected_unrelated_basis_item_does_not_hide_canonical_recap():
    rows=projected_documents()
    before=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))[0]['recap']
    root(rows)['support_revision_ids']=[rows[0].revision_id]
    rows[1].content['text']='Diagnostic medical prive.'  # In the basis, not a declared support.
    frozen=deepcopy(rows)
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert payload['recap']==before and report['exclusions']
    assert rows==frozen


@pytest.mark.parametrize('quote',['Diagnostic medical prive.','Contact invite@example.test','Tél. 06 12 34 56 78'])
def test_undisclosed_support_quotations_do_not_hide_the_recap(quote):
    rows=projected_documents()
    support=next(r for r in rows if r.revision_id==root(rows)['support_revision_ids'][0])
    support.content['citations'][0]['quote']=quote
    payload,_=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert payload['recap']['title']==root(rows)['title'] and quote not in str(payload)


@pytest.mark.parametrize('excluded',['protected-support','shared-protected-quote'])
def test_excluded_support_stays_excluded_without_hiding_the_recap(excluded):
    rows=projected_documents()
    recap=root(rows)
    support=next(r for r in rows if r.revision_id==recap['support_revision_ids'][0])
    if excluded=='protected-support':support.content['text']='Diagnostic medical prive.'
    else:support.content['citations'][0]['quote']='Diagnostic medical prive.'
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context',include_quotes=True))
    assert payload['recap']=={'title':recap['title'],'text':recap['text']}
    assert support.revision_id in {e['revision_id'] for e in report['exclusions']}
    assert 'Diagnostic' not in str(payload) and support.revision_id not in str(payload)


@pytest.mark.parametrize('failure',['protected-text','masked-text','all-supports-protected',
    'foreign-support','wrong-version','missing-basis'])
def test_real_restrictions_and_unverified_supports_still_block_recap(failure):
    rows=projected_documents()
    recap=root(rows)
    support=next(r for r in rows if r.revision_id==recap['support_revision_ids'][0])
    include_quotes=False
    if failure=='protected-text':recap['text']='Diagnostic medical prive.'
    elif failure=='masked-text':recap['title']+=' 06 12 34 56 78'
    elif failure=='all-supports-protected':
        for row in rows:
            if row.revision_id in recap['support_revision_ids']:row.content['text']='Diagnostic medical prive.'
    elif failure=='foreign-support':recap['support_revision_ids']=[str(uuid4())]
    elif failure=='wrong-version':recap['format']='qh.context-recap/0'
    else:rows=[rows[0],*rows[2:]]
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context',include_quotes=include_quotes))
    assert 'recap' not in payload and report['recap_status']=='restricted'
