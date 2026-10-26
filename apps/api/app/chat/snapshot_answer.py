"""Validate snapshot references and output disclosure; no canonical hydration."""
import json

from app.core.models import MessageRole
from app.projections.disclosure_guard import HIGH_RISK,redact
from app.chat.guest import unique_fields


def answer_schema(payload):
    return dict(type='object',additionalProperties=False,
        required=['answer','reference_aliases','insufficient_context','support_basis'],properties=dict(
        answer=dict(type='string',minLength=1,maxLength=1_000_000),
        reference_aliases=dict(type='array',maxItems=100,items=dict(type='string',enum=[i['reference'] for i in payload['items']])),
        insufficient_context=dict(type='boolean'),
        support_basis=dict(type='string',enum=['dialogue','canonical','mixed','insufficient'])))


def decode_snapshot_answer(message,payload):
    if message.role!=MessageRole.ASSISTANT or len(message.content.encode())>2_000_000:raise ValueError('Invalid answer envelope')
    value=json.loads(message.content,object_pairs_hook=unique_fields)
    if not isinstance(value,dict) or set(value)!={'answer','reference_aliases','insufficient_context','support_basis'}:raise ValueError('Invalid answer fields')
    text,refs,basis=value['answer'],value['reference_aliases'],value['support_basis']
    allowed={i['reference'] for i in payload['items']}
    if (not isinstance(text,str) or not 1<=len(text.strip())<=1_000_000 or type(value['insufficient_context']) is not bool
        or not isinstance(refs,list) or len(refs)>100 or any(not isinstance(r,str) or r not in allowed for r in refs)
        or len(set(refs))!=len(refs) or basis not in ('dialogue','canonical','mixed','insufficient')
        or basis in ('canonical','mixed') and not refs or basis=='dialogue' and refs):raise ValueError('Invalid snapshot support')
    if HIGH_RISK.search(text) or any(ord(c)<32 and c not in '\n\t' for c in text):raise ValueError('Output disclosure refused')
    value['answer']=redact(text)[0]
    return value
