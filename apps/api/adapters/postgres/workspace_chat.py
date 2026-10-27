"""Append-only attempt receipts in existing intake JSON; never semantic source input."""
import asyncio
from uuid import UUID, uuid5

from app.understanding.enrichment import EnrichmentConflict


class WorkspaceChatStorage:
    def _chat_states(self, c, scope):
        rows = c.execute("""SELECT DISTINCT ON (document->>'question_id') document FROM context_intake
            WHERE context_space_id=%s AND document->>'kind'='chat_attempt'
            ORDER BY document->>'question_id',created_at DESC,id DESC""", (scope,)).fetchall()
        return [{k:r['document'][k] for k in ('question_id','operation_id','state')} for r in rows]

    def _chat_event(self, c, scope, question, operation, state):
        document = dict(kind='chat_attempt',question_id=question,operation_id=operation,state=state)
        self._immutable(c, 'context_intake', dict(id=str(uuid5(UUID(operation), state)),
            context_space_id=scope, document=document))

    def _chat_operation(self, scope, question, operation, answer):
        with self.connect() as c:
            self._authorize(c, (scope,), lock=True)
            c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))', ('qh-context:'+scope,))
            state = self._read(c, scope)
            if not any(r['id']==question and r['kind']=='message' and r['role']=='user' for r in state['intake']):
                raise ValueError('Persisted question required')
            done = next((r for r in state['intake'] if r.get('reply_to')==question), None)
            if done:
                return dict(completed=True, **state)
            previous = next((r for r in state['chat_attempts'] if r['question_id']==question), None)
            if answer is None:
                if len(state['intake'])>=500:
                    raise ValueError('Context intake exceeds supported limit')
                used = c.execute('SELECT 1 FROM context_intake WHERE id=%s AND context_space_id=%s',
                    (str(uuid5(UUID(operation), 'running')),scope)).fetchone()
                if used or previous and previous['state']=='running':
                    raise EnrichmentConflict('Attempt already submitted; synchronize its state')
                self._chat_event(c, scope, question, operation, 'running')
                return state
            if not previous or previous['operation_id']!=operation or previous['state']!='running':
                raise EnrichmentConflict('Attempt changed')
            if answer is not False:
                self._append_on(c, scope, dict(id=str(uuid5(UUID(question), 'answer')), **answer))
            self._chat_event(c, scope, question, operation, 'completed' if answer is not False else 'failed')
            return self._read(c, scope)

    async def claim_chat(self, scope, question, operation):
        return await asyncio.to_thread(self._chat_operation, scope, question, operation, None)

    async def finish_chat(self, scope, question, operation, answer=False):
        return await asyncio.to_thread(self._chat_operation, scope, question, operation, answer)
