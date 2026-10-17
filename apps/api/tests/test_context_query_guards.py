"""Hydration and concurrency failure injection independent of the HTTP fixture."""

import asyncio
from copy import deepcopy

import pytest

from adapters.context.hydration import hydrate
from adapters.context.incremental import IncrementalContextEngine
from adapters.context.native import NativeContextError
from app.core.models import (ContextQuery, ContextResult, ContextSearchHit,
                             ContextRetrievalUnavailable, ItemRevisionRef)
from tests.test_native_context import FIXTURE


class Repository:
    def __init__(self):
        self.snapshot=deepcopy(FIXTURE)
        for row in self.snapshot['understanding_item_revisions']:
            row['current_revision_id']=None
        self.version=1
        self.advance=False

    def read_snapshot(self,scopes,ids):
        if self.advance:self.version+=1
        return dict(context_ids=list(scopes),source_revisions=self.snapshot['source_revisions'],
                    understanding_item_revisions=[r for r in self.snapshot['understanding_item_revisions'] if r['id'] in ids])


def case():
    repo=Repository();row=repo.snapshot['understanding_item_revisions'][0]
    query=ContextQuery(context_ids=(row['context_space_id'],),text='Cedar',view='history')
    return repo,row,query


@pytest.mark.parametrize('bad',['missing','duplicate','source','scope','citation','current'])
def test_canonical_payload_and_provenance_fail_closed(bad):
    repo,row,query=case();id=row['id']
    if bad=='missing':repo.snapshot['understanding_item_revisions']=[]
    if bad=='duplicate':repo.snapshot['understanding_item_revisions'].append(deepcopy(row))
    if bad=='source':repo.snapshot['source_revisions']=[]
    if bad=='scope':row['context_space_id']='foreign'
    if bad=='citation':row['content']['citations']=[dict(source_revision_id=row['provenance'][0],start=0,end=4,quote='fake')]
    if bad=='current':row['current_revision_id']='missing'
    with pytest.raises(NativeContextError):hydrate(repo,query,[id])


def test_changed_during_final_hydration_is_unavailable():
    repo,row,query=case()
    engine=IncrementalContextEngine(repo,None)
    engine._ready=lambda scopes:{(scopes[0],'epoch',repo.version)}
    hit=ContextSearchHit(id='test',context_id=query.context_ids[0],excerpt='Cedar',provenance=(),
                        item_revision=ItemRevisionRef(context_id=query.context_ids[0],item_id=row['item_id'],revision_id=row['id']))
    async def selected(q):return ContextResult(hits=(hit,))
    engine._text_search=selected
    repo.advance=True
    with pytest.raises(ContextRetrievalUnavailable,match='^Context retrieval unavailable$'):
        asyncio.run(engine.search(query))


def test_core_canonical_payloads_import_without_frameworks():
    import subprocess
    import sys
    from tests.test_architecture import API_ROOT
    result=subprocess.run([sys.executable,'-I','-S','-c',
        'import sys;sys.path.insert(0,sys.argv[1]);from app.core.models import CanonicalRevision,ContextQuery',str(API_ROOT)],
        capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
