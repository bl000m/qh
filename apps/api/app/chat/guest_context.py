"""Ephemeral reference-only guest continuity, bound to the exact authorized payload."""
from collections import OrderedDict
from hashlib import sha256
import json
import re
from time import monotonic


def checked_referents(groups, allowed):
    if (not isinstance(groups, list) or len(groups)>8
        or any(not isinstance(group,list) or not 1<=len(group)<=16
            or any(not isinstance(ref,str) or ref not in allowed for ref in group)
            or len(set(group))!=len(group) for group in groups)):
        raise ValueError('Invalid conversation references')
    return [[ref for ref in group] for group in groups]


def ordinal_focus(question, conversation):
    """Resolve only whole-message, explicit ordinal follow-ups, never facts."""
    patterns=(
        (r'(?:(?:approfondisci|sviluppa|puoi approfondire) )?(?:la|il) (prima|primo|seconda|secondo)',
            {'prima':0,'primo':0,'seconda':1,'secondo':1}),
        (r'(?:(?:approfondis|développe|détaille|peux-tu (?:approfondir|détailler|développer)) )?(?:la|le) (première|premier|seconde|second|deuxième)',
            {'première':0,'premier':0,'seconde':1,'second':1,'deuxième':1}),
        (r'(?:(?:expand on|elaborate on) )?(?:the )?(first|second)', {'first':0,'second':1}),
    )
    value=question.strip().casefold().rstrip(' .!?')
    value=re.sub(r'^et (?:pour )?', '', value)
    for pattern,positions in patterns:
        match=re.fullmatch(pattern,value)
        if match:
            groups=next((turn for turn in reversed(conversation) if len(turn)>1),[])
            position=positions[match[1]]
            if len(groups)<=position:return []
            selected=groups[position]
            return selected if sum(set(group)==set(selected) for group in groups)==1 else []
    return None


class GuestReferenceHistory:
    def __init__(self, *, clock=monotonic):
        self.clock, self.entries = clock, OrderedDict()

    @staticmethod
    def fingerprint(snapshot, payload):
        return sha256(json.dumps([snapshot,payload],sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def read(self, session, snapshot, payload):
        now=self.clock()
        for key, (expiry, _, _) in list(self.entries.items()):
            if expiry<=now:
                self.entries.pop(key)
        entry=self.entries.get(session)
        fingerprint=self.fingerprint(snapshot,payload)
        if entry is None:
            return []
        if entry[1]!=fingerprint:
            self.entries.pop(session)
            return []
        allowed={item['reference'] for item in payload['items']}
        return [checked_referents(groups,allowed) for groups in entry[2]]

    def append(self, session, snapshot, payload, groups):
        turns=self.read(session,snapshot,payload)
        groups=checked_referents(groups,{item['reference'] for item in payload['items']})
        if not turns and not groups:
            return
        self.entries[session]=(self.clock()+900,self.fingerprint(snapshot,payload),(turns+[groups])[-6:])
        self.entries.move_to_end(session)
        while len(self.entries)>128:
            self.entries.popitem(last=False)


def clarification(question):
    value=question.casefold()
    if re.search(r'\b(approfondisci|prima|seconda|perché|quali)\b',value):
        answer='Non riesco a identificare con certezza il riferimento precedente. Puoi indicare il nome dell’elemento da approfondire o confrontare?'
    elif re.search(r'\b(first|second|explain|why|elaborate)\b',value):
        answer='I cannot identify the previous reference with certainty. Which named item would you like to explore or compare?'
    else:
        answer='Je ne peux pas identifier avec certitude le renvoi à la réponse précédente. Pouvez-vous nommer l’élément à détailler ou à comparer ?'
    return dict(answer=answer,reference_aliases=[],referents=[],support_basis='dialogue',insufficient_context=False,simulated=False)


def context_clarification(question, payload):
    """Fail closed on missing temporal evidence or unavailable previous wording."""
    value=question.casefold()
    previous=re.search(r'(?:ta|tes|votre|previous|tua|tue) (?:réponse|réponses|answer|risposta|risposte)',value)
    previous=previous or re.search(r'(?:tu|vous).{0,40}(?:confon|mélang)|(?:confon\w*|mélang\w*)-(?:tu|vous)|(?:you|hai).{0,40}(?:confus|said|detto)',value)
    challenge=re.search(r'pourquoi|comment|confon|confusion|mélang|incorrect|erreur|why|perché|confus',value)
    if previous and challenge:
        return clarification(question)
    chronology=re.search(r'derni[eè]res? (?:deux )?expériences? professionnelles?|ultime (?:due )?esperienze (?:lavorative|professionali)|last two (?:jobs|work experiences|professional experiences)',value)
    if chronology and not any(re.search(r'\b(?:19|20)\d{2}\b',item['text']) for item in payload['items']):
        if 'ultime' in value:
            answer='Le informazioni autorizzate non riportano periodi per ordinare le esperienze lavorative. Non posso identificare le ultime due senza inventare la cronologia. Attività e progetti restano consultabili separatamente.'
        elif 'last two' in value:
            answer='The authorized information has no periods for ordering the jobs. I cannot identify the last two without inventing a chronology. Activities and projects can be explored separately.'
        else:
            answer='Les informations autorisées ne donnent pas de périodes pour classer les expériences professionnelles. Je ne peux donc pas identifier les deux dernières sans inventer la chronologie. Les activités et projets restent consultables séparément.'
        return dict(answer=answer,reference_aliases=[],referents=[],support_basis='insufficient',insufficient_context=True,simulated=False)
    return None
