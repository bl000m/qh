"""Prepare the failed synthetic edge stage offline. Every HTTP send is mocked.

No option enables live HTTP. This reconstructs a candidate request, not the lost
response or proof that the unrecorded original request was byte-identical.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

import httpx
from adapters.context.factory import create_graphiti_engine
from adapters.context.graphiti import group_id
from graphiti_core.prompts import prompt_library
from graphiti_core.prompts.extract_edges import ExtractedEdges


async def prepare(ledger_path, audit_path, output):
    ledger = json.loads(ledger_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert ledger['metadata']['text'] == 'Bea founded Cedar Observatory.'
    entities = ledger['observations'][0]['result']['extracted_entities']
    assert {e['name'] for e in entities} == {'Bea', 'Cedar Observatory'}
    episode = audit['B_episodes'][0]
    assert episode['content'] == ledger['metadata']['text']
    for key, value in {'MISTRAL_API_KEY': 'synthetic-offline-only',
                       'MISTRAL_LLM_MODEL': 'ministral-8b-2512',
                       'MISTRAL_EMBEDDING_MODEL': 'mistral-embed',
                       'NEO4J_URI': 'bolt://localhost:7687', 'NEO4J_USER': 'synthetic',
                       'NEO4J_PASSWORD': 'synthetic'}.items():
        os.environ[key] = value
    adapter, sdk = await create_graphiti_engine()
    captured = []
    def capture(request):
        captured.append({'endpoint': str(request.url), 'body': json.loads(request.content),
                         'sha256': hashlib.sha256(request.content).hexdigest()})
        return httpx.Response(200, json={'choices': [{'message': {'content': '{"edges": []}'},
                                                      'finish_reason': 'stop'}]})
    await sdk._client.aclose()
    sdk._client = httpx.AsyncClient(transport=httpx.MockTransport(capture))
    try:
        from datetime import datetime
        context = {'episode_content': episode['content'], 'previous_episodes': [],
                   'nodes': [{'name': e['name'], 'entity_types': ['Entity']} for e in entities],
                   'reference_time': datetime.fromisoformat(episode['technical_reference_time']),
                   'edge_types': [], 'custom_extraction_instructions': ''}
        await adapter.client.llm_client.generate_response(prompt_library.extract_edges.edge(context),
            response_model=ExtractedEdges, max_tokens=16384,
            group_id=group_id(ledger['metadata']['scope']), prompt_name='extract_edges.edge')
        assert len(captured) == 1
        artifact = {'external_requests': 0, 'database_writes': 0,
                    'original_request_identity': 'not provable; original payload hash absent',
                    'original_response': 'missing; never reconstructed',
                    'provenance': ledger['metadata'], 'request': captured[0]}
        with output.open('x') as handle:
            json.dump(artifact, handle, indent=2)
        print('PASS: offline candidate edge request prepared; no external HTTP or database writes')
    finally:
        await adapter.close()
        await sdk.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(prepare(args.ledger, args.audit, args.output))


if __name__ == '__main__':
    main()
