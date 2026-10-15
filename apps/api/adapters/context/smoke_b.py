"""Prepared manual B-only 8B experiment. Never invoked by startup/tests/CI."""

from copy import deepcopy
import argparse
import asyncio
import base64
import json
import logging
import math
import os
from pathlib import Path
import struct
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from adapters.context.diagnostics import describe_failure, llm_phase
from adapters.context.factory import create_graphiti_engine
from adapters.context.smoke_quality import SmokeFixture
from app.core.models import ContextId, ContextQuery, SourceId, SourceRevisionId, SourceRevisionRef

MODEL = "ministral-8b-2512"
MAX_REQUESTS = 12
BUDGET_USD = 0.01
FIXTURE = SmokeFixture("Bea founded Cedar Observatory.", frozenset({"Bea", "Cedar Observatory"}),
    expected_facts=frozenset({"Bea founded Cedar Observatory", "Cedar Observatory was founded by Bea"}))


class ExperimentStopped(BaseException):
    pass


class ExperimentTransport(httpx.AsyncBaseTransport):
    def __init__(self, ledger: Path, *, inner=None, capture_synthetic=False):
        self.capture_synthetic = capture_synthetic
        self.diagnostic = None
        self.ledger = ledger
        self.inner = inner if inner is not None else httpx.AsyncHTTPTransport(retries=0)
        self.records = []
        self.observations = []
        self.metadata = {}
        self.cost = 0.0
        self.failed = False
        self.failure_reason = None
        self.inflight = False

    def save(self):
        self.ledger.write_text(json.dumps({"requests":self.records,"estimated_cost_usd":self.cost,
                                         "diagnostic":self.diagnostic,"stopped":self.failed,"failure_reason":self.failure_reason,"observations":self.observations,"metadata":self.metadata},indent=2))

    def stop(self, reason):
        self.failed = True
        self.failure_reason = reason
        self.save()
        raise ExperimentStopped(reason)

    async def handle_async_request(self, request):
        if self.failed or self.inflight:
            self.stop("Experiment stopped or concurrent send forbidden")
        body = json.loads(await request.aread())
        chat = str(request.url) == "https://api.mistral.ai/v1/chat/completions"
        embed = str(request.url) == "https://api.mistral.ai/v1/embeddings"
        if request.method != "POST" or not (chat or embed) or body.get("model") != (MODEL if chat else "mistral-embed") or body.get("stream"):
            self.stop("Request outside the authorized B experiment")
        if embed and not (isinstance(body.get("input"),list) and len(body['input'])==1 and isinstance(body['input'][0],str)):
            self.stop("Embedding batches forbidden")
        rate = (0.15 if chat else 0.10)/1_000_000
        output_cap = body.get("max_tokens",0)
        if not isinstance(output_cap,int) or not 0 <= output_cap <= 16384:
            self.stop("Unexpected output cap")
        reserve = (len(request.content)+1024+output_cap)*rate
        if len(self.records)>=MAX_REQUESTS or self.cost+reserve>BUDGET_USD:
            self.stop("Request count or estimated budget exhausted")
        row={"number":len(self.records)+1,"model":body['model'],"endpoint":str(request.url),
             "pre_send_estimate_usd":reserve,"max_output_tokens":output_cap}
        if chat and self.capture_synthetic:
            row["phase"] = llm_phase.get()
            row["synthetic_request"] = {key: body[key] for key in
                ("model", "messages", "response_format", "temperature", "max_tokens") if key in body}
        self.records.append(row)
        self.save()  # A failed attempt is consumed, never restarted/retried.
        self.inflight = True
        try:
            response = await self.inner.handle_async_request(request)
            row['status'] = response.status_code
            if response.status_code!=200:
                await response.aclose()
                self.stop("Provider HTTP error")
            raw = await response.aread()
            if chat and self.capture_synthetic:
                # Only the dedicated fixture runner opts in. No headers/SDK objects.
                try:
                    envelope = json.loads(raw)
                    row['synthetic_response'] = {
                        'choices': [{'message': {'content': c.get('message', {}).get('content')},
                                     'finish_reason': c.get('finish_reason')}
                                    for c in envelope.get('choices', [])]}
                except (ValueError, AttributeError, TypeError):
                    row['synthetic_response_body'] = raw.decode('utf-8', errors='replace')
                self.save()  # Persist before SDK JSON parsing/schema/quality validation.
            data=json.loads(raw)
            usage=data.get('usage') or {}
            if not isinstance(usage.get('prompt_tokens'),int) or not isinstance(usage.get('completion_tokens',0),int):
                self.stop("Missing usage")
            row['usage']=usage
            cost=(usage['prompt_tokens']+usage.get('completion_tokens',0))*rate
            row['estimated_cost_usd']=cost
            self.cost+=cost
            if cost>reserve or self.cost>BUDGET_USD:
                self.stop("Unexpected usage or budget risk")
            if chat and data['choices'][0].get('finish_reason')!='stop':
                self.stop("Incomplete generation")
            if embed:
                entries=data['data']
                if len(entries)!=1 or entries[0].get('index')!=0:
                    self.stop("Invalid embedding result count")
                vector=entries[0]['embedding']
                if isinstance(vector,str):
                    vector=struct.unpack('<1024f',base64.b64decode(vector,validate=True))
                if len(vector)!=1024 or not all(math.isfinite(v) for v in vector):
                    self.stop("Invalid embedding")
            self.save()
            return response
        except ExperimentStopped:
            raise
        except BaseException:
            self.stop("Provider result invalid or request failed; no retry")
        finally:
            self.inflight = False

    async def aclose(self):
        await self.inner.aclose()


async def run(ledger: Path):
    with ledger.open('x') as handle:
        ledger.chmod(0o600)
        handle.write('{}')  # Refuse to restart an existing experiment.
    logging.disable(logging.CRITICAL)
    os.environ['MISTRAL_LLM_MODEL'] = MODEL  # Child process only, never edit VPS .env.
    os.environ['MISTRAL_EMBEDDING_MODEL'] = 'mistral-embed'
    async def authorized(description):
        return True  # Only reachable after explicit CLI experiment acknowledgement.
    adapter,sdk = await create_graphiti_engine(approval=authorized)
    await sdk._client._transport.inner.aclose()
    guard=ExperimentTransport(ledger, capture_synthetic=True)
    sdk._client._transport.inner=guard
    def observe(evidence, phase, answer):
        guard.observations.append({"phase":phase,"result":deepcopy(answer)})
        guard.save()  # Preserve invalid outputs as diagnostics, never as approved facts.
        FIXTURE.validate(evidence,phase,answer)
    adapter.quality_observer=observe
    marker=uuid4().hex
    space=ContextId('qh7-b-8b-'+marker)
    source=SourceRevisionRef(source_id=SourceId('qh7-source-'+marker),revision_id=SourceRevisionId('revision-1'))
    reference_time = datetime.now(timezone.utc)
    guard.metadata={"reference_time": reference_time.isoformat(), "stage": "initialize",
                    "ingestion_status": "not_started", "scope":str(space),"source_id":str(source.source_id),
                    "source_revision":str(source.revision_id),"text":FIXTURE.text}
    guard.save()
    try:
        await adapter.initialize()
        guard.metadata.update(stage="ingest", ingestion_status="started")
        guard.save()
        await adapter.ingest_source(context_id=space,source=source,text=FIXTURE.text,
                                    reference_time=reference_time)
        guard.metadata.update(stage="search", ingestion_status="succeeded")
        guard.save()
        result=await adapter.search(ContextQuery(text='Who founded the observatory?',context_ids=(space,)))
        if not result.hits or any(h.context_id!=space or h.provenance!=(source,) or h.excerpt.strip().rstrip('.') not in FIXTURE.expected_facts for h in result.hits):
            guard.stop('Semantic retrieval/provenance failed')
        guard.metadata['facts']=[h.excerpt for h in result.hits]
        print('PASS: B-only extraction, grounded fact and scoped semantic retrieval')
    except BaseException as exc:
        guard.failed=True
        if guard.metadata.get("ingestion_status") == "started":
            guard.metadata["ingestion_status"] = "failed"
        diagnostic = getattr(exc, 'diagnostic', None) or describe_failure(exc, 'smoke')
        guard.diagnostic = diagnostic.as_dict()
        if guard.failure_reason is None:
            guard.failure_reason="Local/extraction validation failure: "+type(exc).__name__
        print('STOP: B-only smoke failed; no retry or further provider requests')
    finally:
        guard.save()
        await adapter.close(); await sdk.close()
        print('Synthetic scope retained:',space)
        print('Requests:',len(guard.records),'estimated USD:',guard.cost)
    if guard.failed:
        raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorized-experiment',action='store_true',help='Use only after explicit owner approval of this model/scope/budget/count')
    parser.add_argument('--ledger',type=Path,required=True)
    args=parser.parse_args()
    if not args.authorized_experiment:
        parser.error('Explicit new 8B experiment authorization required; no provider called')
    asyncio.run(run(args.ledger))


if __name__=='__main__':
    main()
