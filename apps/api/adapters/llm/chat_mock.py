"""Deterministic extractive demonstration, NOT LLM comprehension; no network."""
import json

from app.core.models import GenerationResult, Message, MessageRole
from app.chat.serialization import expand_context


class MockChatProvider:
    async def generate(self, request):
        context = json.loads(request.messages[1].content)
        rows, excerpts = [], []
        for row in expand_context(context):
            text = row['content'].get('text')
            if not isinstance(text, str) or not text.strip():
                continue
            label = '[Proposé, non confirmé] ' if row['validation_state'] == 'proposed' else '[Confirmé courant] '
            if sum(len(t) for t in excerpts) + len(label) + len(text) > 2800:
                continue
            rows.append(row)
            excerpts.append(label + text)
            if len(rows) == 3:
                break
        answer = 'Mode mock : extraits conservés, sans analyse de votre question.\n' + '\n'.join(excerpts)
        if not rows:
            answer = 'Le contexte disponible est insuffisant pour répondre.'
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps({
            'answer': answer, 'revision_ids': [r['revision_id'] for r in rows],
            'insufficient_context': not bool(rows),
        }, ensure_ascii=False)))
