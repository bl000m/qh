"""Bounded local parsing and single-Engine replay. No external inference."""
import asyncio
from io import BytesIO
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from fastapi.testclient import TestClient

from adapters.pdf import extract_pdf
from app.api.security import SecurityBindings
from app.composition import ApplicationServices
from app.core.models import ContextSpaceNotFound, GenerationResult, Message, MessageRole, GenerationRequest
from app.main import create_app
from app.understanding.documents import DocumentInvalid, MAX_PDF_BYTES, prepare_document, original_citations
from app.understanding.uum import UumExtractionProvider
from tests.test_consolidation import fixture


def pdf_bytes(texts=('Le responsable est Alice.',), password=None):
    writer=PdfWriter()
    for text in texts:
        page=writer.add_blank_page(width=612,height=792)
        if text:
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
            stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 50 700 Td ('+text+') Tj ET').encode())
            page[NameObject('/Contents')]=writer._add_object(stream)
    if password is not None:writer.encrypt(password)
    out=BytesIO();writer.write(out);return out.getvalue()


def test_pdf_extraction_pages_size_and_no_script_execution():
    data=pdf_bytes(('Le responsable est Alice.','Autre page.'))
    assert asyncio.run(extract_pdf(data))==['Le responsable est Alice.','Autre page.']
    assert asyncio.run(extract_pdf(data+b' '*(MAX_PDF_BYTES-len(data))))==['Le responsable est Alice.','Autre page.']


@pytest.mark.parametrize('data,reason',[(b'%PDF-broken','corrompu'),(b'plain text','corrompu'),
    (pdf_bytes(password=''),'mot de passe'),(pdf_bytes(('',)),'aucun texte'),
    (b'x'*(MAX_PDF_BYTES+1),'3 MiB')])
def test_pdf_refusals(data,reason):
    with pytest.raises(DocumentInvalid,match=reason):asyncio.run(extract_pdf(data))


def test_upload_auth_precedes_parsing_and_private_download():
    service,who,scope,repo,ai,_=fixture()
    service.pdf_parser=AsyncMock(return_value=['Le responsable est Alice.','Autre page.'])
    repo.import_document=AsyncMock(return_value=dict(context_id=scope))
    repo.document=AsyncMock(return_value=dict(original=b'PDF ORIGINAL',filename='test.pdf'))
    async def authenticate(token):return who.subject_id
    app=create_app(services=ApplicationServices(context=service.context,policy=service.policy,consolidation=service),
        security=SecurityBindings(authenticate=authenticate,policy=service.policy))
    with TestClient(app) as client:
        path=f'/context-spaces/{scope}/workspace/documents/{uuid4()}'
        headers={'Authorization':'Bearer owner','Content-Type':'application/pdf','X-Document-Name':'test.pdf','X-Document-Display-Name':'Profil%20technique'}
        assert client.put(path,headers=headers,content=b'%PDF-test').status_code==200
        _,doc,source,data=repo.import_document.call_args.args
        assert data==b'%PDF-test' and doc['source_revision_id']==source['id']
        assert source['origin']['turns'][1]['turn_id'].endswith(':page:2')
        assert source['source_name']=='test.pdf' and doc['display_name']=='Profil technique'
        assert client.put(path,headers=headers,content=b'x'*(MAX_PDF_BYTES+1)).status_code==413
        service.pdf_parser.assert_awaited_once()
        assert client.put(path,headers={**headers,'Content-Type':'text/plain'},content=b'abc').status_code==415
        download=client.get(path,headers=headers)
        assert download.content==b'PDF ORIGINAL' and download.headers['cache-control']=='private, no-store'
        assert download.headers['content-disposition'].startswith('attachment;')
        service.policy.evaluate.return_value=SimpleNamespace(allowed=False)
        assert client.put(path,headers=headers,content=b'%PDF-test').status_code==404
        assert client.get(path,headers=headers).status_code==404
        service.pdf_parser.assert_awaited_once();ai._provider.assert_not_called()


def test_original_page_citations_preserve_exact_text_and_offsets():
    doc,source=prepare_document(str(uuid4()),str(uuid4()),'test.pdf',b'original',['First page.','Second page.'])
    row=dict(provenance=['consolidation'],content=dict(citations=[dict(source_revision_id='consolidation',
        start=1,end=13,quote='Second page.',turn_id=doc['document_turns'][1]['id'])]))
    derived=original_citations([row],[source])[0]
    ref=derived['content']['citations'][1]
    assert ref['source_revision_id']==source['id']
    assert source['content'][ref['start']:ref['end']]=='Second page.'
    assert source['id'] in derived['provenance']
    assert len(row['content']['citations'])==1


def test_long_document_all_parts_are_sent_then_validated_recap():
    text=''.join(f'Line {i}: some unverified source information.\n' for i in range(700))
    packets=[]
    async def generate(request):
        packet=json.loads(request.messages[-1].content)
        if 'statements' in packet:
            assert packet['evidence'][0]['passages'][0]['speakers']==['unverified PDF']
            assert packet['evidence'][0]['passages'][0]['quote'] in text
            out=dict(title='Document',text='Proposed document information.',supporting_statements=[packet['statements'][0]])
        else:
            packets.append(packet)
            out=dict(format='qh.atomic-understanding.refs/1',items=[dict(text='Part '+str(len(packets)),
                primary_dimension=None,evidence_refs=[packet['passages'][0]['ref']])])
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(out)))
    provider=UumExtractionProvider(Mock(generate=AsyncMock(side_effect=generate)),consolidate=True,with_recap=True,chunked=True)
    source=dict(source_revision_id=str(uuid4()),input_sha256='test',text=text,
        turns=[dict(turn_id='page:1',speaker='unverified PDF',start=0,end=len(text))])
    request=GenerationRequest(messages=(Message(role=MessageRole.SYSTEM,content='source'),
        Message(role=MessageRole.USER,content=json.dumps(source))))
    result=asyncio.run(provider.generate(request))
    assert len(packets)>1 and ''.join(s['text'] for p in packets for s in p['segments'])==text
    assert provider.parts[0]['start']==0 and provider.parts[-1]['end']==len(text)
    assert len(json.loads(result.message.content)['items'])==len(packets)
    assert provider.recap['supporting_statements']==['Part 1']
    assert all(len(''.join(s['text'] for s in p['segments']))<=12000 for p in packets)


def test_empty_pages_are_retained_without_invalid_zero_length_engine_turns():
    doc,source=prepare_document(str(uuid4()),str(uuid4()),'test.pdf',b'original',['Page 1.','','Page 3.'])
    assert len(doc['document_turns'])==3 and doc['document_turns'][1]['text']==''
    assert [t['turn_id'].split(':')[-1] for t in source['origin']['turns']]==['1','3']
    assert source['origin']['metadata']['empty_pages']==[2]


def test_empty_pdf_understanding_is_not_reported_as_semantic_success(monkeypatch):
    service,who,scope,repo,_,batch=fixture()
    batch['intake'][0]['source_revision_id']=str(uuid4())
    monkeypatch.setattr('app.understanding.consolidation.propose_selected_conversation',
        AsyncMock(return_value=({'id':str(uuid4())},())))
    with pytest.raises(DocumentInvalid,match='originaux restent conservés'):
        asyncio.run(service.consolidate(who,scope))
    repo.publish.assert_not_awaited();repo.fail.assert_awaited_once()
