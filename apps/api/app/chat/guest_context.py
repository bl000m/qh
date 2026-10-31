"""Ephemeral reference-only guest continuity, bound to the exact authorized payload."""
from collections import OrderedDict
from hashlib import sha256
import json
import re
from time import monotonic


def checked_referents(groups, allowed):
    if (not isinstance(groups, list) or len(groups)>8
        or any(not isinstance(group,list) or not 1<=len(group)<=100
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
    mentions=0
    for pattern,positions in patterns:
        mentions += len(re.findall(r'(?<!\w)(?:'+pattern+r')(?!\w)',value))
        match=re.fullmatch(pattern,value)
        if match:
            groups=[]
            for turn in reversed(conversation):
                if not turn:break  # A non-list response invalidates the previous list.
                if len(turn)>1:
                    groups=turn
                    break
            position=positions[match[1]]
            if len(groups)<=position:return []
            selected=groups[position]
            return selected if sum(set(group)==set(selected) for group in groups)==1 else []
    # Compound/unrecognized ordinal requests must not become a fresh selection.
    compound=re.search(r'[?;:]|\b(?:puis|poi|then|ensuite|and|et)\b',value)
    return [] if mentions>1 or (mentions and compound) else None


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
    """Do not reconstruct previous wording that is deliberately not retained.

    Temporal sufficiency belongs to selection over current items AND approved quotes.
    """
    value=question.casefold()
    previous=re.search(r'(?:ta|tes|votre|previous|tua|tue) (?:réponse|réponses|answer|risposta|risposte)',value)
    previous=previous or re.search(r'(?:tu|vous).{0,40}(?:confon|mélang)|(?:confon\w*|mélang\w*)-(?:tu|vous)|(?:you|hai).{0,40}(?:confus|said|detto)',value)
    challenge=re.search(r'pourquoi|comment|confon|confusion|mélang|incorrect|erreur|why|perché|confus',value)
    if previous and challenge:
        return clarification(question)
    return None
