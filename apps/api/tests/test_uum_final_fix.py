"""Focused final correction: simulated HTTP only, no runtime data or paid calls."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest

from adapters.llm.mistral import MistralProvider, ExperimentBudget
from adapters.postgres.enrichment import PostgresEnrichmentRepository
from app.understanding.enrichment import EnrichmentConflict
from app.understanding.uum import FORMAT, OUTPUT_SCHEMA, normalize_output
from tests.test_enrichment import setup, payload


@pytest.mark.parametrize('empty', [False, True])
def test_fictional_understanding_or_legitimate_empty_keeps_exact_evidence_atomic_and_idempotent(tmp_path, monkeypatch, empty):
    monkeypatch.setenv('MISTRAL_API_KEY', 'synthetic-only')
    quote='Dans cet exemple fictif, je souhaite organiser un atelier photo.'
    assistant='**Suggestion** : louer un studio ne constitue pas votre décision.'
    item=dict(text='Dans cet exemple fictif, l’utilisateur souhaite organiser un atelier photo.',
        primary_dimension='objectives_intentions', assignment_certainty='asserted', evidence=[dict(quote=quote)])
    value=dict(format=FORMAT, items=[] if empty else [item]); sent=[]
    def response(req):
        body=json.loads(req.content);sent.append(body)
        assert body['response_format']==dict(type='json_schema', json_schema=dict(name='qh_atomic_understanding', schema=OUTPUT_SCHEMA, strict=True))
        assert 'Fictional, hypothetical and simulated' in body['messages'][0]['content']
        assert 'INCLUDING Markdown markers' in body['messages'][0]['content']
        return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=500,completion_tokens=200),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(value)))]))
    delegate=MistralProvider(budget=ExperimentBudget(tmp_path/'ledger.json',create=True),transport=httpx.MockTransport(response))
    repo,_,_,service=setup();service.uum=True
    data=payload(quote);data['turns'].append(dict(id=str(uuid4()),role='assistant',content=assistant,captured_at=data['turns'][0]['captured_at']));data['extraction_mode']='semantic';scope=str(uuid4())
    async def run():
        result=await service.enrich(repo.subject_id,scope,data,semantic_provider=delegate,provider_mode='uum-mistral/3')
        replay=await service.enrich(repo.subject_id,scope,data,semantic_provider=delegate,provider_mode='uum-mistral/3')
        return result,replay
    result,replay=asyncio.run(run());assert replay['replayed'] and len(sent)==repo.calls==1
    source,rows=next(iter(repo.saved.values()))[2:];assert quote in source['content'] and assistant in source['content']
    assert len(rows)==len(result['revision_ids'])==(0 if empty else 1)
    if rows:
        assert rows[0]['validation_state']=='proposed'
        assert rows[0]['content']['primary_dimension']['value']=='objectives_intentions'
        assert rows[0]['content']['citations'][0]['quote']==quote
    # Exercise the actual SQL adapter's replay admission, retaining fingerprint/owner.
    sql=PostgresEnrichmentRepository(url=None,subject_id=repo.subject_id)
    cursor=Mock();cursor.execute.side_effect=[Mock(fetchone=lambda:dict(origin=source['origin'])),Mock(fetchall=lambda:[dict(id=i) for i in result['revision_ids']])]
    assert sql._find_on(cursor,scope,source['id'],source['origin']['metadata']['request_sha256'])['replayed']
    cursor.execute.side_effect=[Mock(fetchone=lambda:dict(origin=source['origin']))]
    with pytest.raises(EnrichmentConflict):sql._find_on(cursor,scope,source['id'],'foreign-fingerprint')


def test_format_and_markdown_quotes_remain_strict_without_any_repairs():
    from tests.test_uum import source, wire
    text='**Budget** : 500 euros dans cet exemple fictif.'
    original=wire(text, 'constraints_preferences');snapshot=deepcopy(original)
    assert normalize_output(original,source(text))['items']
    assert original==snapshot
    del original['format']
    with pytest.raises(ValueError):normalize_output(original,source(text))
    original['format']=FORMAT;original['items'][0]['evidence'][0]['quote']=text.replace('**','')
    with pytest.raises(ValueError):normalize_output(original,source(text))
