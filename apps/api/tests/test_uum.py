"""Approved UUM contract, with synthetic explicit judgments; no provider calls."""
from copy import deepcopy
import pytest

from app.core.uum import PRIMARY_DIMENSIONS, validate_primary, review_primary
from app.understanding.uum import FORMAT, normalize_output
from app.understanding.citations import CitationResolutionError
from adapters.postgres.semantic_profiles import generic_definitions, semantic_definitions, uum_definitions


def test_profile_is_additive_single_primary_and_structural_kinds_stay_independent():
    old = deepcopy((generic_definitions(), semantic_definitions()))
    profiles = uum_definitions()
    assert (generic_definitions(), semantic_definitions()) == old
    assert {p['structural_kind'] for p in profiles} == {'item', 'entity', 'relation'}
    for p in profiles:
        assert p['version'] == 3
        schema = p['property_schema']
        assert 'primary_dimension' not in schema['required']
        assert schema['properties']['primary_dimension']['properties']['value']['enum'] == list(PRIMARY_DIMENSIONS)


@pytest.mark.parametrize('dimension', PRIMARY_DIMENSIONS)
def test_assignment_is_independent_from_truth_and_item_confirmation(dimension):
    p = dict(value=dimension, certainty='asserted', evidence_refs=[0], review_state='proposed')
    content = dict(text='Uncertain reported proposition', citations=[{}], primary_dimension=p)
    assert validate_primary(p, 1) == p
    assert review_primary(content, {'state': 'accepted'}) == dict(p, review_state='accepted')
    assert review_primary(content, {'state': 'rejected'}) == dict(p, review_state='rejected')
    assert content['primary_dimension'] == p


@pytest.mark.parametrize('refs', [[], [True], [-1], [1], [0, 0], '0'])
def test_bad_evidence_is_not_repaired(refs):
    with pytest.raises(ValueError):
        validate_primary(dict(value=PRIMARY_DIMENSIONS[0], certainty='tentative', evidence_refs=refs, review_state='proposed'), 1)


def source(text='Exact quote.'):
    return dict(id='trusted-source', content=text, origin={'turns': [dict(turn_id='trusted-turn', start=0, end=len(text))]})


def wire(text='Exact quote.', primary='situation_information'):
    item = dict(text=text, primary_dimension=primary, evidence=[{'quote': text}])
    if primary is not None:
        item['assignment_certainty'] = 'tentative'
    return dict(format=FORMAT, items=[item])


def test_wire_has_no_model_generated_ids_indices_offsets_or_human_state():
    raw = wire(); frozen = deepcopy(raw)
    result = normalize_output(raw, source())['items'][0]
    assert raw == frozen
    assert result['local_id'] == '0' and result['shape'] == 'item'
    assert result['primary_dimension']['evidence_refs'] == [0]
    assert result['primary_dimension']['review_state'] == 'proposed'
    assert result['evidence'] == [dict(source_revision_id='trusted-source', quote='Exact quote.', start=0, end=12)]
    assert 'primary_dimension' not in normalize_output(wire(primary=None), source())['items'][0]
    assert normalize_output(dict(format=FORMAT, items=[]), source()) == {'items': []}


@pytest.mark.parametrize('field', ['local_id', 'shape', 'review_state', 'evidence_refs', 'owner', 'properties'])
def test_extra_model_authority_is_rejected(field):
    raw = wire(); raw['items'][0][field] = 'untrusted'
    with pytest.raises(ValueError): normalize_output(raw, source())


@pytest.mark.parametrize('text', ['Exact quote. Exact quote.', 'Something else.'])
def test_ambiguous_or_missing_quote_fails_closed(text):
    with pytest.raises(CitationResolutionError): normalize_output(wire(), source(text))


def test_unclassified_cannot_silently_hide_an_unknown_enum():
    raw = wire(primary='sleep')
    with pytest.raises(ValueError): normalize_output(raw, source())
    raw = wire(primary=None); raw['items'][0]['assignment_certainty'] = 'asserted'
    with pytest.raises(ValueError): normalize_output(raw, source())


def test_unicode_exact_span_without_normalization():
    text = 'Énergie 🧭 : je préfère rester.'
    assert normalize_output(wire(text, 'constraints_preferences'), source(text))['items'][0]['evidence'][0]['end'] == len(text)
