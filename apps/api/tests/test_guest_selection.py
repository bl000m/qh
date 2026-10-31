"""Offline selection/composition replay; no paid calls, no PDF extraction."""
from copy import deepcopy
import json

import pytest

from app.chat.snapshot_answer import SnapshotAnswerError
from app.chat.selection import decode_selection, decode_composition, selection_request, composition_request, date_catalog, requested_order
from app.core.models import Message, MessageRole


def benchmark_payload(both=True):
    texts=[
        ('Projet de formation en Rust envisagé sans inscription encore décidée.',0,[10]),
        ("Proposition de contrat non signé pour le poste d'ingénieur logiciel chez Helios, avec un début envisagé au 1er mars 2027.",1,[1,3]),
        ('Prime de mobilité proposée de 900 euros, conditionnée à la présentation de justificatifs de déménagement.',1,[6]),
        ('Rémunération proposée : 54 000 euros bruts par an.',1,[4]),
        ('Expérience précédente comme coordinateur data/digital chez Amarante de juin 2018 à décembre 2021, incluant la migration CRM vers Sendinblue et des analyses SQL.',0,[6,7]),
        ('Expérience professionnelle actuelle : ingénieur de recherche chez Orbite depuis septembre 2023, incluant le projet Atlas, le déploiement de Matomo et le monitoring avec Prometheus.',0,[2,3]),
        ("Formation en cours à l'École 42 en architecture des systèmes de 2022 à 2024, présentée comme une formation et non un emploi.",0,[9]),
        ('Statut du contrat : projet non signé, sans valeur contractuelle effective.',1,[2]),
        ('Temps de travail proposé : 35 heures par semaine avec deux jours de télétravail par semaine.',1,[5]),
        ("Expérience précédente en freelance comme développeur full-stack de janvier 2022 à août 2023 pour l'association Nova, sur le projet Lumen (portail Ruby on Rails et PostgreSQL).",0,[4,5])]
    from pathlib import Path
    corpus=json.loads((Path(__file__).resolve().parents[3]/'docs/evidence/pdf-fidelity-20261030/corpus.json').read_text())
    items=[dict(reference=f'R{index+1}',text=text,citations=[dict(quote=corpus['documents'][doc]['lines'][line]) for line in lines])
        for index,(text,doc,lines) in enumerate(texts) if both or doc==0]
    recap=(dict(title='Expérience professionnelle et proposition de contrat pour Alex Martin',
        text="Ce contexte présente le parcours professionnel d'Alex Martin, incluant ses expériences en ingénierie, freelance et coordination data, ainsi qu'une proposition de contrat non signé chez Helios avec ses conditions.") if both else
        dict(title="Expérience professionnelle d'Alex Martin",text='Expériences professionnelles déclarées : ingénieur de recherche chez Orbite (depuis septembre 2023), développeur full-stack en freelance pour Nova (janvier 2022 à août 2023), et coordinateur data/digital chez Amarante (juin 2018 à décembre 2021).'))
    return dict(format='qh.disclosure/1',name='Synthetic reference',items=items,recap=recap)


def plan(payload,refs,*,operation='answer',limit=0):
    rows={item['reference']:dict(subject_type='Requested type',matches_subject=item['reference'] in refs,
        matches_conditions=True) for item in payload['items']}
    return dict(requested_subject='Requested subject',assessments=rows)


def message(value):return Message(role=MessageRole.ASSISTANT,content=json.dumps(value))


@pytest.mark.parametrize('both',[False,True])
@pytest.mark.parametrize('reverse',[False,True])
def test_explicit_order_is_server_controlled_before_composition(both,reverse):
    payload=benchmark_payload(both)
    if reverse:payload['items'].reverse()
    frozen=deepcopy(payload)
    value=plan(payload,{'R5','R6','R10'},operation='enumerate',limit=2)
    result=decode_selection(message(value),payload,'Quali sono le ultime due esperienze?')
    assert result['groups']==[['R6'],['R10']] and payload==frozen
    request=composition_request(payload,'Ultime due?',result['groups'],language='it')
    packet=json.loads(request.messages[1].content)
    assert {i['reference'] for i in packet['snapshot']['items']}=={'R6','R10'}
    assert 'recap' not in packet['snapshot'] and 'Helios' not in str(packet) and 'Rust' not in str(packet)
    response=message(dict(sections=dict(subject_1='Orbite: ricerca dal settembre 2023.',subject_2='Nova: freelance gennaio 2022–agosto 2023.'),insufficient_context=False))
    assert decode_composition(response,payload,result['groups'])['referents']==[['R6'],['R10']]


def test_project_decisions_use_the_same_literal_dates_and_order():
    payload=dict(items=[dict(reference='R1',text='Le 10 février 2026, Atlas est adopté.'),dict(reference='R2',text='Le 15 avril 2026, Lumen est adopté.'),
        dict(reference='R3',text='Le 9 mai 2026, Neptune est proposé sans adoption.'),dict(reference='R4',text='Le 21 janvier 2026, Iris est adopté.')])
    value=plan(payload,{'R1','R2','R4'},operation='enumerate',limit=2)
    assert decode_selection(message(value),payload,'Ultime due decisioni adottate?')['groups']==[['R2'],['R1']]


@pytest.mark.parametrize('question,expected',[
    ('Le ultime due esperienze?',('latest',2)),('Les deux dernières décisions ?',('latest',2)),
    ('The last two versions?',('latest',2)),('The three earliest events?',('earliest',3)),
    ('Le prime 4 attività?',('earliest',4)),('Confronta le versioni.',None),('E prima?',None)])
def test_order_detection_is_generic_and_subject_independent(question,expected):
    assert requested_order(question)==expected


@pytest.mark.parametrize('failure',['omitted','outside','invalid-boolean'])
def test_selection_rejects_incomplete_or_unauthorized_assessments(failure):
    payload=benchmark_payload();value=plan(payload,{'R6','R10'})
    if failure=='omitted':value['assessments'].pop('R10')
    if failure=='outside':value['assessments']['OUTSIDE']=value['assessments'].pop('R10')
    if failure=='invalid-boolean':value['assessments']['R10']['matches_subject']='true'
    with pytest.raises(ValueError):decode_selection(message(value),payload)


def test_unknown_or_overlapping_dates_cannot_invent_order():
    for text in ('Alpha sans période.','Alpha en 2023.'):
        payload=dict(items=[dict(reference='R1',text=text),dict(reference='R2',text='Beta en 2023.')])
        result=decode_selection(message(plan(payload,{'R1','R2'})),payload,'The last one event?')
        assert result['groups']==[] and result['ordering_unknown']


def test_catalog_preserves_exact_proofs_precision_and_deduplicated_quotes():
    item=dict(text='Décision.',citations=[dict(quote='Adoption en septembre 2023.'),dict(quote='Adoption en septembre 2023.'),dict(quote='Fin le 2026-04-02.')])
    dates=date_catalog(item)
    assert [entry['value'] for entry in dates.values()]==['2023-09','2026-04-02']
    assert dates['D1']==dict(value='2023-09',quote='septembre 2023',evidence=1)
    assert dates['D2']['evidence']==2
    assert not any(entry['value']=='2023-09-01' for entry in dates.values())


def test_numeric_identifiers_and_amounts_are_not_temporal_evidence():
    dates=date_catalog(dict(text='Version V2024.7, build 9000, publiée le 2026-04-02. Coût : 2027 euros. Budget : 2021–2022 euros.'))
    assert [entry['value'] for entry in dates.values()]==['2026-04-02']


def test_composition_slots_cannot_drop_evidence_or_add_subjects():
    payload=benchmark_payload();groups=[['R6'],['R10']]
    for sections in (dict(subject_1='Only Orbite.'),dict(subject_1='Orbite.',subject_2='Nova.',subject_3='Rust.')):
        with pytest.raises(SnapshotAnswerError,match='guest.invalid_composition'):
            decode_composition(message(dict(sections=sections,insufficient_context=False)),payload,groups)
    with pytest.raises(SnapshotAnswerError,match='guest.internal_structure_in_answer'):
        decode_composition(message(dict(sections=dict(subject_1='R6',subject_2='Nova.'),insufficient_context=False)),payload,groups)


def test_activity_links_and_contract_conditions_survive_composition():
    payload=benchmark_payload();groups=[['R6'],['R10'],['R5']];items={i['reference']:i for i in payload['items']}
    sections={f'subject_{n+1}':items[group[0]]['text'] for n,group in enumerate(groups)}
    result=decode_composition(message(dict(sections=sections,insufficient_context=False)),payload,groups)
    assert 'Matomo' in result['answer'].splitlines()[0] and 'Rails' in result['answer'].splitlines()[1] and 'Sendinblue' in result['answer'].splitlines()[2]
    packet=json.loads(composition_request(payload,'Condizioni?', [['R2','R3','R4','R8','R9']],language='it').messages[1].content)
    assert 'Rust' not in str(packet)
    assert any('CDI' in quote for item in packet['snapshot']['items'] for quote in item.get('evidence_quotes',[]))
    assert any('Neptune' in quote for item in packet['snapshot']['items'] for quote in item.get('evidence_quotes',[]))


def test_schema_requires_complete_assessment_and_authorized_date_ids():
    payload=benchmark_payload();request=selection_request(payload,'Esperienze?',history=[dict(role='user',content='EXCLUDED'),dict(role='assistant',content='999999')])
    rows=request.output_schema['properties']['assessments']
    assert set(rows['required'])=={i['reference'] for i in payload['items']}
    assert set(rows['properties']['R6']['properties'])=={'subject_type','matches_subject','matches_conditions'}
    assert 'EXCLUDED' not in request.messages[1].content and '999999' not in request.messages[1].content


def test_conversation_context_is_reference_only_and_keeps_current_authority():
    from app.chat.selection import REFERENCE_PROMPT
    payload=benchmark_payload()
    request=selection_request(payload,'E prima?',conversation=[[['R6'],['R10']]])
    packet=json.loads(request.messages[1].content)
    assert packet['conversation_references']==[[['R6'],['R10']]]
    assert REFERENCE_PROMPT in request.messages[0].content and 'history' not in packet


def test_empty_selection_does_not_create_composition_subject():
    payload=benchmark_payload(False)
    assert decode_selection(message(plan(payload,set())),payload)['groups']==[]


def test_large_pool_is_not_truncated_to_reference_memory_bound():
    payload=dict(items=[dict(reference=f'R{i}',text=f'Événement en {2010+i}.') for i in range(1,10)])
    result=decode_selection(message(plan(payload,{i['reference'] for i in payload['items']})),payload,'The last two events?')
    assert result['groups']==[['R9'],['R8']]
