"""Prepare exact synthetic disclosure payloads OFFLINE; contains no HTTP client."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/api'))
from app.core.models import GenerationRequest, GenerationResult, Message, MessageRole
from app.understanding.extractor import UnderstandingExtractor, canonical_json
from app.understanding.selected import selected_source
from app.understanding.semantic import SemanticExtractionProvider
from tests.semantic_fixtures import WELLBEING, PROFESSIONAL, ALIAS


def prepare():
    payloads = []
    cases = [
        ('Bien-être', WELLBEING, ()),
        ('Projet professionnel', PROFESSIONAL, ()),
        ('Bien-être', (ALIAS,), ('Sommeil','Activité physique','Habitudes de vie','Énergie')),
        ('Projet professionnel', ('Nous conservons cet objectif d’isolation des données par service.',),
         ('Architecture','Protection des données','Données persistantes','Livraison','Fiabilité')),
    ]
    for index,(name,texts,names) in enumerate(cases,1):
        scope = str(uuid5(NAMESPACE_URL,'qh51-authorized-synthetic/'+name))
        conversation = dict(id='qh51-experiment-'+str(index),acquired_at='2026-10-21T12:00:00Z',
            turns=[dict(id=str(uuid5(NAMESPACE_URL,'qh51-experiment-turn/'+str(index)+'/'+str(i))),speaker='user (owner-declared)',text=text) for i,text in enumerate(texts)],
            metadata=dict(purpose='QH-51 synthetic semantic extraction experiment proposal',synthetic=True))
        source = selected_source(scope,conversation)
        captured = []
        class Capture:
            async def generate(self,request):
                captured.extend([dict(role=m.role.value,content=m.content) for m in request.messages])
                return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content='{"items":[]}'))
        base = GenerationRequest(messages=(Message(role=MessageRole.SYSTEM,content='Engine request'),Message(role=MessageRole.USER,
            content=canonical_json(dict(source_revision_id=source['id'],input_sha256=UnderstandingExtractor.source_hash(source),text=source['content'],turns=source['origin']['turns'])))))
        asyncio.run(SemanticExtractionProvider(Capture(),known_themes=names,vocabulary_partial=True).generate(base))
        upper = len(canonical_json(captured).encode())+256
        if upper>8000:raise ValueError('Input upper bound exceeded before any possible disclosure')
        body=dict(model='mistral-small-2603',messages=captured,temperature=0,max_tokens=2000,response_format={'type':'json_object'})
        payloads.append(dict(call=index,space=name,context_id=scope,source_revision_id=source['id'],
            vocabulary_basis='Explicit synthetic reference assignments, not unreviewed output from earlier calls',
            input_tokens_upper_bound=upper,request_sha256=hashlib.sha256(canonical_json(body).encode()).hexdigest(),body=body))
    return dict(purpose='QH-51 isolated extraction experiment — PROPOSED, NOT AUTHORIZED',
        endpoint='https://api.mistral.ai/v1/chat/completions',max_posts=4,max_usd='0.02',output_tokens_per_post=2000,input_tokens_per_post_upper_bound=8000,
        provider_calls_executed=0,payloads=payloads)


if __name__=='__main__':
    print(json.dumps(prepare(),ensure_ascii=False,indent=2))
