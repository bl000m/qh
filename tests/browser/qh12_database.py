"""Test-only backup fingerprints and native rebuild; no persistent QH targets."""
import hashlib
import json
import os
from pathlib import Path
import sys

from neo4j import GraphDatabase
from psycopg import sql

from adapters.context.incremental import IncrementalProjector, ProjectionWorker
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from tests.oidc_database import connect

assert os.environ.get('QH12_BROWSER_TEST') == '1'
assert os.environ['POSTGRES_HOST'] == 'postgres' and os.environ['POSTGRES_DB'] in ('qh', 'qh12_restore')
CANONICAL = {'users', 'user_identities', 'context_spaces', 'sources', 'source_revisions',
             'understanding_items', 'understanding_item_revisions', 'item_revision_types',
             'item_revision_provenance', 'relation_revision_details', 'semantic_type_versions'}


def snapshot():
    result = {}
    with connect() as connection:
        tables = [r[0] for r in connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")]
        for table in tables:
            rows = connection.execute(sql.SQL('SELECT to_jsonb(t) FROM {} t').format(sql.Identifier(table))).fetchall()
            encoded = sorted(json.dumps(r[0], sort_keys=True, ensure_ascii=False) for r in rows)
            result[table] = {'count': len(rows), 'sha256': hashlib.sha256('\n'.join(encoded).encode()).hexdigest()}
    assert CANONICAL <= result.keys()
    return result


def rebuild():
    before = snapshot()
    driver = GraphDatabase.driver(os.environ['NEO4J_URI'], auth=('neo4j', os.environ['NEO4J_PASSWORD']))
    try:
        projector = IncrementalProjector(driver, namespace=os.environ['QH_NATIVE_GRAPH_NAMESPACE'])
        projector.initialize()
        with connect() as connection:
            scopes = connection.execute('SELECT DISTINCT cs.id,cs.owner_id FROM context_spaces cs '
                                        'JOIN understanding_item_revisions r ON r.context_space_id=cs.id').fetchall()
        for scope, owner in scopes:
            worker = ProjectionWorker(CanonicalRepository(url=database_url(), subject_id=owner), projector, (str(scope),))
            worker.rebuild(str(scope))
        after = snapshot()
        assert {k: before[k] for k in CANONICAL} == {k: after[k] for k in CANONICAL}
    finally:
        driver.close()
    print('PASS: restored canonical tables unchanged across native graph rebuild; no extractor')


if sys.argv[1] == 'snapshot':
    print(json.dumps(snapshot(), sort_keys=True))
elif sys.argv[1] == 'compare':
    assert snapshot() == json.loads(Path(sys.argv[2]).read_text())
    print('PASS: all restored SQL table fingerprints match the stopped test database')
elif sys.argv[1] == 'rebuild':
    rebuild()
else:
    raise SystemExit('Unknown test operation')
