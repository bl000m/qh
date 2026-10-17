"""Deterministic extractive demonstration, NOT LLM comprehension; no network."""
import json

from app.core.models import GenerationResult, Message, MessageRole


class MockChatProvider:
    async def generate(self, request):
        context = json.loads(request.messages[1].content)
        rows = [r for r in context['revisions'] if isinstance(r['content'].get('text'), str)
                and r['content']['text'].strip()][:3]
        answer = 'Mode mock : extraits conservés, sans analyse de votre question.\n' + '\n'.join(
            ('[Proposé, non confirmé] ' if r['validation_state'] == 'proposed' else '[Confirmé courant] ')
            + r['content']['text'][:600] for r in rows)
        if not rows:
            answer = 'Le contexte disponible est insuffisant pour répondre.'
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps({
            'answer': answer, 'revision_ids': [r['revision_id'] for r in rows],
            'insufficient_context': not bool(rows),
        }, ensure_ascii=False)))
