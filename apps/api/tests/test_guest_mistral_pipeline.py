"""Real SQL/native/OIDC/SMTP guest facade; Mistral transport remains simulated."""
import httpx,json

from app.projections.disclosure import LIVE_PROVIDER
from tests.test_guest_mistral import setup,wire_reply
from tests.test_sharing_pipeline import client_for,invite,pytestmark as pytestmark
from tests.test_guest_pipeline import guest as guest
from tests.test_disclosure_pipeline import disclosure as disclosure
from tests.test_projection_drafts_sql import drafts as drafts
from tests.test_generic_semantics import generic as generic
from tests.test_migrations import empty_database as empty_database
from tests.test_native_context import real_engine as real_engine
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only
from adapters.llm.guest_offline import OfflineSnapshotProvider


def test_guest_real_path_accounted_with_only_materialized_payload(guest,tmp_path,monkeypatch):
    p=guest
    chat,calls,ledger,_=setup(tmp_path,monkeypatch,subject=p['repo'].subject_id)
    before=p['repo'].read_snapshot((p['scope'],))
    with client_for(p,OfflineSnapshotProvider(),chat.live) as c:
        # The real scope comes from the verified stored invitation, never client input.
        factory=chat.live.factory
        def transport(request):
            sent=json.loads(request.content);packet=json.loads(sent['messages'][1]['content'])
            calls.append(packet)
            assert set(packet)<={'snapshot','question','subjects','language'}
            assert all(item in preview['payload']['items'] for item in packet['snapshot']['items'])
            refs=[packet['snapshot']['items'][0]['reference']]
            return httpx.Response(200,json=dict(model=LIVE_PROVIDER,usage=dict(prompt_tokens=100,completion_tokens=30),
                choices=[dict(finish_reason='stop',message=dict(content=json.dumps(wire_reply(dict(answer='Un objectif est proposé.',reference_aliases=refs,support_basis='canonical',insufficient_context=False),packet,sent))))]))
        factory.transport=httpx.MockTransport(transport)
        snapshot,invitation,preview=invite(c,p,provider_name=LIVE_PROVIDER)
        status=c.get('/guest/provider');assert status.status_code==200 and status.json()['model']==LIVE_PROVIDER
        assert not calls
        answer=c.post('/guest/snapshots/'+snapshot+'/ask',json=dict(question='Quel objectif est proposé ?'))
        assert answer.status_code==200 and not answer.json()['simulated']
        assert answer.json()['accounting']['status']=='completed' and len(calls)==2
    assert p['repo'].read_snapshot((p['scope'],))==before
