"""Ephemeral reference-only guest continuity, bound to the exact authorized payload."""
from collections import OrderedDict
from hashlib import sha256
import json
from time import monotonic


def checked_referents(groups, allowed):
    if (not isinstance(groups, list) or len(groups)>8
        or any(not isinstance(group,list) or not 1<=len(group)<=16
            or any(not isinstance(ref,str) or ref not in allowed for ref in group)
            or len(set(group))!=len(group) for group in groups)):
        raise ValueError('Invalid conversation references')
    return [[ref for ref in group] for group in groups]


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
