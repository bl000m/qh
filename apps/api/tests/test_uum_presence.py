"""Presence is a consistent graph-verified read, never a page-local count."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app.context.presence import dimension_presence
from app.core.models import ContextRetrievalUnavailable
from app.core.uum import PRIMARY_DIMENSIONS


def test_seven_bounded_reads_same_projection_and_no_global_counts():
    queries=[]
    async def browse(request):
        queries.append(request.query)
        return SimpleNamespace(projection_token=(('scope','epoch',4),), revisions=('authorized',) if request.query.primary_dimension=='open_questions' else ())
    result=asyncio.run(dimension_presence(Mock(browse=browse),'owner','scope','proposed'))
    assert len(queries)==7 and all(q.limit==1 and q.latest_pending for q in queries)
    assert [q.primary_dimension for q in queries[:-1]]==list(PRIMARY_DIMENSIONS)
    assert queries[-1].primary_unclassified
    assert result['dimensions']['open_questions'] and sum(result['dimensions'].values())==1
    assert not result['unclassified'] and 'count' not in result


@pytest.mark.parametrize('tokens', [(), (('scope','other-epoch',4),), (('scope','epoch',5),)])
def test_projection_change_or_missing_consistency_proof_aborts_entire_response(tokens):
    context=Mock(browse=AsyncMock(side_effect=[
        SimpleNamespace(projection_token=(('scope','epoch',4),),revisions=()),
        SimpleNamespace(projection_token=tokens,revisions=())]))
    with pytest.raises(ContextRetrievalUnavailable):
        asyncio.run(dimension_presence(context,'owner','scope','current'))


def test_history_cannot_be_presented_as_current_presence():
    context=Mock()
    with pytest.raises(ValueError):asyncio.run(dimension_presence(context,'owner','scope','history'))
    context.browse.assert_not_called()
