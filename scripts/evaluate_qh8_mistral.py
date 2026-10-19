"""Explicit live synthetic experiment or offline replay; never called by CI/startup.

Creates only a uniquely named disposable SQL DB and graph namespace on the enforced
QH test servers. Original model responses and validation outcomes are separate.
Reference labels are only hashed for the manifest, never used to build requests.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
from alembic import command
from alembic.config import Config
from neo4j import GraphDatabase
import psycopg
from psycopg import sql

from adapters.context.runtime import NativeRuntime
from adapters.llm.mistral import ExperimentBudget, MistralProvider, MistralError
from adapters.llm.offline import ReplayLLMProvider, request_hash
from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.security import PostgresSecurityReader
from adapters.postgres.semantic_profiles import register_generic_profiles
from app.core.models import ContextRequest, ContextQuery
from app.policy.owner import OwnerPolicyService
from app.understanding.extractor import UnderstandingExtractor, decode_output, digest
from app.understanding.citations import VERSION as CITATION_RESOLVER_VERSION

FIXTURES = ROOT / "apps/api/tests/fixtures"


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def source_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_pipeline(runtime, repo, owner, scope, ids):
    deadline = time.monotonic() + 30
    while repo.sync_status((scope,))[0]["sync_state"] != "ready":
        if time.monotonic() > deadline:
            raise RuntimeError("Worker did not become ready")
        time.sleep(0.1)
    export = repo.read_snapshot((scope,), ids)
    rows = export["understanding_item_revisions"]
    assert {r["id"] for r in rows} == set(ids)
    assert all(
        r["validation_state"] == "proposed" and r["current_revision_id"] is None
        for r in rows
    )
    values = sorted(
        {
            d["value"]
            for r in rows
            for d in r["content"].get("descriptors", [])
            if d["certainty"] == "asserted"
        }
    )
    selected = []
    if values:
        hits = asyncio.run(
            runtime.context_for(owner).select_descriptors(
                subject_id=owner, context_ids=(scope,), values=values, limit=100
            )
        )
        selected = [str(h.item_revision.revision_id) for h in hits.hits]
        assert set(selected) == {
            r["id"]
            for r in rows
            if any(
                d["certainty"] == "asserted"
                for d in r["content"].get("descriptors", [])
            )
        }
    text = rows[0]["content"]["text"][:40]
    result = asyncio.run(
        runtime.context_for(owner).retrieve(
            ContextRequest(
                subject_id=owner,
                query=ContextQuery(text=text, context_ids=(scope,), limit=100),
            )
        )
    )
    assert rows[0]["id"] in {str(h.item_revision.revision_id) for h in result.hits}
    try:
        asyncio.run(
            runtime.context_for(owner).select_descriptors(
                subject_id=str(uuid4()), context_ids=(scope,), values=["decision"]
            )
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("Foreign subject not denied")
    return dict(
        status="PASS",
        export=export,
        descriptor_revision_ids=selected,
        sync_state="ready",
        foreign_subject_denied=True,
    )


def execute(
    *,
    out,
    live,
    replay_from=None,
    resume_from=None,
    case_names=None,
    reviewed_resumption=False,
    resolve_citations=False,
):
    if resolve_citations and (live or replay_from is None):
        raise ValueError("Citation derivation requires offline capture replay")
    expected = {
        "POSTGRES_HOST": "qh30-sql-test",
        "POSTGRES_DB": "qh30_admin",
        "QH30_SQL_TEST": "1",
        "QH30_TEST_NEO4J_URI": "bolt://qh30-native-neo4j-test:7687",
    }
    if any(os.environ.get(k) != v for k, v in expected.items()):
        raise RuntimeError("Explicit disposable SQL/Neo4j configuration required")
    if live and os.environ.get("CI"):
        raise RuntimeError("Live calls prohibited in CI")
    os.umask(0o077)
    out = Path(out)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    cases = json.loads((FIXTURES / "mistral_unseen_conversations.json").read_text())
    dataset_hash = source_digest(FIXTURES / "mistral_unseen_conversations.json")
    if case_names:
        if set(case_names) - {c["name"] for c in cases} or len(set(case_names)) != len(
            case_names
        ):
            raise ValueError("Explicit known nonduplicate cases required")
        cases = [c for c in cases if c["name"] in case_names]
    if live and resume_from:
        resume_from = Path(resume_from)
        manifest = json.loads((resume_from / "manifest.json").read_text())
        if manifest["dataset_sha256"] != dataset_hash or manifest[
            "reference_sha256"
        ] != source_digest(FIXTURES / "mistral_evaluation_reference.json"):
            raise ValueError("Frozen input/reference changed")
        ledger = resume_from / "ledger.json"
        budget = ExperimentBudget(ledger)
        if reviewed_resumption:
            dump(
                out / "ledger-before-reconciliation.json",
                json.loads(ledger.read_text()),
            )
            budget.reconcile_reviewed_429(
                reason="Owner authorized resumption after reporting PAYG activation and positive credit; retain 2 attempts and USD 0.006 failed reservation"
            )
        provider = MistralProvider(budget=budget)
        dump(
            out / "resumption.json",
            dict(
                original_evidence=str(resume_from),
                ledger=str(ledger),
                cases=[c["name"] for c in cases],
                model="mistral-small-2603",
                billing_verification="owner statement; standard key cannot inspect admin billing/workspace; inferencing checked operationally",
            ),
        )
    elif live:
        manifest = dict(
            mode="live",
            owner=str(uuid4()),
            scopes={c["name"]: str(uuid4()) for c in cases},
            dataset_sha256=dataset_hash,
            reference_sha256=source_digest(
                FIXTURES / "mistral_evaluation_reference.json"
            ),
        )
        budget = ExperimentBudget(out / "ledger.json", create=True)
        provider = MistralProvider(budget=budget)
    else:
        manifest = json.loads((Path(replay_from) / "manifest.json").read_text())
        assert manifest["dataset_sha256"] == dataset_hash
        provider = None
    dump(out / "manifest.json", manifest)
    admin_url = database_url()
    admin = psycopg.connect(
        host=admin_url.host,
        port=admin_url.port,
        dbname=admin_url.database,
        user=admin_url.username,
        password=admin_url.password,
        autocommit=True,
    )
    name = "qh8_mistral_" + uuid4().hex
    admin.execute(
        sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(sql.Identifier(name))
    )
    old_db = os.environ["POSTGRES_DB"]
    os.environ["POSTGRES_DB"] = name
    runtime = None
    driver = None
    results = []
    namespace = "qh8-mistral-" + name
    try:
        os.chdir(ROOT / "apps/api")
        command.upgrade(
            Config(str(ROOT / "apps/api/adapters/postgres/alembic.ini")),
            "0005_retire_legacy_category", "0006_owner_organization",
        )
        url = database_url()
        owner = manifest["owner"]
        repo = CanonicalRepository(url=url, subject_id=owner)
        with repo.connect() as c:
            c.execute(
                "INSERT INTO users(id,display_name) VALUES (%s,'Synthetic Mistral experiment')",
                (owner,),
            )
            for scope in manifest["scopes"].values():
                c.execute(
                    "INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,'Synthetic unseen conversation')",
                    (scope, owner),
                )
        register_generic_profiles(repo)
        policy = OwnerPolicyService(owner_for=PostgresSecurityReader(url=url).owner_for)
        driver = GraphDatabase.driver(
            os.environ["QH30_TEST_NEO4J_URI"],
            auth=("neo4j", os.environ["QH30_TEST_NEO4J_PASSWORD"]),
            max_transaction_retry_time=0,
        )
        runtime = NativeRuntime(
            url=url, driver=driver, policy=policy, namespace=namespace, poll_seconds=0.1
        )
        runtime.start()
        if live and not resume_from:
            metadata = asyncio.run(provider.verify_model())
            dump(out / "model-availability.json", metadata)
        for case in cases:
            case_dir = out / case["name"]
            case_dir.mkdir(mode=0o700)
            scope = manifest["scopes"][case["name"]]
            if not live:
                capture = json.loads(
                    (Path(replay_from) / case["name"] / "raw.json").read_text()
                )
                provider = ReplayLLMProvider(
                    expected_request_sha256=capture["request_sha256"],
                    response_json=capture["response"]["choices"][0]["message"][
                        "content"
                    ],
                )
            extractor = UnderstandingExtractor(
                repository=repo, policy=policy, provider=provider
            )
            ref = asyncio.run(
                extractor.import_conversation(
                    subject_id=owner,
                    context_id=scope,
                    conversation=case["conversation"],
                )
            )
            source = repo.read_sources((scope,), (ref,))[0]
            dump(case_dir / "source.json", source)
            result = dict(case=case["name"], source_revision_id=ref, scope=scope)
            try:
                cp = asyncio.run(
                    extractor.extract(
                        subject_id=owner,
                        context_id=scope,
                        source_revision_id=ref,
                        extraction_key="mistral-initial-v1",
                    )
                )
                result["raw_validation"] = "PASS"
            except ValueError as exc:
                result.update(
                    raw_validation="FAIL",
                    validation_error=dict(type=type(exc).__name__, message=str(exc)),
                )
                cp = None
            finally:
                if live and provider.last_exchange is not None:
                    capture = {
                        **provider.last_exchange,
                        "request_sha256": request_hash(provider.last_request),
                    }
                    dump(case_dir / "raw.json", capture)
            if resolve_citations:
                result["original_raw_validation"] = result["raw_validation"]
                if "validation_error" in result:
                    result["original_validation_error"] = result.pop("validation_error")
                original = dict(
                    version=1,
                    context_space_id=scope,
                    source_revision_id=ref,
                    input_sha256=extractor.source_hash(source),
                    extraction_key="mistral-initial-v1",
                    output=decode_output(
                        capture["response"]["choices"][0]["message"]["content"]
                    ),
                )
                try:
                    cp, audit = asyncio.run(
                        extractor.resolve_citations(
                            subject_id=owner,
                            checkpoint=original,
                            extraction_key="mistral-citation-resolution-v1",
                        )
                    )
                    dump(case_dir / "derived-output.json", cp["output"])
                    dump(case_dir / "citation-resolution.json", audit)
                    result.update(
                        raw_validation="PASS",
                        citation_resolution="PASS",
                        corrected_spans=sum(r["changed"] for r in audit["citations"]),
                    )
                except ValueError as exc:
                    cp = None
                    issues = getattr(exc, "issues", ())
                    dump(
                        case_dir / "citation-resolution.json",
                        dict(
                            status="REJECTED",
                            version=CITATION_RESOLVER_VERSION,
                            original_output_sha256=digest(original["output"]),
                            derived_output_sha256=None,
                            input_sha256=original["input_sha256"],
                            error_type=type(exc).__name__,
                            message=str(exc),
                            issues=issues,
                        ),
                    )
                    result.update(raw_validation="FAIL", citation_resolution="REJECTED")
            if cp is not None:
                ids = asyncio.run(extractor.publish(subject_id=owner, checkpoint=cp))
                if resolve_citations:
                    replayed_ids = asyncio.run(
                        extractor.publish(subject_id=owner, checkpoint=cp)
                    )
                    assert replayed_ids == ids
                    result["checkpoint_replay"] = "PASS"
                pipeline = collect_pipeline(runtime, repo, owner, scope, ids)
                dump(case_dir / "canonical.json", pipeline)
                result.update(pipeline="PASS", revision_ids=list(ids), items=len(ids))
                dump(case_dir / "checkpoint.json", cp)
            else:
                assert not repo.read_snapshot((scope,))["understanding_item_revisions"]
                result.update(pipeline="NOT PUBLISHED", items=0, source_retained=True)
                if resolve_citations:
                    rejected_state = repo.sync_status((scope,))[0]
                    assert (
                        rejected_state["desired_version"]
                        == rejected_state["applied_version"]
                        == 0
                    )
                    result["rejected_scope_versions"] = dict(desired=0, applied=0)
            if resolve_citations:
                assert provider.calls == 1
                result["offline_provider_replays"] = provider.calls
            dump(case_dir / "validation.json", result)
            results.append(result)
            dump(out / "results.json", results)
            print(
                json.dumps({k: v for k, v in result.items() if k != "revision_ids"}),
                flush=True,
            )
        return results
    except Exception as exc:
        if runtime is not None:
            try:
                failure = repo.read_snapshot(tuple(manifest["scopes"].values()))
                failure["sync_status"] = repo.sync_status(
                    tuple(manifest["scopes"].values())
                )
                with repo.connect() as c:
                    c.execute("SET TRANSACTION READ ONLY")
                    failure["source_revision_count"] = c.execute(
                        "SELECT count(*) AS n FROM source_revisions"
                    ).fetchone()["n"]
                dump(out / "failure-state.json", failure)
            except Exception:
                dump(
                    out / "failure-state.json",
                    {"status": "diagnostic snapshot unavailable"},
                )
        dump(
            out / "experiment-error.json",
            dict(
                type=type(exc).__name__,
                provider_diagnostic=getattr(provider, "last_failure", None),
                message=str(exc)
                if isinstance(exc, MistralError)
                else "Experiment stopped; inspect protected artifacts",
            ),
        )
        raise
    finally:
        if runtime is not None:
            runtime.stop()
        if driver is not None:
            # Runtime closes its driver; use a new connection for this test-owned namespace only.
            with GraphDatabase.driver(
                os.environ["QH30_TEST_NEO4J_URI"],
                auth=("neo4j", os.environ["QH30_TEST_NEO4J_PASSWORD"]),
            ) as cleanup:
                with cleanup.session() as s:
                    s.run(
                        "MATCH (n) WHERE n.key STARTS WITH $prefix OR n.id STARTS WITH $prefix OR n.slice_id STARTS WITH $prefix DETACH DELETE n",
                        prefix=namespace + ":",
                    ).consume()
        os.environ["POSTGRES_DB"] = old_db
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        admin.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--replay-from", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--case", action="append", dest="case_names")
    parser.add_argument("--reviewed-resumption", action="store_true")
    parser.add_argument(
        "--resolve-citations",
        action="store_true",
        help="Derive exact locators from frozen captures; offline replay only",
    )
    args = parser.parse_args()
    try:
        if (args.resume_from or args.reviewed_resumption) and not args.live:
            raise ValueError("Resumption requires explicit live mode")
        execute(
            out=args.out,
            live=args.live,
            replay_from=args.replay_from,
            resume_from=args.resume_from,
            case_names=args.case_names,
            reviewed_resumption=args.reviewed_resumption,
            resolve_citations=args.resolve_citations,
        )
    except Exception as exc:
        print("Experiment stopped:", type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
