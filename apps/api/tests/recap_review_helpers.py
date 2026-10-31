"""Controlled model replay for orchestration tests, not semantic entailment proof."""
from copy import deepcopy
import json

from app.core.models import Message,MessageRole


def review_reply(request):
    packet=json.loads(request.messages[-1].content);results={}
    for key,candidate in packet['candidates'].items():
        supports=[dict(statement_ref=r,evidence_refs=next(s['evidence_refs'] for s in packet['statements'] if s['ref']==r)) for r in candidate['declared_supports']]
        results[key]=[dict(field=field,quote=candidate[field],supported=True,supports=deepcopy(supports)) for field in ('title','text')]
    return Message(role=MessageRole.ASSISTANT,content=json.dumps(dict(format='qh.recap-claim-review/1',reviews=results)))


def historical_contents(contents):
    """Represent retained v3 metadata; never reclassify it as model-reviewed."""
    for content in contents:
        extraction=content.get('extraction',{})
        values=[*extraction.get('recap_components',[])]
        if extraction.get('recap'):values.append(extraction['recap'])
        for component in values:
            component['presentation_version']=3
            component.pop('claim_review',None)
