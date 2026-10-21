"""Synthetic QH-8 fixture → actual extractor → canonical proposed revisions.

Only called by the explicitly isolated QH-12 harness. No LLM HTTP, persistent QH
write or claim of human confirmation. Confirmed/rejected states below are test
fixtures with an explicit synthetic actor, never changes to original proposals.
"""
import json
import asyncio
from copy import deepcopy
import os
from types import SimpleNamespace
from uuid import uuid4

from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.demo_identities import DEMO_IDENTITIES
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.semantic_profiles import register_generic_profiles
from app.policy.owner import OwnerPolicyService
from tests.test_understanding import CASES
from tests.test_understanding_pipeline import import_extract

assert os.environ.get('QH12_BROWSER_TEST') == '1'
assert os.environ['POSTGRES_HOST'] == 'postgres' and os.environ['POSTGRES_DB'] == 'qh'
owner = str(DEMO_IDENTITIES[0][1])
repo = CanonicalRepository(url=database_url(), subject_id=owner)
scope = str(uuid4())
with repo.connect() as connection:
    assert connection.execute('SELECT version_num FROM alembic_version').fetchone()['version_num'] == '0006_owner_organization'
    connection.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Démo QH-8')", (scope, owner))
register_generic_profiles(repo)
if os.environ.get('QH51_SEMANTIC_BROWSER_TEST')=='1':
    from adapters.postgres.semantic_profiles import register_semantic_profiles
    register_semantic_profiles(repo)
policy = OwnerPolicyService(owner_for=PostgresSecurityReader(url=repo.url).owner_for)
p = {'repo': repo, 'scope': scope, 'service': SimpleNamespace(policy=policy)}
usecase, provider, source_ref, checkpoint = import_extract(p, CASES[0], key='qh12-offline-demo')
asyncio.run(usecase.publish(subject_id=owner, checkpoint=checkpoint))
assert provider.calls == 1  # Deterministic fixture port, never a paid/network provider.
original = repo.read_snapshot((scope,))['understanding_item_revisions']
choice = next(row for row in original if {'value': 'decision', 'certainty': 'asserted'} in row['content'].get('descriptors', []))
clones = []
for number, state in [(2, 'confirmed'), (3, 'proposed'), (4, 'rejected')]:
    row = deepcopy(choice)
    row.update(id=str(uuid4()), revision_no=number, based_on_revision_id=choice['id'], validation_state=state)
    row.pop('created_at'); row.pop('current_revision_id')
    if state != 'proposed':
        row.update(validated_by=owner, validated_at='2026-10-17T12:00:00Z')
    clones.append(row)
# Separate test-only meanings, not repairs of QH-8 output.
base = dict(context_space_id=scope, revision_no=1, type_version=1,
            origin_kind='human', validation_state='proposed', provenance=[source_ref])
timestamp = dict(base, id=str(uuid4()), item_id=str(uuid4()), type_id='qh.generic.entity',
                 content={'text': 'Report timestamp 2026-10-01T12:00:00Z.',
                          'descriptors': [{'value': 'reported_timestamp', 'certainty': 'asserted'}]},
                 fact_from='2026-10-01T12:00:00Z', fact_to='2026-10-01T12:00:00Z')
legacy = dict(base, id=str(uuid4()), item_id=str(uuid4()), type_id='qh.decision',
              content={'legacy_note': 'Opaque bibliography control', 'citations': 'Bibliography, not a QH-8 locator',
                       'descriptors': [{'value': 'bibliography', 'certainty': 'asserted'},
                                       {'value': 'opaque_attribute', 'certainty': {'toString': None}}]})
repo.save(revisions=[*clones, timestamp, legacy])
with repo.connect() as connection:
    connection.execute('UPDATE understanding_items SET current_revision_id=%s WHERE id=%s', (clones[0]['id'], choice['item_id']))
print('PASS: QH-8 fake-provider batch and distinct revision/time/legacy controls published to test DB only')

# Additional browse controls are isolated fixtures, never a persistent demo seed.
empty_scope, proposed_scope, historical_scope = (str(uuid4()) for _ in range(3))
with repo.connect() as connection:
    for id, name in [(empty_scope,'Empty navigation control'),(proposed_scope,'Proposals-only control'),(historical_scope,'History-only control')]:
        connection.execute('INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,%s)',(id,owner,name))
source = repo.read_sources((scope,),(source_ref,))[0]
for id,state in [(proposed_scope,'proposed'),(historical_scope,'rejected')]:
    copy_source = dict(source,id=str(uuid4()),source_id=str(uuid4()),context_space_id=id)
    copy_row = deepcopy(base)
    copy_row.update(id=str(uuid4()),item_id=str(uuid4()),context_space_id=id,
        type_id='qh.generic.item', content={'text':'Explicit isolated navigation control.', 'descriptors':[{'value':'Previously unseen Ω','certainty':'tentative'}, {'value':'control','certainty':'asserted'}]},
        validation_state=state,provenance=[copy_source['id']])
    if state=='rejected':copy_row.update(validated_by=owner,validated_at='2026-10-17T12:00:00Z')
    repo.save(sources=[copy_source],revisions=[copy_row])

# Three original proposed-only conversations for QH-13 navigation/compaction guards.
# This script is gated to the disposable harness above, never the persistent VPS.
demo_spaces = []
for case, name in zip(CASES, ('Projet pilote', 'Bien-être', 'Organisation personnelle')):
    demo_scope = str(uuid4())
    with repo.connect() as connection:
        connection.execute('INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,%s)', (demo_scope,owner,name))
    demo_p = {'repo':repo, 'scope':demo_scope, 'service':SimpleNamespace(policy=policy)}
    demo_usecase, _, demo_source, demo_cp = import_extract(demo_p,case,key='qh13-navigation-control')
    demo_ids = asyncio.run(demo_usecase.publish(subject_id=owner,checkpoint=demo_cp))
    demo_spaces.append(dict(scope=demo_scope,name=name,revision_ids=demo_ids,source_revision_id=demo_source))

# Disposable owner-review Space, independent of prior browse/search expectations.
review_scope = str(uuid4())
with repo.connect() as connection:
    connection.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Review UX V2 control')", (review_scope,owner))
review_p = {'repo':repo,'scope':review_scope,'service':SimpleNamespace(policy=policy)}
review_usecase, _, _, review_cp = import_extract(review_p, CASES[0], key='qh50-isolated-review')
asyncio.run(review_usecase.publish(subject_id=owner,checkpoint=review_cp))

# Dedicated QH-54 interpretation review: no mutation of shared chat/review fixtures.
understanding_scope = str(uuid4())
with repo.connect() as connection:
    connection.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Compréhension QH-54 isolée')", (understanding_scope,owner))
understanding_p = {'repo':repo,'scope':understanding_scope,'service':SimpleNamespace(policy=policy)}
understanding_usecase, _, _, understanding_cp = import_extract(understanding_p, CASES[0], key='qh54-isolated-interpretation')
asyncio.run(understanding_usecase.publish(subject_id=owner,checkpoint=understanding_cp))

print(json.dumps({'owner': owner, 'scope': scope, 'source_revision_id': source_ref, 'demo_spaces':demo_spaces, 'review_scope':review_scope, 'understanding_scope':understanding_scope,
                  'original_ids': [r['id'] for r in original],
                  'empty_scope':empty_scope,'proposed_scope':proposed_scope,'historical_scope':historical_scope,
                  'confirmed_id': clones[0]['id'],
                  'all_ids': [r['id'] for r in [*original, *clones, timestamp, legacy]],
                  'decision_ids': [choice['id'], *[r['id'] for r in clones]],
                  'relation': next(r for r in original if r['structural_kind'] == 'relation')['relation']}))
