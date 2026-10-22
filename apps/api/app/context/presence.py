"""Bounded, owner-authorized UUM presence; every read verifies the operational graph."""
from app.core.models import ContextBrowse, ContextRequest, ContextRetrievalUnavailable
from app.core.uum import PRIMARY_DIMENSIONS


async def dimension_presence(context, subject, scope, view):
    if view not in ('current', 'proposed'):
        raise ValueError('Explicit current or proposed view required')
    token, dimensions = None, {}
    for dimension in (*PRIMARY_DIMENSIONS, None):
        result = await context.browse(ContextRequest(subject_id=subject,
            query=ContextBrowse(context_id=scope, view=view, limit=1,
                primary_dimension=dimension, primary_unclassified=dimension is None,
                latest_pending=view == 'proposed')))
        if not result.projection_token or token is not None and token != result.projection_token:
            raise ContextRetrievalUnavailable('Projection changed during presence read')
        token = result.projection_token
        dimensions[dimension or 'unclassified'] = bool(result.revisions)
    return dict(context_id=scope, view=view, dimensions={d: dimensions[d] for d in PRIMARY_DIMENSIONS},
        unclassified=dimensions['unclassified'])
