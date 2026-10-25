"""Disposable-only exact UUM sharing fixture, then additive 0009 upgrade."""
import asyncio,json,os
from uuid import uuid4
from unittest.mock import AsyncMock,Mock
from alembic import command
from alembic.config import Config
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.demo_identities import DEMO_IDENTITIES
from adapters.postgres.review import PostgresReviewRepository
from adapters.context.incremental import IncrementalProjector,ProjectionWorker
from neo4j import GraphDatabase
from app.core.models import GenerationResult,Message,MessageRole
from app.understanding.selected import propose_selected_conversation

assert os.environ.get('QH_SHARING_BROWSER_TEST')=='1' and os.environ['POSTGRES_HOST']=='postgres' and os.environ['POSTGRES_DB']=='qh'
assert os.environ.get('QH_NATIVE_GRAPH_NAMESPACE','').startswith('qh12-browser-')
owner=str(DEMO_IDENTITIES[0][1]);repo=CanonicalRepository(url=database_url(),subject_id=owner);scope=str(uuid4())
with repo.connect() as c:c.execute("INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Atelier partagé')",(scope,owner))
quotes=['Nous voulons organiser un atelier accessible.',
    'Contact : atelier@example.test, téléphone +33 6 12 34 56 78.',
    'Diagnostic de cancer : SANTE_EXCLUE_DEMO_B.']
wire=dict(format='qh.atomic-understanding/1',items=[dict(text=q,primary_dimension='objectives_intentions' if i==0 else 'situation_information',
    assignment_certainty='asserted',evidence=[dict(quote=q)]) for i,q in enumerate(quotes)])
source,rows=asyncio.run(propose_selected_conversation(subject_id=owner,context_id=scope,
    conversation=dict(id=str(uuid4()),acquired_at='2026-10-25T12:00:00Z',metadata={'synthetic':True},
        turns=[dict(id=str(uuid4()),speaker='user (owner-declared)',text=q) for q in quotes+['SOURCE_INTEGRALE_DEMO_B']]),
    extraction_key='qh40-sharing-fixture/1',policy=Mock(evaluate=AsyncMock(return_value=Mock(allowed=True))),
    provider=Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(wire))))),descriptor_version=3))
repo.save(sources=[source],revisions=rows)
# Explicit synthetic owner review; never mutate a proposal or production record.
driver=GraphDatabase.driver(os.environ['NEO4J_URI'],auth=(os.environ['NEO4J_USER'],os.environ['NEO4J_PASSWORD']))
projector=IncrementalProjector(driver,namespace=os.environ['QH_NATIVE_GRAPH_NAMESPACE']);projector.initialize()
worker=ProjectionWorker(repo,projector,(scope,))
try:
    for _ in range(20):
        if not worker.run_once():break
    assert worker.last_error is None
finally:driver.close()
asyncio.run(PostgresReviewRepository(url=repo.url).apply(owner,scope,rows[0]['id'],dict(
    operation_id=str(uuid4()),action='confirm',expected_latest_revision_id=rows[0]['id'],
    expected_current_revision_id=None,text=None)))
command.upgrade(Config('adapters/postgres/alembic.ini'),'0009_guest_invitations')
print(json.dumps(dict(sharing_scope=scope,sharing_excluded='SANTE_EXCLUE_DEMO_B',sharing_source='SOURCE_INTEGRALE_DEMO_B')))
