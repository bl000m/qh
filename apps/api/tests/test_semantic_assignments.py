"""Semantic contract checks use explicit proposals, no model/network or classifier."""
import asyncio
from copy import deepcopy
import json
from unittest.mock import AsyncMock

import pytest

from app.core.models import GenerationRequest, GenerationResult, Message, MessageRole
from app.core.assignments import qualified_assignments, theme_name
from app.understanding.semantic import SemanticExtractionProvider


def assignment(value='Sommeil', **changes):
    return dict(dimension='thematic', value=value, certainty='tentative', evidence_refs=[0], **changes)


def test_dimension_multi_membership_evidence_and_normalization_are_independent():
    values=[assignment('  Sommeil  et\trepos '),assignment('Activité physique'),
        dict(assignment('decision'),dimension='semantic_role'),assignment('decision')]
    result=qualified_assignments(values,1)
    assert [d['value'] for d in result]==['Sommeil et repos','Activité physique','decision','decision']
    assert len(result)==4 and all(d['certainty']=='tentative' for d in result)
    assert qualified_assignments([values[0],deepcopy(values[0])],1)==[result[0]]
    assert theme_name('e\u0301nergie')=='énergie' and theme_name('Sommeil')!=theme_name('sommeil')


@pytest.mark.parametrize('changes',[
    {'dimension':'decision'},{'certainty':'confirmed'},{'evidence_refs':[]},
    {'evidence_refs':[True]},{'evidence_refs':[-1]},{'evidence_refs':[1]},
    {'evidence_refs':[0,0]},{'value':' '},{'value':'a\0b'},{'review_state':'accepted'},
])
def test_invalid_or_provider_approved_assignments_fail_whole_validation(changes):
    value=assignment();value.update(changes)
    with pytest.raises(ValueError):qualified_assignments([assignment('Valid sibling'),value],1)


def test_discordant_duplicates_never_silently_override_certainty():
    value=assignment();other=dict(value,certainty='asserted')
    with pytest.raises(ValueError):qualified_assignments([value,other],1)
    with pytest.raises(ValueError):qualified_assignments([{'value':'decision','certainty':'asserted'}],1)


def test_semantic_adapter_sends_only_exact_source_and_explicit_bounded_vocabulary_once():
    response=GenerationResult(message=Message(role=MessageRole.ASSISTANT,content='{"items":[]}'))
    delegate=type('Provider',(),{'generate':AsyncMock(return_value=response)})()
    provider=SemanticExtractionProvider(delegate,known_themes=('Sommeil','Activité physique'))
    source=dict(source_revision_id='exact-source',input_sha256='exact-hash',text='Original text',turns=[])
    request=GenerationRequest(messages=(Message(role=MessageRole.SYSTEM,content='legacy'),Message(role=MessageRole.USER,content=json.dumps(source))))
    assert asyncio.run(provider.generate(request))==response
    assert delegate.generate.await_count==1
    disclosed=json.loads(delegate.generate.call_args.args[0].messages[-1].content)
    assert disclosed==dict(source,descriptor_version=2,known_themes=['Sommeil','Activité physique'],vocabulary_coverage='partial')
    source['other_space']='not allowed';request=GenerationRequest(messages=(request.messages[0],Message(role=MessageRole.USER,content=json.dumps(source))))
    with pytest.raises(ValueError):asyncio.run(provider.generate(request))
    assert delegate.generate.await_count==1
