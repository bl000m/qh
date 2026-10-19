"""Explicit offline demo adapters for the existing LLMProvider port; no network.

Fixture generation is scripted, not semantic inference. Replay returns a captured
response only for the identical request. Neither adapter is installed at startup.
"""

from copy import deepcopy
import hashlib
import json

from app.core.models import GenerationResult, Message, MessageRole


def request_hash(request):
    payload = [(m.role.value, m.content) for m in request.messages]
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


class FixtureUnderstandingProvider:
    """Materialize hand-authored proposals/citations for known synthetic turns."""

    def __init__(self, items):
        self.items = deepcopy(items)
        self.calls = 0
        self.last_request = None
        self.last_result = None

    async def generate(self, request):
        self.calls += 1
        self.last_request = request
        source = json.loads(request.messages[-1].content)
        items = deepcopy(self.items)
        for item in items:
            for ref in item["evidence"]:
                turn_id = ref.pop("turn_id")
                turn = next(t for t in source["turns"] if t["turn_id"] == turn_id)
                quote = ref["quote"]
                # Find only inside the recorded turn, never across unrelated text.
                start = source["text"].index(quote, turn["start"], turn["end"])
                ref.update(
                    source_revision_id=source["source_revision_id"],
                    start=start,
                    end=start + len(quote),
                )
        self.last_result = GenerationResult(
            message=Message(
                role=MessageRole.ASSISTANT,
                content=json.dumps({"items": items}, ensure_ascii=False),
            )
        )
        return self.last_result


class ReplayLLMProvider:
    """Exact capture replay, independent of fixture interpretation/rendering."""

    def __init__(self, *, expected_request_sha256, response_json):
        self.expected_request_sha256 = expected_request_sha256
        self.response_json = response_json
        self.calls = 0

    async def generate(self, request):
        self.calls += 1
        if request_hash(request) != self.expected_request_sha256:
            raise ValueError("Replay request fingerprint mismatch")
        return GenerationResult(
            message=Message(role=MessageRole.ASSISTANT, content=self.response_json)
        )


class LiteralSegmentProvider:
    """Honest no-network control: copy selected user turns, no semantic inference.

    Assistant turns may be preserved as explicitly selected source context, but
    never become human claims or automatic proposals in this demonstration mode.
    This is an LLMProvider substitute, not a new extraction/validation engine.
    """
    async def generate(self, request):
        source = json.loads(request.messages[-1].content)
        items = []
        for turn in source['turns']:
            if turn['speaker'] != 'user (owner-declared)':
                continue
            quote = source['text'][turn['start']:turn['end']]
            items.append(dict(local_id=turn['turn_id'], shape='item', text=quote,
                properties={'basis': 'literal owner-submitted utterance; no semantic inference'},
                evidence=[dict(source_revision_id=source['source_revision_id'],
                    start=turn['start'], end=turn['end'], quote=quote)]))
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,
            content=json.dumps({'items': items}, ensure_ascii=False)))
