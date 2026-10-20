"""Selected-source intake; the frozen QH-8 extractor remains the ONLY validator.

A request-local buffer exposes the prepared original source to the existing Engine
without committing it first. Engine extract/publish run unchanged. Only the outer
application's CanonicalRepository transaction makes source + proposals durable.
This is no persistent staging model or second interpretation/validation engine.
"""
from copy import deepcopy
from dataclasses import replace
from uuid import UUID, uuid5

from app.core.models import Message, MessageRole
from app.understanding.citations import resolve_output_citations
from app.understanding.extractor import UnderstandingExtractor, canonical_json, decode_output, MAX_JSON


class _EmptyResult(ValueError):
    pass


class _PreparedSource:
    def __init__(self, subject, source):
        self.subject_id, self.source = str(subject), source
        self.revisions = ()

    def read_sources(self, scopes, refs):
        if tuple(map(str, scopes)) != (self.source['context_space_id'],) or tuple(map(str, refs)) != (self.source['id'],):
            raise PermissionError('Only the exact prepared source is available')
        return [deepcopy(self.source)]

    def save(self, *, sources=(), revisions=()):
        if sources:
            raise ValueError('The prepared source is immutable; no persistent writes')
        self.revisions = tuple(deepcopy(revisions))


def selected_source(context_id, conversation):
    """Intake serialization of an already validated owner-selected segment.

    Unlike the historical QH-8 fixture import, a selection can be one turn. It
    keeps the established source identity/text/turn-locator representation, without
    inventing extra turns to satisfy that old importer or mutating its sealed file.
    """
    chunks, turns, offset = [], [], 0
    for turn in conversation['turns']:
        prefix = turn['speaker'] + ': '
        chunk = prefix + turn['text'] + '\n'
        turns.append(dict(turn_id=turn['id'],speaker=turn['speaker'],
            start=offset+len(prefix),end=offset+len(prefix)+len(turn['text'])))
        chunks.append(chunk); offset += len(chunk)
    source_id = str(uuid5(UUID(str(context_id)), 'conversation:'+conversation['id']))
    source = dict(id=str(uuid5(UUID(source_id),'revision:1')), source_id=source_id,
        context_space_id=str(context_id), revision_no=1, content=''.join(chunks),
        origin=dict(kind='conversation',conversation_id=conversation['id'],
            acquired_at=conversation['acquired_at'],turns=turns,metadata=deepcopy(conversation['metadata'])))
    if len(canonical_json(source).encode()) > MAX_JSON:
        raise ValueError('Selected source too large')
    return source


async def propose_selected_conversation(*, subject_id, context_id, conversation, extraction_key, policy, provider):
    source = selected_source(context_id, conversation)
    buffer = _PreparedSource(subject_id, source)

    class ResolvedProvider:
        async def generate(self, request):
            # Original Engine authorizes and constructs this exact source request.
            result = await provider.generate(request)
            if result.message.role != MessageRole.ASSISTANT:
                return result  # The unchanged Engine rejects the role.
            output = decode_output(result.message.content)
            if output == {'items': []}:
                raise _EmptyResult('Explicit successful empty extraction')
            derived, _audit = resolve_output_citations(output, source=source)
            return replace(result, message=Message(role=MessageRole.ASSISTANT,
                content=canonical_json(derived)))

    engine = UnderstandingExtractor(repository=buffer, policy=policy, provider=ResolvedProvider())
    try:
        checkpoint = await engine.extract(subject_id=subject_id,context_id=context_id,
            source_revision_id=source['id'],extraction_key=extraction_key)
    except _EmptyResult:
        return source, ()
    # Same fingerprint/source/policy/whole-batch revalidation as canonical replay;
    # this publish only fills the private request buffer, never SQL or the graph.
    await engine.publish(subject_id=subject_id, checkpoint=checkpoint)
    return source, buffer.revisions
