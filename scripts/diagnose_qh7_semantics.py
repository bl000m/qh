"""Offline investigation of saved synthetic QH-7 results, never a live API smoke.

Requires the existing local Neo4j credentials and saved experiment checkpoints.
Every SDK request uses httpx.MockTransport and a synthetic API key. No semantic
state is persisted; Graphiti transformations are replayed in memory.
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from adapters.context.factory import create_graphiti_engine
from adapters.context.graphiti import episode_id
from app.core.models import ContextId, SourceId, SourceRevisionId, SourceRevisionRef
from graphiti_core.nodes import EpisodicNode, EntityNode
from graphiti_core.prompts import prompt_library
from graphiti_core.prompts.extract_nodes import ExtractedEntities, SummarizedEntities
from graphiti_core.prompts.extract_edges import ExtractedEdges
from graphiti_core.utils.maintenance.node_operations import _build_entity_types_context, extract_attributes_from_nodes
from graphiti_core.utils.maintenance.edge_operations import extract_edges

logging.disable(logging.CRITICAL)

async def main():
    parser=argparse.ArgumentParser(description="Replay QH-7 semantic failures locally; SDK HTTP is mocked, Neo4j reads only.")
    parser.add_argument('--ledger',required=True)
    parser.add_argument('--first-result',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    ledger=json.loads(Path(args.ledger).read_text())
    prior=json.loads(Path(args.first_result).read_text())
    records={r['number']:r for r in ledger['requests']}
    os.environ['MISTRAL_API_KEY']='synthetic-offline-diagnosis'
    os.environ['MISTRAL_LLM_MODEL']='ministral-3b-2512'
    adapter,sdk=await create_graphiti_engine()
    await sdk._client._transport.inner.aclose()
    captured=[]
    reply={}
    def capture(request):
        # This mock never forwards to a network transport.
        body=bytes(request.content)
        captured.append({'sha256':hashlib.sha256(body).hexdigest(),'body':json.loads(body)})
        return httpx.Response(200,json={'id':'offline','object':'chat.completion','created':0,
            'model':'ministral-3b-2512','choices':[{'index':0,'finish_reason':'stop','message':{
                'role':'assistant','content':json.dumps(reply)}}]})
    # Exercise SDK serialization offline while keeping default-deny real transport unused.
    await sdk._client.aclose()
    sdk._client=httpx.AsyncClient(transport=httpx.MockTransport(capture))
    result={'external_requests':0,'database_writes':0,'prompt_hashes':{},'checks':{}}
    episodes={}
    try:
        for label in ('A','B'):
            row=next(x for x in ledger['functional'] if x.get('ingested')==label)
            ref=SourceRevisionRef(source_id=SourceId(row['source_id']),revision_id=SourceRevisionId(row['revision_id']))
            episodes[label]=await EpisodicNode.get_by_uuid(adapter.client.driver,episode_id(ContextId(ledger['spaces'][label]),ref))
        for label,expected,answer in (('A',prior['request']['payload_sha256'],prior['extraction']),
                                      ('B',records[4]['payload_sha256'],records[4]['result'])):
            ep=episodes[label]
            context={'entity_types':_build_entity_types_context(None),'episode_content':ep.content,
                     'custom_extraction_instructions':''}
            reply.clear();reply.update(answer)
            await adapter.client.llm_client.generate_response(prompt_library.extract_nodes.extract_text(context),
                response_model=ExtractedEntities,group_id=ep.group_id,prompt_name='extract_nodes.extract_text')
            result['prompt_hashes'][label+'_entities']={'expected':expected,'reconstructed':captured[-1]['sha256'],
                'match':captured[-1]['sha256']==expected}
        a,b=captured[0]['body'],captured[1]['body']
        result['checks']['entity_requests_equal_after_Ada_Bea_substitution']=json.dumps(a)==json.dumps(b).replace('Bea founded','Ada founded')
        ep=episodes['B']
        context={'previous_episodes':[],'episode_content':ep.content,
                 'nodes':[{'name':'Cedar Observatory','entity_types':['Entity']}],
                 'reference_time':ep.valid_at,'edge_types':[],'custom_extraction_instructions':''}
        reply.clear();reply.update(records[5]['result'])
        await adapter.client.llm_client.generate_response(prompt_library.extract_edges.edge(context),
            response_model=ExtractedEdges,max_tokens=16384,group_id=ep.group_id,prompt_name='extract_edges.edge')
        result['prompt_hashes']['B_edges']={'expected':records[5]['payload_sha256'],'reconstructed':captured[-1]['sha256'],
            'match':captured[-1]['sha256']==records[5]['payload_sha256']}
        edge_body=captured[-1]['body']
        summary_context={'entities':[{'name':'Cedar Observatory','summary':'','entity_types':['Entity'],'attributes':{}}],
                         'episode_content':ep.content,'previous_episodes':[],'entity_type_descriptions':{}}
        reply.clear();reply.update(records[6]['result'])
        await adapter.client.llm_client.generate_response(prompt_library.extract_nodes.extract_summaries_batch(summary_context),
            response_model=SummarizedEntities,group_id=ep.group_id,prompt_name='extract_nodes.extract_summaries_batch')
        result['prompt_hashes']['B_summary']={'expected':records[6]['payload_sha256'],'reconstructed':captured[-1]['sha256'],
            'match':captured[-1]['sha256']==records[6]['payload_sha256']}
        summary_body=captured[-1]['body']
        result['checks']['2023_absent_from_summary_request']='2023' not in json.dumps(summary_body)
        result['checks']['technical_reference_timestamp']=ep.valid_at.isoformat()
        result['checks']['edge_time_equals_episode_reference']=records[5]['result']['edges'][0]['valid_at']==ep.valid_at.isoformat().replace('+00:00','Z')
        result['checks']['A_edge_time_equals_episode_reference']=records[2]['result']['edges'][0]['valid_at']==episodes['A'].valid_at.isoformat().replace('+00:00','Z')
        result['checks']['source_has_no_explicit_date']=ep.content=='Bea founded Cedar Observatory.'
        result['checks']['entity_schema_accepts_missing_Bea']=bool(ExtractedEntities.model_validate(records[4]['result']))
        result['checks']['edge_schema_accepts_unknown_endpoint']=bool(ExtractedEdges.model_validate(records[5]['result']))
        result['checks']['summary_schema_accepts_unsupported_year']=bool(SummarizedEntities.model_validate(records[6]['result']))
        result['checks']['edge_prompt_requires_listed_endpoints']='must use only the' in json.dumps(edge_body)
        class Replay:
            def __init__(self): self.calls=[]
            async def generate_response(self,*args,**kwargs):
                name=kwargs['prompt_name'];self.calls.append(name)
                return records[5 if name=='extract_edges.edge' else 6]['result']
        replay=Replay()
        embedder=SimpleNamespace(create_batch=AsyncMock(return_value=[[0.0]*1024]))
        clients=SimpleNamespace(llm_client=replay,embedder=embedder)
        node=EntityNode(name='Cedar Observatory',group_id=ep.group_id,labels=['Entity'],summary='',attributes={},created_at=ep.created_at)
        edges=await extract_edges(clients,ep,[node],[],{('Entity','Entity'):[]},ep.group_id,None)
        result['replay']={'returned_edges':len(edges),'llm_calls':list(replay.calls)}
        await extract_attributes_from_nodes(clients,[node],ep,[],None,edges=edges)
        result['replay']['summary_after_graphiti']=node.summary
        result['replay']['llm_calls']=replay.calls
        result['checks']['all_reconstructed_hashes_match']=all(x['match'] for x in result['prompt_hashes'].values())
        # Proposed smoke-only guards: report defects, never fill in missing facts.
        actual={x['name'] for x in records[4]['result']['extracted_entities']}
        result['proposed_guards']={'missing_expected_fixture_entities':sorted({'Bea','Cedar Observatory'}-actual),
            'unknown_edge_endpoints':sorted({e[k] for e in records[5]['result']['edges'] for k in ('source_entity_name','target_entity_name')}-actual),
            'unsupported_summary_years':['2023'] if '2023' in records[6]['result']['summaries'][0]['summary'] and '2023' not in ep.content else []}
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))
    finally:
        await adapter.close();await sdk.close()
asyncio.run(main())
