"""Documentation rehearsal: memory only, no credentials, SQL, graph or HTTP.

Scope UUIDs below are reproducible simulation IDs, NOT persistent import targets.
This does not exercise authenticated API, SQL idempotence or worker delivery.
"""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from adapters.llm.chat_mock import MockChatProvider
from adapters.llm.offline import FixtureUnderstandingProvider
from app.chat.context import build_context, decode_answer
from app.core.models import (
    CanonicalRevision, CanonicalSource, Message, MessageRole, RevisionRelation,
    RevisionTime,
)
from app.policy.models import PolicyDecision
from app.understanding.extractor import UnderstandingExtractor, digest


class MemoryOnlyRepository:
    subject_id = str(uuid5(NAMESPACE_URL, 'qh:demo-plan:simulation-owner'))

    def __init__(self):
        self.sources = {}
        self.revisions = []

    def save(self, *, sources=(), revisions=()):
        self.sources.update({s['id']: deepcopy(s) for s in sources})
        self.revisions = deepcopy(revisions)

    def read_sources(self, scopes, refs):
        return [deepcopy(self.sources[ref]) for ref in refs]


class SimulationPolicy:
    async def evaluate(self, request):
        return PolicyDecision(allowed=True)  # NOT an Alice/Bob authorization test.


async def main():
    path = Path('tests/fixtures/qh8_conversations.json')
    cases = json.loads(path.read_text())
    result = {'persistent_writes': False, 'network_calls': 0,
              'simulation_ids_are_not_persistent_targets': True,
              'fixture_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'created_at_placeholder': '2026-10-17T00:00:00.000000+00:00',
              'cases': []}
    for case in cases:
        scope = str(uuid5(NAMESPACE_URL, 'qh:demo-plan:simulation:' + case['name']))
        repo = MemoryOnlyRepository()
        extractor = UnderstandingExtractor(repository=repo, policy=SimulationPolicy(),
                                           provider=FixtureUnderstandingProvider(case['items']))
        args = dict(subject_id=repo.subject_id, context_id=scope)
        ref = await extractor.import_conversation(**args, conversation=case['conversation'])
        cp = await extractor.extract(**args, source_revision_id=ref,
                                     extraction_key='demo-a-fixture-v1-original')
        derived, audit = await extractor.resolve_citations(
            subject_id=repo.subject_id, checkpoint=cp,
            extraction_key='demo-a-fixture-v1-resolved')
        ids = await extractor.publish(subject_id=repo.subject_id, checkpoint=derived)
        assert ids == await extractor.publish(subject_id=repo.subject_id, checkpoint=derived)
        source = repo.sources[ref]
        rows = tuple(CanonicalRevision(
            context_space_id=scope, item_id=r['item_id'], revision_id=r['id'],
            revision_no=1, structural_kind=r['type_id'].rsplit('.', 1)[1],
            type_id=r['type_id'], type_version=1, content=r['content'],
            origin_kind=r['origin_kind'], validation_state=r['validation_state'],
            validated_by=None, validated_at=None, current_revision_id=None,
            is_current_confirmed=False, based_on_revision_id=None,
            created_at=result['created_at_placeholder'],
            temporal=RevisionTime(fact_from=None, fact_to=None, valid_from=None, valid_to=None),
            relation=RevisionRelation(**r['relation']) if r.get('relation') else None,
            provenance=(CanonicalSource(source_id=source['source_id'], source_revision_id=ref,
                                        revision_no=1, origin=source['origin']),),
        ) for r in sorted(repo.revisions, key=lambda r: r['id']))
        built = build_context(context_id=scope, revisions=rows, include_proposed=True,
                              messages=(Message(role=MessageRole.USER,
                                                content='Quelles décisions avons-nous prises ?'),))
        answer = await MockChatProvider().generate(built.request)
        _, declared, insufficient = decode_answer(answer.message, built)
        assert not insufficient and all(r.validation_state == 'proposed' for r in rows)
        result['cases'].append({
            'name': case['name'], 'conversation_sha256': digest(case['conversation']),
            'fixture_items_sha256': digest(case['items']), 'simulation_space_id': scope,
            'simulation_source_id': source['source_id'], 'simulation_source_revision_id': ref,
            'simulation_input_sha256': cp['input_sha256'],
            'original_output_sha256': digest(cp['output']),
            'derived_output_sha256': digest(derived['output']),
            'resolver_changed_output': cp['output'] != derived['output'],
            'resolver_version': audit['version'],
            'strict_valid_proposed_revisions': len(ids),
            'same_checkpoint_replay_ids_match': True,
            'simulation_revision_ids': list(ids),
            'chat_omitted_local_ids': [item['local_id'] for item, rid in
                                     zip(derived['output']['items'], ids)
                                     if rid not in {r.revision_id for r in built.revisions}],
            'chat': {'provided_revisions': len(built.revisions),
                     'declared_reference_ids': [r.revision_id for r in declared],
                     'partial': built.partial, 'context_bytes': built.context_bytes,
                     'input_bound_not_observed_tokens': built.input_bound,
                     'question': built.request.messages[-1].content,
                     'answer': json.loads(answer.message.content)['answer']},
        })
    print(json.dumps(result, ensure_ascii=False, indent=2))


asyncio.run(main())
