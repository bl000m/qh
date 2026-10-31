"""Offline loading orchestration; exact authorized browse remains the boundary."""
import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.models import ContextSpaceNotFound, ContextRetrievalUnavailable
from app.understanding.enrichment import EnrichmentUnavailable
from tests.test_consolidation import fixture


@dataclass
class Revision:
    revision_id: str
    content: dict = field(default_factory=dict)


def test_exact_batch_is_ordered_and_never_generates():
    service, who, scope, repo, ai, _ = fixture()
    ids = [str(i) for i in range(12)]
    current = dict(id='version', revision_ids=ids)
    stored_recap = dict(format='qh.context-recap/1', version_id='version',
        basis_revision_ids=ids, support_revision_ids=['0'], title='Stored title', text='Stored summary.')
    rows = {id: Revision(id) for id in ids}
    rows['0'].content = dict(extraction=dict(recap=stored_recap))
    repo.read.return_value = dict(current=current, understanding_ids=ids, intake=['saved conversation'])
    async def browse(request):
        assert request.subject_id == who.subject_id
        assert request.query.context_id == scope and request.query.view == 'history'
        assert request.query.revision_ids == tuple(ids)
        return SimpleNamespace(revisions=tuple(rows[id] for id in reversed(ids)))

    service.context.browse.side_effect = browse
    result = asyncio.run(service.read(who.subject_id, scope))
    assert [row['revision_id'] for row in result['understanding']] == ids
    assert result['intake'] == ['saved conversation']
    assert result['recap']['text'] == 'Stored summary.'
    service.context.browse.assert_awaited_once()
    ai.authorize_consolidation.assert_not_called()
    ai._provider.assert_not_called()
    repo.claim.assert_not_called()


@pytest.mark.parametrize('failure', ['missing', 'different', 'duplicate', 'graph'])
def test_batch_read_fails_closed_on_any_unavailable_exact_revision(failure):
    service, who, scope, repo, ai, _ = fixture()
    repo.read.return_value = dict(current=None, understanding_ids=['first', 'second'])

    async def browse(request):
        if failure == 'graph':
            raise ContextRetrievalUnavailable('Offline stale graph')
        rows = (Revision('first'),)
        if failure == 'different':
            rows += (Revision('other'),)
        if failure == 'duplicate':
            rows += (Revision('second'), Revision('second'))
        return SimpleNamespace(revisions=rows)

    service.context.browse.side_effect = browse
    with pytest.raises((EnrichmentUnavailable, ContextRetrievalUnavailable)):
        asyncio.run(service.read(who.subject_id, scope))
    ai._provider.assert_not_called()


def test_policy_is_rechecked_before_disclosing_loaded_workspace():
    service, who, scope, repo, _, _ = fixture()
    repo.read.return_value = dict(current=None, understanding_ids=[])
    service.policy.evaluate = AsyncMock(side_effect=[SimpleNamespace(allowed=True), SimpleNamespace(allowed=False)])
    with pytest.raises(ContextSpaceNotFound):
        asyncio.run(service.read(who.subject_id, scope))
    repo.read.assert_awaited_once_with(scope)


def test_empty_workspace_still_checks_graph_availability():
    service, who, scope, repo, _, _ = fixture()
    repo.read.return_value = dict(current=None, understanding_ids=[])
    service.context.browse.side_effect = ContextRetrievalUnavailable('Offline stale graph')
    with pytest.raises(ContextRetrievalUnavailable):
        asyncio.run(service.read(who.subject_id, scope))


def test_internal_batch_rejects_unbounded_or_ambiguous_selection():
    from app.core.models import ContextBrowse
    for selection in [('same', 'same'), tuple(str(i) for i in range(101)), ['id']]:
        with pytest.raises(ValueError):
            ContextBrowse(context_id='scope', view='history', revision_ids=selection)
    with pytest.raises(ValueError):
        ContextBrowse(context_id='scope', view='history', revision_id='one', revision_ids=('two',))
