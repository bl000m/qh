"""Offline request/response replays, not a claim about real-model judgment."""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from dataclasses import replace
from app.projections.disclosure import preview_fingerprint

from app.chat.guest import question_payload
from app.chat.snapshot_answer import projection_request, public_answer, PROMPT
from tests import test_guest_mistral as guest_fixture
from tests.test_sharing_simplified import setup as api_setup
from app.api.guest import COOKIE


@pytest.mark.parametrize('progress',[False,True],ids=['missing-progress','explicit-progress-outside-recap'])
def test_question_uses_authorized_semantic_recap_and_complete_details_without_invented_progress(tmp_path,monkeypatch,progress):
    payload=dict(format='qh.disclosure/1',name='Atelier',recap=dict(title='Atelier informatico',
        text='Preparazione di un atelier informatico di sei giorni, con programma e attività pratiche.'),items=[
        dict(reference='R1',text='È prevista la preparazione del programma di sei giorni e delle attività didattiche.',validation_state='proposed',sources=['S1']),
        dict(reference='R2',text='Per gli esercizi pratici è previsto Jupyter Notebook.',validation_state='proposed',sources=['S1'])])
    if progress:
        payload['items'].append(dict(reference='R3',text='La preparazione dei materiali della prima giornata è completata.',validation_state='proposed',sources=['S1']))
    frozen=deepcopy(payload)
    monkeypatch.setattr(guest_fixture,'PAYLOAD',payload)
    chat,_,_,grant=guest_fixture.setup(tmp_path,monkeypatch)
    calls=[]
    text=('La preparazione dei materiali della prima giornata è completata. Per le attività restano disponibili il programma e Jupyter Notebook.'
        if progress else 'Il lavoro riguarda la preparazione di un atelier informatico di sei giorni, con programma e attività pratiche. Non è documentato quali attività siano già state completate.')
    def response(request):
        wire=json.loads(request.content);calls.append(wire)
        assert wire['messages'][0]['content']==PROMPT
        sent=json.loads(wire['messages'][1]['content'])
        assert sent['snapshot']==question_payload(payload)
        assert sent['snapshot']['recap']==payload['recap'] and len(sent['snapshot']['items'])==len(payload['items'])
        assert 'validation_state' not in json.dumps(sent) and 'sources' not in json.dumps(sent)
        return httpx.Response(200,json=dict(model='mistral-small-2603',usage=dict(prompt_tokens=200,completion_tokens=80),
            choices=[dict(finish_reason='stop',message=dict(content=json.dumps(dict(answer=text,
                reference_aliases=['R3'] if progress else ['R1','R2'],insufficient_context=not progress,support_basis='canonical'))))]))
    chat.live.factory.transport=httpx.MockTransport(response)
    value=asyncio.run(chat.ask('token',grant.snapshot_id,'A che punto siamo con il progetto?'))
    answer=public_answer(value)
    assert answer['answer']==text and answer['insufficient_context']==(not progress)
    assert set(answer)=={'answer','insufficient_context','simulated'} and len(calls)==1 and payload==frozen


def test_summary_is_never_added_from_outside_the_authorized_projection():
    payload=dict(format='qh.disclosure/1',items=[dict(reference='R1',text='Informazione consentita.')])
    packet=json.loads(projection_request(payload,'Che cosa sappiamo?').messages[1].content)
    assert 'recap' not in packet['snapshot'] and packet['snapshot']['items'][0]['text']=='Informazione consentita.'
    assert 'EXCLUDED-CANARY' not in json.dumps(packet)


def test_owner_test_and_guest_use_identical_authorized_projection_with_recap():
    app,_,scope,_,_,provider,sharing,payload=api_setup()
    payload=deepcopy(payload);payload['recap']=dict(title='Atelier informatico',text='Programma e strumenti per un atelier.')
    original=sharing.repository.preview.return_value
    preview=replace(original,payload_json=json.dumps(payload),fingerprint='')
    preview=replace(preview,fingerprint=preview_fingerprint(preview))
    sharing.repository.preview.return_value=preview
    guest=app.state.services.guest
    guest.repository.payload.return_value=replace(guest.repository.payload.return_value,payload_json=json.dumps(payload))
    with TestClient(app,base_url='https://qh.example.test',headers={'Origin':'https://qh.example.test'}) as client:
        client.cookies.set(COOKIE,'synthetic-verified-cookie')
        path=f'/context-spaces/{scope}/sharing/previews/{preview.id}/ask'
        assert client.post(path,json=dict(question='Quels outils ?')).status_code==200
        assert client.post('/guest/ask',json=dict(question='Quels outils ?')).status_code==200
        packets=[json.loads(call.args[0].messages[1].content)['snapshot'] for call in provider.generate.call_args_list]
        assert packets==[question_payload(payload),question_payload(payload)]
        assert 'ORIGINAL-QUOTE-CANARY' not in json.dumps(packets)
        assert client.get('/guest/snapshots/'+guest.repository.payload.return_value.snapshot_id).status_code==404
