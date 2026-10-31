"""Universal navigation assignments; independent of epistemic and item review state."""
from copy import deepcopy

PRIMARY_DIMENSIONS = (
    'situation_information', 'objectives_intentions', 'decisions_actions',
    'constraints_preferences', 'hypotheses_uncertainties', 'open_questions',
)
# Persisted version-bound recap contract, shared by understanding and projections.
RECAP_FORMAT, RECAP_PRESENTATION_VERSIONS = 'qh.context-recap/1', (2, 3, 4)


def validate_primary(value, evidence_count):
    if not isinstance(value, dict) or set(value) != {'value', 'certainty', 'evidence_refs', 'review_state'}:
        raise ValueError('Explicit primary assignment required')
    if value['value'] not in PRIMARY_DIMENSIONS or value['certainty'] not in ('asserted', 'tentative'):
        raise ValueError('Invalid primary dimension or certainty')
    if value['review_state'] not in ('proposed', 'accepted', 'rejected'):
        raise ValueError('Invalid assignment review')
    refs = value['evidence_refs']
    if (not isinstance(refs, list) or not refs
            or any(type(i) is not int or not 0 <= i < evidence_count for i in refs)
            or len(set(refs)) != len(refs)):
        raise ValueError('Exact primary assignment evidence required')
    return deepcopy(value)


def review_primary(content, decision):
    if not isinstance(decision, dict) or set(decision) - {'state', 'value', 'evidence_refs'} or 'state' not in decision:
        raise ValueError('Explicit primary review decision required')
    state = decision['state']
    current = content.get('primary_dimension')
    citations = content.get('citations', [])
    if not isinstance(citations, list):
        raise ValueError('Canonical citations required')
    if state == 'proposed':
        if set(decision) != {'state', 'value', 'evidence_refs'}:
            raise ValueError('A replacement requires evidence and dimension')
        return validate_primary(dict(value=decision['value'], certainty='tentative',
            evidence_refs=decision['evidence_refs'], review_state='proposed'), len(citations))
    if state not in ('accepted', 'rejected') or set(decision) != {'state'} or current is None:
        raise ValueError('Accept/reject requires an existing primary assignment')
    return dict(validate_primary(current, len(citations)), review_state=state)
