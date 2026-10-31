"""Deterministic extractive demonstration, NOT LLM comprehension; no network."""
import json

from app.core.models import GenerationResult, Message, MessageRole
from app.chat.references import expand_model_context


class MockChatProvider:
    async def generate(self, request):
        context = json.loads(request.messages[1].content)
        rows, excerpts = [], []
        for row in expand_model_context(context, max_revisions=100):
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
        aliases = {ref: alias for alias, ref in context['allowed_reference_aliases'].items()}
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT, content=json.dumps({
            'answer': answer, 'reference_aliases': [aliases[r['revision_id']] for r in rows],
            'insufficient_context': not bool(rows), 'support_basis': 'canonical' if rows else 'insufficient',
        }, ensure_ascii=False)))
