"""Versioned explicit assignments; no inference from labels, text or SQL kinds."""
from copy import deepcopy
import unicodedata

DIMENSIONS = ('thematic', 'semantic_role')


def theme_name(value):
    if not isinstance(value, str) or '\0' in value or len(value) > 256:
        raise ValueError('Bounded explicit descriptor value required')
    result = unicodedata.normalize('NFC', ' '.join(value.split()))
    if not result:
        raise ValueError('Nonempty descriptor value required')
    return result


def qualified_assignments(values, evidence_count, known_themes=()):
    """Validate model assignments before canonical publication, never trust review."""
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError('Bounded descriptor assignments required')
    found = {}
    for raw in values:
        if not isinstance(raw, dict) or not {'dimension', 'value', 'certainty', 'evidence_refs'} <= raw.keys() or raw.keys() - {'dimension', 'value', 'certainty', 'evidence_refs', 'name_candidate'}:
            raise ValueError('Explicit versioned descriptor fields required')
        if raw['dimension'] not in DIMENSIONS or raw['certainty'] not in ('asserted', 'tentative'):
            raise ValueError('Invalid assignment dimension or certainty')
        refs = raw['evidence_refs']
        if (not isinstance(refs, list) or not 1 <= len(refs) <= 100 or
                any(type(i) is not int or not 0 <= i < evidence_count for i in refs) or len(set(refs)) != len(refs)):
            raise ValueError('Exact assignment evidence references required')
        value = dict(deepcopy(raw), value=theme_name(raw['value']), evidence_refs=sorted(refs))
        if 'name_candidate' in raw:
            candidate = raw['name_candidate']
            if (raw['dimension'] != 'thematic' or candidate not in known_themes or
                    not isinstance(candidate, str) or theme_name(candidate) != candidate or candidate == value['value']):
                raise ValueError('Name candidate must be an exact disclosed Space theme')
        key = (value['dimension'], value['value'])
        if key in found and found[key] != value:
            raise ValueError('Discordant duplicate assignment')
        found[key] = value
    return list(found.values())


def validate_persisted_assignments(values, evidence_count):
    if not isinstance(values, list):
        raise ValueError('Semantic assignments required')
    raw = []
    for value in values:
        if not isinstance(value, dict) or value.get('review_state') not in ('proposed', 'accepted', 'rejected'):
            raise ValueError('Explicit backend review state required')
        entry = dict(value)
        entry.pop('review_state')
        raw.append(entry)
    candidates = tuple(d['name_candidate'] for d in raw if isinstance(d.get('name_candidate'), str))
    if qualified_assignments(raw, evidence_count, candidates) != raw:
        raise ValueError('Canonical normalized assignments required')


def review_assignments(values, decisions, evidence_count):
    validate_persisted_assignments(values, evidence_count)
    if not isinstance(decisions, list) or not 1 <= len(decisions) <= 100:
        raise ValueError('Bounded explicit assignment decisions required')
    result, seen = deepcopy(values), set()
    for decision in decisions:
        if (not isinstance(decision, dict) or not {'index', 'state'} <= decision.keys() or
                decision.keys() - {'index', 'state', 'reuse_value'}):
            raise ValueError('Explicit assignment decision fields required')
        index = decision['index']
        if type(index) is not int or not 0 <= index < len(result) or index in seen:
            raise ValueError('Distinct exact assignment indices required')
        seen.add(index)
        if decision['state'] not in ('accepted', 'rejected'):
            raise ValueError('Explicit acceptance or rejection required')
        assignment = result[index]
        reuse = decision.get('reuse_value')
        if reuse is not None:
            if assignment['dimension'] != 'thematic' or decision['state'] != 'accepted' or theme_name(reuse) != reuse:
                raise ValueError('Only an accepted theme can reuse an exact name')
            assignment['value'] = reuse
        assignment['review_state'] = decision['state']
        if decision['state'] == 'accepted':
            assignment.pop('name_candidate', None)
    validate_persisted_assignments(result, evidence_count)
    return result
