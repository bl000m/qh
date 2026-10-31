"""Canonical support resolution, without a semantic reviewer or share-time inference."""
from copy import deepcopy
from uuid import uuid4

import pytest

from app.projections.disclosure_guard import OutboundDisclosureGuard
from tests.test_disclosure import policy
from tests.test_modular_recap import projected_documents


def test_protected_unrelated_basis_item_does_not_hide_canonical_recap():
    rows=projected_documents()
    before=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))[0]['recap']
    rows[1].content['text']='Diagnostic medical prive.'
    frozen=deepcopy(rows)
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert payload['recap']==before and report['exclusions']
    assert rows==frozen


@pytest.mark.parametrize('failure',['protected-text','protected-support','protected-quote','masked-quote',
    'foreign-source','missing-citation','missing-support','wrong-version','missing-basis'])
def test_real_restrictions_and_unverified_supports_still_block_recap(failure):
    rows=projected_documents()
    general=next(c for row in rows for c in row.content['extraction'].get('recap_components',[]) if c['kind']=='general')
    support=next(r for r in rows if r.revision_id==general['support_revision_ids'][0])
    if failure=='protected-text':general['text']='Diagnostic medical prive.'
    elif failure=='protected-support':support.content['text']='Diagnostic medical prive.'
    elif failure=='protected-quote':support.content['citations'][0]['quote']='Diagnostic medical prive.'
    elif failure=='masked-quote':support.content['citations'][0]['quote']='Contact invite@example.test'
    elif failure=='foreign-source':support.content['citations'][0]['source_revision_id']=str(uuid4())
    elif failure=='missing-citation':support.content.pop('citations')
    elif failure=='missing-support':general['support_revision_ids']=[str(uuid4())]
    elif failure=='wrong-version':general['version_id']=str(uuid4())
    else:rows=rows[:2]
    # Hiding citations in the UI cannot bypass their privacy/provenance checks.
    for include_quotes in (False,True):
        payload,_=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context',include_quotes=include_quotes))
        assert 'recap' not in payload
