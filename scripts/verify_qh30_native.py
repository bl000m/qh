"""Dedicated-database QH-30 fixture restart/rebuild probe; never run on QH DBs."""

import argparse
import asyncio
import os
import sys

from neo4j import GraphDatabase

from adapters.context.native import NativeContextEngine, NativeContextError
from app.core.models import ContextQuery
from tests.test_native_context import A, FIXTURE, loader, validate_content

PROBE = "qh30-universal-restart-probe"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=["prepare", "check", "rebuild-after-loss"], required=True
    )
    args = parser.parse_args()
    uri = os.environ["QH30_TEST_NEO4J_URI"]
    if uri != "bolt://qh30-native-neo4j-test:7687":
        raise SystemExit("Refusing a non-dedicated QH30 test database")
    with GraphDatabase.driver(
        uri,
        auth=("neo4j", os.environ["QH30_TEST_NEO4J_PASSWORD"]),
        max_transaction_retry_time=0,
    ) as driver:
        engine = NativeContextEngine(
            driver,
            slice_id=PROBE,
            read_snapshot=loader(FIXTURE, []),
            validate_content=validate_content,
        )
        if args.phase == "prepare":
            engine.initialize()
            engine.replace(FIXTURE, generation="one")
        if args.phase == "rebuild-after-loss":
            with driver.session() as session:
                session.run(
                    "MATCH (n) WHERE "
                    "(n:QH30Revision OR n:QH30Source) AND n.slice_id=$id "
                    "OR n:QH30Slice AND n.id=$id "
                    "OR n:QH30Generation AND n.key STARTS WITH $prefix DETACH DELETE n",
                    id=PROBE,
                    prefix=PROBE + ":",
                ).consume()
            try:
                asyncio.run(engine.search(ContextQuery(text="Cedar", context_ids=(A,))))
            except NativeContextError:
                pass
            else:
                raise AssertionError(
                    "Lost projection must not be a successful empty result"
                )
            engine.replace(FIXTURE, generation="two")
        result = asyncio.run(
            engine.search(ContextQuery(text="Cedar", context_ids=(A,)))
        )
        assert len(result.hits) == 3 and all(
            h.context_id == A and h.item_revision and h.provenance for h in result.hits
        )
        assert not {"graphiti_core", "mistralai", "openai"} & set(sys.modules)
        print(
            "PASS:",
            args.phase,
            "3 scoped fixture revisions with provenance; no Graphiti/LLM SDK imported",
        )


if __name__ == "__main__":
    main()
