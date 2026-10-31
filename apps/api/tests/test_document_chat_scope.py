"""Offline source isolation, identity evidence and original download without AI."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.chat.documents import document_selection,document_reply,scoped_revision_ids,is_original_request
from app.core.models import Message,MessageRole
from tests.test_consolidation import fixture,document
from tests.test_chat_service import request

DOCS=[dict(source_revision_id='cv',filename='CV Mathia_Pagani.pdf'),
      dict(source_revision_id='contract',filename='contrat finale.pdf'),
      dict(source_revision_id='interview',filename='Synanto_EAE_2026.pdf')]
ROWS=[dict(revision_id='cv-item',content=dict(text='Mathia Pagani, expérience déclarée dans le CV.',citations=[dict(source_revision_id='cv',turn_id='cv:page:1')])),
      dict(revision_id='contract-item',content=dict(text='Le contrat prévoit un poste de développeur.',citations=[dict(source_revision_id='contract',turn_id='contract:page:2')])),
      dict(revision_id='interview-item',content=dict(text='Souhait de devenir architecte, exprimé dans l’entretien, sans engagement contractuel.',citations=[dict(source_revision_id='interview',turn_id='interview:page:1')])),
      dict(revision_id='mixed-item',content=dict(text='Les sources présentent des informations différentes.',citations=[dict(source_revision_id='contract'),dict(source_revision_id='interview')]))]


def test_document_selection_scopes_contract_and_interview_without_reclassifying_data():
    before=deepcopy(ROWS)
    for question,expected in [('Que prévoit le contrat Synanto ?','contract-item'),
        ('Quali desideri emergono dall’entretien professionnel 2026 ?','interview-item')]:
        selected,ambiguous=document_selection(question,DOCS)
        assert not ambiguous
        assert scoped_revision_ids(ROWS,selected,DOCS)==(expected,)
    custom=[dict(DOCS[0],display_name='Mon profil technique'),*DOCS[1:]]
    assert document_reply('Télécharge mon profil technique',custom)['documents']==[custom[0]]
    assert document_reply('Télécharge CV Mathia_Pagani.pdf',custom)['documents']==[custom[0]]
    assert ROWS==before
    assert document_selection('Fais un résumé de ce contexte',DOCS)==(None,False)
    assert document_selection('Synthèse des trois PDF',DOCS)==(None,False)
    assert document_selection('Qu’est-ce qu’un contrat ?',[])==(None,False)
    assert document_selection('Qui est Mathia Pagani et quel est son parcours ?',DOCS)==(None,False)
    selected,ambiguous=document_selection('Compare contrat et entretien',DOCS)
    assert not ambiguous and scoped_revision_ids(ROWS,selected,DOCS)==('contract-item','interview-item','mixed-item')
    assert document_selection('Selon mon CV',DOCS+[dict(DOCS[0],source_revision_id='other-cv')])[1]


def test_original_lookup_is_ambiguous_or_access_scoped_and_never_invents_documents():
    assert is_original_request('Puoi darmi il PDF originale del contratto?')
    assert is_original_request('Retrieve my CV')
    assert not is_original_request('Donne les compétences du CV')
    assert document_reply('Recupera il PDF del contratto Synanto',DOCS)['documents']==[DOCS[1]]
    assert len(document_reply('Télécharge le CV et le contrat',DOCS)['documents'])==2
    assert 'Quel original' in document_reply('Télécharge le PDF original',DOCS)['text']
    assert document_reply('Télécharge bulletin.pdf',DOCS)['documents']==[]
    denied=document_reply('Télécharge mon CV',[])
    assert denied['documents']==[] and 'Mathia' not in denied['text']


def test_owner_original_request_uses_same_receipt_without_ai_or_graph_generation():
    service,who,scope,repo,ai,_=fixture()
    asked=document('Télécharge le PDF du contrat Synanto')
    state=dict(current=None,intake=[asked])
    repo.read.return_value=state;repo.claim_chat=AsyncMock(return_value=state);repo.finish_chat=AsyncMock()
    repo.documents=AsyncMock(return_value=DOCS)
    service.ai=None
    assert asyncio.run(service.respond(who,scope,request(),asked['id'],str(uuid4())))==dict(state='completed')
    reply=repo.finish_chat.call_args.args[3]
    assert reply['documents']==[DOCS[1]] and 'attribution' not in reply
    ai.authorize_consolidation.assert_not_awaited();ai.respond.assert_not_called()
    service.context.browse.assert_not_awaited()


def test_source_scoped_generation_excludes_interview_and_prior_assistant_claims():
    service,who,scope,repo,ai,_=fixture()
    asked=document('Que prévoit le contrat Synanto ?')
    prior=document('Quel est le parcours ?')
    previous=dict(document('Une ancienne réponse mélange les documents.'),role='assistant',reply_to=prior['id'])
    doc_rows=[dict(id=str(uuid4()),kind='document',role='user',name=d['filename'],source_revision_id=d['source_revision_id']) for d in DOCS]
    state=dict(current=dict(id='version',revision_ids=[r['revision_id'] for r in ROWS]),intake=[*doc_rows,prior,previous,asked],understanding=ROWS)
    repo.read.return_value=state;repo.claim_chat=AsyncMock(return_value=state);repo.finish_chat=AsyncMock();service.read=AsyncMock(return_value=state)
    ai.respond=AsyncMock(return_value=SimpleNamespace(message=Message(role=MessageRole.ASSISTANT,content='Le contrat prévoit un poste de développeur.'),model='offline',support_basis='canonical',insufficient_context=False,partial_coverage=False,references=[]))
    asyncio.run(service.respond(who,scope,request(),asked['id'],str(uuid4())))
    generated=ai.respond.call_args.args[1]
    assert generated.consolidated_revision_ids==('contract-item',)
    assert generated.messages==(Message(role=MessageRole.USER,content=asked['text']),)


def test_recap_identity_survives_existing_uum_envelope_with_source_evidence():
    import json
    from app.understanding.uum import UumExtractionProvider
    from app.core.models import GenerationRequest,GenerationResult
    from tests.test_consolidation import reference_output
    texts=['Mathia Pagani décrit son expérience dans son CV.',
        'Le contrat de Mathia Pagani documente un poste de développeur.']
    full='\n'.join(texts)
    atomic=dict(format='qh.atomic-understanding/1',items=[dict(text=t,primary_dimension=None,evidence=[dict(quote=t)]) for t in texts])
    captured=[]
    async def replay(request):
        captured.append(request)
        packet=json.loads(request.messages[-1].content)
        output=dict(format='qh.context-consolidation/1',understanding=atomic,
            recap=dict(title='Mathia Pagani — CV et contrat',text='Mathia Pagani : expérience déclarée dans le CV et poste documenté par le contrat.',supporting_statements=texts))
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(reference_output(output,packet))))
    provider=UumExtractionProvider(SimpleNamespace(generate=replay),consolidate=True,with_recap=True)
    packet=dict(source_revision_id=str(uuid4()),input_sha256='offline',text=full,turns=[
        dict(turn_id='cv:page:1',speaker='document CV, page 1',start=0,end=len(texts[0])),
        dict(turn_id='contract:page:2',speaker='document contrat, page 2',start=len(texts[0])+1,end=len(full))])
    generated=asyncio.run(provider.generate(GenerationRequest(messages=(Message(role=MessageRole.SYSTEM,content='Engine'),Message(role=MessageRole.USER,content=json.dumps(packet))))))
    assert 'Mathia Pagani' in provider.recap['title']
    assert [item['text'] for item in json.loads(generated.message.content)['items']]==texts
    instructions=captured[0].messages[0].content
    # Generic naming rule: exact names from the items, never initials expanded or file names.
    assert 'name it exactly as written in the understanding items' in instructions
    assert 'never expand' in instructions and 'covering all its documents' in instructions


def test_guest_original_download_requires_read_and_exact_permission_without_provider():
    from dataclasses import replace
    from datetime import timedelta
    from app.api.guest import COOKIE
    from tests.test_sharing_simplified import setup
    app,_,_,_,now,provider,_,_=setup()
    guest=app.state.services.guest
    with TestClient(app,base_url='https://qh.example.test',headers={'Origin':'https://qh.example.test'}) as client:
        client.cookies.set(COOKIE,'synthetic-verified-cookie')
        assert client.post('/guest/ask',json=dict(question='Télécharge mon CV')).status_code==401
        grant=replace(guest.repository.authenticate.return_value,rights=('READ','ASK_AI'))
        guest.repository.authenticate.return_value=grant
        app.state.services.policy._guest_for.return_value=grant
        guest.repository.documents=AsyncMock(return_value=[])
        denied=client.post('/guest/ask',json=dict(question='Télécharge mon CV'))
        assert denied.status_code==200 and denied.json()['documents']==[]
        assert 'Mathia' not in denied.text and 'source_revision_id' not in denied.text
        guest.repository.documents.return_value=[DOCS[0]]
        allowed=client.post('/guest/ask',json=dict(question='Télécharge mon CV'))
        assert allowed.status_code==200 and allowed.json()['documents']==[DOCS[0]]
        now[0]+=timedelta(hours=2)
        assert client.post('/guest/ask',json=dict(question='Télécharge mon CV')).status_code==401
        provider.generate.assert_not_awaited()
