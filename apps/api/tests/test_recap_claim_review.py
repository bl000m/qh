"""Claim review protocol/Guard checks. Model judgements are replayed, not proven."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.models import Message,MessageRole
from app.projections.disclosure_guard import OutboundDisclosureGuard
from app.understanding import recap
from app.understanding.recap_review import RecapReview,reviewed_evidence
from tests.test_disclosure import policy
from tests.test_modular_recap import projected
from tests.test_document_semantic_permissions import fixture

TEXTS=['Le projet Atlas est proposé, sans approbation.',
       'La décision Lumen a été adoptée le 15 avril 2026.',
       'La version Iris reste expérimentale.',
       'Le déploiement Neptune est prévu sous réserve du financement.']


from tests.recap_review_helpers import review_reply


def corpus():
    texts=[*TEXTS,'Date personnelle : 02/03/1981.','Diagnostic médical privé.']
    rows=[];documents=[str(uuid4()),str(uuid4())]
    for n,text in enumerate(texts):
        source=documents[n%2]
        rows.append(dict(id=str(uuid4()),item_id=str(uuid4()),provenance=[source],
            content=dict(text=text,extraction={},citations=[dict(source_revision_id=source,quote=text)])))
    summary=dict(title='Projet Atlas, décision Lumen, version Iris et déploiement Neptune',
        text='Le projet Atlas est proposé, sans approbation. Lumen a été adoptée. Iris reste expérimentale. Neptune dépend du financement.',
        supporting_statements=TEXTS.copy(),provider_output_sha256='0'*64)
    atomic=dict(items=[dict(text=r['content']['text'],evidence=[dict(quote=r['content']['text'])]) for r in rows])
    packet=dict(evidence=[dict(statement=t,passages=[dict(quote=t,speakers=['user'],turn_ids=[f't{i}'])]) for i,t in enumerate(texts)])
    return summary,atomic,packet,rows,documents


def reviewed_rows():
    summary,atomic,packet,rows,documents=corpus()
    protocol=RecapReview(summary,atomic,packet);protocol.accept(review_reply(protocol.request))
    bound=recap.bind(summary,rows,str(uuid4()))
    base=projected()[0]
    from app.core.models import SourceRevisionRef
    projected_rows=[replace(base,revision_id=r['id'],item_id=r['item_id'],content=r['content'],
        provenance=tuple(SourceRevisionRef(source_id=str(uuid4()),revision_id=p) for p in r['provenance'])) for r in bound]
    return summary,bound,projected_rows,documents


def test_more_than_two_supports_persist_with_exact_claim_and_source_provenance():
    _,rows,_,_=reviewed_rows()
    root=rows[0]['content']['extraction']['recap']
    assert root['presentation_version']==4 and len(root['support_revision_ids'])==4
    evidence=reviewed_evidence(root,{r['id']:r['content'] for r in rows})
    assert set(evidence)==set(TEXTS)
    current=dict(id=root['version_id'],revision_ids=[r['id'] for r in rows])
    assert recap.from_version(rows,current)['text']==root['text']


@pytest.mark.parametrize('failure',['unsupported','coverage','foreign-item','foreign-quote','mismatched-quote','unused','overlap'])
def test_rejects_unsupported_incomplete_or_unbound_claims(failure):
    summary,atomic,packet,_,_=corpus();review=RecapReview(summary,atomic,packet)
    value=json.loads(review_reply(review.request).content)
    claim=value['reviews']['general'][1]
    if failure=='unsupported':claim['supported']=False
    elif failure=='coverage':claim['quote']='Le projet Atlas est proposé, sans approbation.'
    elif failure=='foreign-item':claim['supports'][0]['statement_ref']='OUTSIDE'
    elif failure=='foreign-quote':claim['supports'][0]['evidence_refs']=['q006']
    elif failure=='mismatched-quote':claim['supports'][0]['evidence_refs']=['q002']
    elif failure=='unused':
        for c in value['reviews']['general']:c['supports']=c['supports'][:1]
    else:value['reviews']['general'].append(deepcopy(claim))
    with pytest.raises(ValueError):review.accept(Message(role=MessageRole.ASSISTANT,content=json.dumps(value)))


@pytest.mark.parametrize('originals',[0,1,2])
def test_unrelated_protected_items_do_not_block_reviewed_canonical_recap(originals):
    _,_,rows,documents=reviewed_rows()
    payload,report=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context',original_documents=tuple(documents[:originals])))
    root=rows[0].content['extraction']['recap']
    assert payload['recap']=={k:root[k] for k in ('title','text')}
    assert report['masks'] and report['exclusions']
    assert 'claim_review' not in json.dumps(payload) and 'support_revision_ids' not in json.dumps(payload)
    assert '1981' not in json.dumps(payload) and 'Diagnostic' not in json.dumps(payload)


@pytest.mark.parametrize('failure',['claim','support','source-quote','missing-review','changed-evidence','wrong-version','foreign-provenance'])
def test_necessary_protected_or_changed_evidence_stays_blocked(failure):
    _,_,rows,_=reviewed_rows();root=rows[0].content['extraction']['recap']
    if failure=='claim':root['text']='Diagnostic médical privé.'
    elif failure=='support':rows[0].content['text']='Diagnostic médical privé.'
    elif failure=='source-quote':
        rows[0].content['citations'][0]['quote']='Date personnelle : 02/03/1981.'
        from app.understanding.extractor import digest
        for claim in root['claim_review']['claims']:
            for support in claim['supports']:
                if support['revision_id']==rows[0].revision_id:
                    support['evidence'][0]['quote_sha256']=digest(rows[0].content['citations'][0]['quote'])
        root['claim_review']['integrity_sha256']=digest(dict(title=root['title'],text=root['text'],claims=root['claim_review']['claims'],review_output_sha256=root['claim_review']['review_output_sha256']))
    elif failure=='missing-review':root.pop('claim_review')
    elif failure=='wrong-version':root['version_id']=str(uuid4())
    elif failure=='foreign-provenance':rows[0]=replace(rows[0],provenance=())
    else:rows[0].content['citations'][0]['quote']='Une autre citation.'
    payload,_=OutboundDisclosureGuard().apply(rows,policy(knowledge_scope='context'))
    assert 'recap' not in payload


def test_historical_unreviewed_recap_is_not_upgraded_by_new_sharing():
    service,rows,documents,scope=fixture()
    # Existing fixture becomes reviewed later; explicitly represent retained v3 metadata.
    for row in rows:
        extraction=row.content.get('extraction',{})
        for component in extraction.get('recap_components',[]):
            component['presentation_version']=3;component.pop('claim_review',None)
    preview=asyncio.run(service.prepare(str(uuid4()),scope,policy(knowledge_scope='context',original_documents=documents)))
    assert 'recap' not in preview.payload


def test_pipeline_reviews_after_generation_without_rewriting_candidate():
    from app.understanding.uum import UumExtractionProvider
    from app.core.models import GenerationResult
    summary,atomic,packet,_,_=corpus()
    provider=UumExtractionProvider(SimpleNamespace(generate=AsyncMock(side_effect=lambda request:GenerationResult(message=review_reply(request)))))
    provider.recap=summary
    # The quote resolver is independently covered by Engine tests; here exercise orchestration.
    import app.understanding.uum as uum
    from unittest.mock import patch
    before=summary['text']
    with patch.object(uum,'normalize_output'),patch.object(provider,'_recap_packet',return_value=packet):
        asyncio.run(provider._review_recap(atomic,dict(source_revision_id=str(uuid4()),text='',turns=[])))
    assert provider.delegate.generate.await_count==1 and summary['text']==before
    assert summary['claim_review']['method']=='independent-model-review'



def test_missing_version_basis_keeps_fallback_even_with_reviewed_supports():
    _,_,rows,_=reviewed_rows()
    # Preserve the authorization/basis-presence fence, including unrelated basis refs.
    payload,_=OutboundDisclosureGuard().apply(rows[:4],policy(knowledge_scope='context'))
    assert 'recap' not in payload


def test_rejected_batch_never_attaches_a_partial_review():
    summary,atomic,packet,_,_=corpus()
    summary['documents']=[dict(title='Un autre résumé',text='Texte à refuser.',supporting_statements=TEXTS[:1])]
    review=RecapReview(summary,atomic,packet);value=json.loads(review_reply(review.request).content)
    value['reviews']['d1'][0]['supported']=False
    with pytest.raises(ValueError):review.accept(Message(role=MessageRole.ASSISTANT,content=json.dumps(value)))
    assert 'claim_review' not in summary and 'claim_review' not in summary['documents'][0]


def test_semantic_review_failure_prevents_canonical_publication():
    from tests.test_consolidation import fixture as consolidation_fixture,consolidation_output,reference_output
    from app.core.models import GenerationResult
    from unittest.mock import Mock
    service,who,scope,repo,ai,batch=consolidation_fixture()
    text=batch['intake'][0]['text']
    atomic=dict(format='qh.atomic-understanding/1',items=[dict(text=text,primary_dimension=None,evidence=[dict(quote=text)])])
    def generate(request):
        packet=json.loads(request.messages[-1].content)
        if 'candidates' in packet:
            data=json.loads(review_reply(request).content);data['reviews']['general'][0]['supported']=False
            return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(data)))
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(reference_output(consolidation_output(atomic),packet))))
    delegate=Mock(generate=AsyncMock(side_effect=generate));ai._provider.return_value=delegate
    with pytest.raises(ValueError,match='Unsupported recap assertion'):asyncio.run(service.consolidate(who,scope))
    assert delegate.generate.await_count==2
    repo.publish.assert_not_awaited();repo.fail.assert_awaited_once()



def test_protected_unrelated_carrier_cannot_taint_a_reviewed_recap():
    summary,atomic,packet,rows,_=corpus()
    review=RecapReview(summary,atomic,packet);review.accept(review_reply(review.request))
    reordered=[rows[-1],*rows[:-1]]
    bound=recap.bind(summary,reordered,str(uuid4()))
    base=projected()[0]
    from app.core.models import SourceRevisionRef
    projected_rows=[replace(base,revision_id=r['id'],item_id=r['item_id'],content=r['content'],
        provenance=tuple(SourceRevisionRef(source_id=str(uuid4()),revision_id=p) for p in r['provenance'])) for r in bound]
    payload,report=OutboundDisclosureGuard().apply(projected_rows,policy(knowledge_scope='context'))
    assert payload['recap']['text']==summary['text'] and report['exclusions']
    assert 'Diagnostic' not in json.dumps(payload)


def test_generator_cannot_self_certify_review_metadata():
    summary,atomic,_,_,_=corpus()
    summary['claim_review']=dict(method='independent-model-review')
    wire=dict(format=recap.FORMAT,understanding=dict(format='qh.atomic-understanding/1',items=atomic['items']),recap=summary)
    summary.pop('provider_output_sha256')
    with pytest.raises(ValueError):recap.decode(json.dumps(wire))
