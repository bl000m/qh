"""Focused offline reference-protocol invariants; never calls a provider."""
from copy import deepcopy

import pytest

from app.understanding.passage_refs import FORMAT, PassageReferences
from app.understanding.selected import selected_source
from app.understanding.uum import OUTPUT_SCHEMA, normalize_output
from app.understanding.extractor import canonical_json


def catalogue(text='**Hypothèse** : épargner 100 € 🧭.\r\nExemple de l’assistant, pas une décision.',
        scope='00000000-0000-0000-0000-000000000001'):
    conversation = dict(id='unicode', acquired_at='2026-10-28T10:00:00Z', metadata={},
        turns=[dict(id='assistant-turn', speaker='assistant (unverified dialogue)', text=text)])
    source = selected_source(scope, conversation)
    packet = dict(source_revision_id=source['id'], input_sha256='synthetic-snapshot',
        text=source['content'], turns=source['origin']['turns'])
    return source, packet, PassageReferences(packet, OUTPUT_SCHEMA)


def output(refs):
    return dict(format=FORMAT, items=[dict(text='Proposition non vérifiée de l’assistant, non adoptée.',
        primary_dimension='hypotheses_uncertainties', assignment_certainty='tentative', evidence_refs=refs)])


def test_shared_evidence_is_referenced_without_source_text_in_provider_output():
    source, packet, refs = catalogue()
    frozen = deepcopy(packet)
    disclosure = refs.disclosure()
    assert ''.join(segment['text'] for segment in disclosure['segments']) == source['content']
    assert 'text' not in disclosure
    assert sum(len(s['text']) for s in disclosure['segments']) == len(source['content'])
    assert disclosure['turns'] == source['origin']['turns']
    assert refs.passages == PassageReferences(packet, OUTPUT_SCHEMA).passages
    wire = output(['p001'])
    wire['items'] *= 12
    assert source['content'] not in canonical_json(wire) and 'quote' not in canonical_json(wire)
    assert all('evidence' not in shape['properties'] for shape in refs.schema['properties']['items']['items']['anyOf'])
    expanded = refs.expand(wire)
    assert len(expanded['items']) == 12 and all(i['evidence']==[dict(quote=refs.passages['p001']['quote'])] for i in expanded['items'])
    assert packet == frozen and OUTPUT_SCHEMA['properties']['format']['enum'] == ['qh.atomic-understanding/1']


def test_unicode_offsets_speaker_and_canonical_provenance_are_unchanged():
    source, _, refs = catalogue()
    # Select the second line: the preceding emoji occupies one Unicode code point.
    passage = next((key, p) for key,p in refs.passages.items() if p['quote'].startswith('Exemple'))
    key, original = passage
    normalized = normalize_output(refs.expand(output([key])), source)
    evidence = normalized['items'][0]['evidence'][0]
    assert evidence == dict(source_revision_id=source['id'], quote=original['quote'], start=original['start'], end=original['end'])
    assert source['content'][evidence['start']:evidence['end']] == original['quote']
    turn = source['origin']['turns'][0]
    assert turn['start']<=evidence['start']<evidence['end']<=turn['end']
    assert turn['speaker'] == 'assistant (unverified dialogue)'
    assert normalized['items'][0]['primary_dimension']['review_state'] == 'proposed'
    assert 'non vérifiée' in normalized['items'][0]['text']
    foreign_source, _, other = catalogue('Autre contenu indépendant.', '00000000-0000-0000-0000-000000000002')
    assert foreign_source['id'] != source['id']
    assert other.expand(output(['p001']))['items'][0]['evidence'][0]['quote'] == 'Autre contenu indépendant.'
    assert refs.expand(output(['p001']))['items'][0]['evidence'][0]['quote'] != 'Autre contenu indépendant.'
    assert evidence['source_revision_id'] == source['id']  # A same-shaped label never resolves via another request.


@pytest.mark.parametrize('invalid', ['unknown', 'empty', 'type', 'duplicate', 'fabricated', 'foreign', 'legacy'])
def test_invalid_or_foreign_reference_output_is_rejected_without_repair(invalid):
    _, _, refs = catalogue()
    wire = output(['p001'])
    item = wire['items'][0]
    if invalid == 'unknown': item['evidence_refs'] = ['p999999']
    elif invalid == 'empty': item['evidence_refs'] = []
    elif invalid == 'type': item['evidence_refs'] = [dict(ref='p001')]
    elif invalid == 'duplicate': item['evidence_refs'] *= 2
    elif invalid == 'fabricated': item['evidence'] = [dict(quote='invented')]
    elif invalid == 'foreign': item['source_revision_id'] = 'another-source'
    else: wire['format'] = 'qh.atomic-understanding/1'
    frozen = deepcopy(wire)
    with pytest.raises(ValueError): refs.expand(wire)
    assert wire == frozen


def test_ambiguous_original_passages_are_not_addressable():
    _, _, refs = catalogue('Même ligne\nMême ligne\nPassage unique.')
    assert 'Même ligne' not in {p['quote'] for p in refs.passages.values()}
    _, packet, _ = catalogue('Même ligne')
    text = packet['text']
    packet['text'] += text
    turn = packet['turns'][0]
    packet['turns'].append(dict(turn, turn_id='another-turn', start=turn['start']+len(text), end=turn['end']+len(text)))
    with pytest.raises(ValueError, match='No unique original quotation'):
        PassageReferences(packet, OUTPUT_SCHEMA)
