"""No HTTP, inference or billing. Only an explicitly labelled snapshot excerpt."""
import json
from app.core.models import GenerationResult,Message,MessageRole


class OfflineSnapshotProvider:
    id='offline'

    async def generate(self,request):
        data=json.loads(request.messages[1].content)
        return GenerationResult(message=Message(role=MessageRole.ASSISTANT,content=json.dumps(dict(
            reference_aliases=[i['reference'] for i in data['snapshot']['items'][:3]],insufficient_context=True))))
