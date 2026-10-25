"""Hand-authored QH-51 fixtures. Exact complete inputs only; NEVER a classifier.

Outputs exercise the semantic adapter, provenance and governance contracts. They
are not model-inference results or evidence of semantic extraction quality.
"""
import json
from copy import deepcopy

from adapters.llm.offline import FixtureUnderstandingProvider

WELLBEING = (
    'Je dors cinq heures. Mon objectif est de dormir sept heures et de garder une soirée calme.',
    'Je choisis une marche douce après le déjeuner. Réduire les écrans pourrait faciliter mon endormissement.',
    'Quel effet aura la marche sur mon énergie ?'
)
PROFESSIONAL = (
    'Nous voulons isoler les données personnelles par service dans notre API.',
    'Nous choisissons PostgreSQL comme stockage canonique. La livraison dépend d’un audit de sécurité.',
    'Quel niveau de disponibilité devons-nous garantir ?'
)
ALIAS = 'Je conserve cet objectif de sommeil.'


def descriptor(dimension, value, *, certainty='tentative', name_candidate=None):
    result=dict(dimension=dimension,value=value,certainty=certainty,evidence_refs=[0])
    if name_candidate is not None:result['name_candidate']=name_candidate
    return result


def candidates(case):
    # Explicit human-readable synthetic reference, not extracted from keywords.
    specs = [
        ('sommeil',0,'Retrouver sept heures de sommeil',['Sommeil','Habitudes de vie','Nutrition'],'objectif','asserted'),
        ('marche',1,'Choisir une marche douce après le déjeuner',['Activité physique','Habitudes de vie'],'décision','asserted'),
        ('ecrans',1,'Réduire les écrans pourrait faciliter l’endormissement',['Sommeil','Habitudes de vie'],'hypothèse','tentative'),
        ('energie',2,'Examiner l’effet de la marche sur l’énergie',['Activité physique','Énergie'],'question ouverte','tentative'),
    ] if case=='wellbeing' else [
        ('api',0,'Isoler les données personnelles par service',['Architecture','Protection des données'],'objectif','asserted'),
        ('sql',1,'Choisir PostgreSQL comme stockage canonique',['Architecture','Données persistantes'],'décision','asserted'),
        ('audit',1,'Subordonner la livraison à un audit de sécurité',['Livraison','Protection des données'],'contrainte','asserted'),
        ('availability',2,'Déterminer le niveau de disponibilité à garantir',['Fiabilité'],'question ouverte','tentative'),
    ]
    turns=WELLBEING if case=='wellbeing' else PROFESSIONAL
    return [dict(local_id=local,shape='item',text=text,
        descriptors=[*[descriptor('thematic',v,certainty=certainty) for v in topics],descriptor('semantic_role',role,certainty=certainty)],
        evidence=[dict(turn_index=index,quote=turns[index])]) for local,index,text,topics,role,certainty in specs]


class ExactSemanticFixtureProvider:
    """Only the full approved synthetic input maps to fixed authored candidates."""
    def __init__(self):self.calls=0;self.requests=[]

    async def generate(self, request):
        source=json.loads(request.messages[-1].content)
        texts=tuple(source['text'][turn['start']:turn['end']] for turn in source['turns'])
        self.calls+=1;self.requests.append(deepcopy(source))
        joined=False
        if texts==WELLBEING:items=candidates('wellbeing')
        elif texts==PROFESSIONAL:items=candidates('professional')
        elif texts==('\n'.join(WELLBEING),):items=candidates('wellbeing');joined=True
        elif texts==('\n'.join(PROFESSIONAL),):items=candidates('professional');joined=True
        elif texts==(ALIAS,):items=[dict(local_id='alias',shape='item',text='Conserver l’objectif de sommeil',descriptors=[descriptor('thematic','Repos nocturne',name_candidate='Sommeil'),descriptor('semantic_role','objectif')],evidence=[dict(turn_index=0,quote=ALIAS)])]
        else:raise ValueError('Unknown complete synthetic input; no inference or fallback')
        for item in items:
            for evidence in item['evidence']:
                index=evidence.pop('turn_index')
                evidence['turn_id']=source['turns'][0 if joined else index]['turn_id']
        return await FixtureUnderstandingProvider(items).generate(request)
