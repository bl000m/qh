"""Only disposable browser harness: actual app/OIDC/graph, Mistral HTTP simulated."""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile

import httpx

from adapters.llm.mistral import ExperimentBudget
from tests.test_chat_sessions import offline_pricing
from adapters.llm.session_config import PrivateSessionFactory
from app.bootstrap import create_runtime_app
from app.chat.sessions import ProviderSessions
import time


def create_app():
    if (os.environ.get('QH45_SESSION_BROWSER_TEST') != '1'
        or os.environ.get('QH11_BROWSER_TEST') != '1'
        or not os.environ.get('QH_NATIVE_GRAPH_NAMESPACE', '').startswith('qh12-browser-')
        or os.environ.get('POSTGRES_HOST') != 'postgres'):
        raise RuntimeError('Disposable browser harness only')
    expected = json.loads(os.environ['QH12_EXPECTED_JSON'])
    app = create_runtime_app()
    if os.environ.get('QH51_SEMANTIC_BROWSER_TEST')=='1':
        from tests.semantic_fixtures import ExactSemanticFixtureProvider
        app.state.services.enrichment.semantic_provider=ExactSemanticFixtureProvider()
    private = tempfile.TemporaryDirectory(prefix='qh45-browser-')
    root = Path(private.name)
    now = datetime.now(timezone.utc)
    receipt = dict(purpose='QH-45 interactive chat', owner_authorized=True,
        model='mistral-small-2603', expires_at=(now+timedelta(hours=1)).isoformat(),
        pricing_verified_at=now.isoformat(), eur_per_usd_upper_bound='2',
        input_usd_per_million='0.15', output_usd_per_million='0.60',
        grants=[dict(subject_id=expected['owner'], context_id=scope) for scope in
            [expected['scope'], expected['proposed_scope'], *[d['scope'] for d in expected['demo_spaces']]]])
    ordinary = os.environ.get('QH_DEVELOPMENT_AI_BROWSER_TEST')=='1'
    if ordinary:
        import hashlib
        from adapters.postgres.demo_identities import DEMO_IDENTITIES
        principal = hashlib.sha256(json.dumps([os.environ['OIDC_ISSUER'],DEMO_IDENTITIES[0][2]],separators=(',',':')).encode()).hexdigest()
        receipt['development_account'] = dict(environment='development', subject_id=expected['owner'], principal_id=principal)
    auth = root/'authorization.json'; auth.write_text(json.dumps(receipt)); auth.chmod(0o600)
    ledger = root/'ledger.json'; ExperimentBudget(ledger, create=True)
    state = json.loads(ledger.read_text()); state['purpose'] = receipt['purpose']; ledger.write_text(json.dumps(state))
    os.environ['MISTRAL_API_KEY'] = 'synthetic-browser-offline-key'

    def simulate(request):
        assert request.url.host == 'api.mistral.ai' and request.method == 'POST'
        data = json.loads(request.content)
        assert data['model'] == 'mistral-small-2603'
        context = json.loads(data['messages'][1]['content'])
        if ordinary:
            if set(context)=={'source_revision_id','input_sha256','text','turns'}:
                # Exact synthetic fixture only, never a production keyword classifier.
                turn=context['turns'][0];quote=context['text'][turn['start']:turn['end']]
                value=dict(format='qh.atomic-understanding/1',items=[dict(text=quote,primary_dimension='objectives_intentions',assignment_certainty='asserted',evidence=[dict(quote=quote)])])
            else:
                value=dict(answer='Réponse de test simulée, sans réseau externe.',reference_aliases=list(context['allowed_reference_aliases'])[:1],insufficient_context=not context['allowed_reference_aliases'])
            return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=100,completion_tokens=60),choices=[dict(finish_reason='stop',message=dict(content=json.dumps(value)))]))
        assert context['context_space_id'] in {g['context_id'] for g in receipt['grants']}
        assert 'R1' in context['allowed_reference_aliases']
        return httpx.Response(200, json=dict(model='mistral-small-2603',
            usage=dict(prompt_tokens=100, completion_tokens=20), choices=[dict(finish_reason='stop',
            message=dict(content=json.dumps(dict(answer='Simulation hors réseau, aucune inférence réelle. Le support reste non confirmé lorsqu’il est proposé.',
                reference_aliases=['R1'], insufficient_context=False))))]))

    factory = PrivateSessionFactory(authorization_path=auth, ledger_path=ledger,
                                   transport=httpx.MockTransport(simulate), pricing=offline_pricing())
    sessions = ProviderSessions(chat=app.state.services.chat, factory=factory, clock=time.time)
    from app.chat.development import DevelopmentAI
    automatic = DevelopmentAI(chat=app.state.services.chat, enrichment=app.state.services.enrichment,
        factory=factory, clock=time.time) if ordinary else None
    app.state.services = replace(app.state.services, chat_sessions=sessions, development_ai=automatic)
    app.state.offline_chat=os.environ.get('QH52_PRODUCT_BROWSER_TEST')!='1'
    if os.environ.get('QH52_PRODUCT_BROWSER_TEST')=='1':
        sessions.session_binding=True
    original = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        try:
            async with original(application):
                yield
        finally:
            private.cleanup()
    app.router.lifespan_context = lifespan
    return app
