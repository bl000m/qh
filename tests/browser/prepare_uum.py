"""Fresh UUM-only browser dataset: no v1/v2 revisions or provider HTTP."""
import asyncio
import json
import os
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from adapters.postgres.canonical import CanonicalRepository
from adapters.postgres.config import database_url
from adapters.postgres.demo_identities import DEMO_IDENTITIES
from adapters.postgres.semantic_profiles import register_uum_profiles
from app.core.models import GenerationResult, Message, MessageRole
from app.core.uum import PRIMARY_DIMENSIONS
from app.understanding.selected import propose_selected_conversation
from app.understanding.uum import FORMAT

assert os.environ.get('QH_UUM_BROWSER_TEST')=='1' and os.environ['POSTGRES_HOST']=='postgres'
owner=str(DEMO_IDENTITIES[0][1]);repo=CanonicalRepository(url=database_url(),subject_id=owner)
register_uum_profiles(repo)
policy=Mock(evaluate=AsyncMock(return_value=Mock(allowed=True)))  # Fixture preparation only; runtime uses owner policy.
scopes=[]
examples={
    'Santé': ['Je dors cinq heures.', 'Je veux dormir sept heures.', 'Je choisis une marche après déjeuner.', 'Je préfère une activité douce.', 'Les écrans pourraient retarder mon sommeil.', 'Quel effet la marche aura-t-elle sur mon énergie ?'],
    'Projet QH': ['PostgreSQL conserve nos données canoniques.', 'Nous voulons un contexte portable.', 'Nous suspendons le merge de cette PR.', 'Le plafond autorisé est de 0,02 USD.', 'La pagination pourrait masquer certains éléments.', 'Comment traiter deux propositions contradictoires ?'],
    'Recruiting': ['L’entretien a lieu vendredi.', 'Nous souhaitons recruter une personne senior.', 'J’ai envoyé l’invitation.', 'La candidate demande du télétravail.', 'Son départ pourrait être lié au trajet.', 'Quand est-elle disponible ?'],
    'Voyage': ['Le vol réservé part le 8 juin.', 'Je souhaite une semaine de repos.', 'J’ai réservé le billet.', 'Mon budget maximal est de 800 euros.', 'Il pourrait pleuvoir pendant le séjour.', 'Faut-il un visa pour ce trajet ?'],
    'Relations personnelles': ['Mon amie a déménagé.', 'Je souhaite reprendre contact.', 'Nous avons convenu de nous appeler vendredi.', 'Je préfère parler en privé.', 'Il est peut-être contrarié.', 'Que souhaite-t-elle pour la suite ?'],
}
for name in ('Santé','Projet QH','Recruiting','Voyage','Relations personnelles','UUM vide'):
    scope=str(uuid4())
    with repo.connect() as c:
        c.execute('INSERT INTO context_spaces(id,owner_id,name) VALUES (%s,%s,%s)',(scope,owner,name))
    if name!='UUM vide':
        quotes=examples[name]
        wire=dict(format=FORMAT,items=[dict(text=quote,primary_dimension=dimension,
            assignment_certainty='asserted',evidence=[{'quote':quote}]) for quote,dimension in zip(quotes,PRIMARY_DIMENSIONS)])
        provider=Mock(generate=AsyncMock(return_value=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(wire)))))
        source,rows=asyncio.run(propose_selected_conversation(subject_id=owner,context_id=scope,
            conversation=dict(id=str(uuid4()),acquired_at='2026-10-21T12:00:00Z',metadata={'synthetic':True},
                turns=[dict(id=str(uuid4()),speaker='user (owner-declared)',text=quote) for quote in quotes]),
            extraction_key='uum-isolated-fixture/1',policy=policy,provider=provider,descriptor_version=3))
        repo.save(sources=[source],revisions=rows)
    scopes.append(dict(scope=scope,name=name,objective=examples[name][1] if name in examples else None))
print(json.dumps(dict(owner=owner,scope=scopes[0]['scope'],proposed_scope=scopes[0]['scope'],
    empty_scope=scopes[-1]['scope'],understanding_scope=scopes[0]['scope'],demo_spaces=scopes[:-1])))
