"""Version-bound presentation metadata; detailed UUM statements remain authoritative."""
from copy import deepcopy

from app.understanding.extractor import decode_output, digest, nonempty, object_fields

FORMAT = 'qh.context-consolidation/1'
PRESENTATION_VERSION = 2
RECAP_SCHEMA = dict(type='object', additionalProperties=False,
    required=['title', 'text', 'supporting_statements'], properties=dict(
        title=dict(type='string', minLength=1, maxLength=120,
            description='Short subject title in the main language of the original memorized content.'),
        text=dict(type='string', minLength=1, maxLength=1500,
            description='Autonomous subject/knowledge overview in the original content language, at most 100 words; no dialogue narration.'),
        supporting_statements=dict(type='array', minItems=1, maxItems=100,
            description='Exact copies of understanding.items[].text supporting this recap; never evidence[].quote or source quotations.',
            items=dict(type='string', minLength=1, maxLength=16000,
                description='Copy one complete understanding.items[].text verbatim, not its evidence quote.'))))
INSTRUCTIONS = '''
The atomic instructions above apply ONLY inside understanding.
Return the strict qh.context-consolidation/1 envelope with understanding containing
all detailed qh.atomic-understanding/1 items, and recap containing title, text and
supporting_statements. Keep the full useful detailed knowledge: quantities,
ingredients, steps, variants, constraints and uncertainties when present. The
100-word maximum applies ONLY to recap.text, never to understanding.items.
The recap is a short semantic overview for a newcomer, not the detailed content:
state the main subjects, what this context contains and what it helps understand.
Write BOTH recap.title and recap.text in the main language of the ORIGINAL
memorized content, not the language of these instructions or schema. Keep detailed
item.text in that original language too; evidence always remains verbatim.
Usually 40-80 words suffice; at most 100 words. Shorter is fine: no minimum length.
Describe the SUBJECT and reusable KNOWLEDGE directly, as an autonomous overview.
Never narrate the exchange: no "The user requests", "The assistant responds",
"L’utente chiede" or chronology of messages. Prefer a short subject title and
"Questo contesto raccoglie..." for Italian content. For example:
title="Organizzazione di un laboratorio informatico";
text="Linee guida per progettare e condurre un laboratorio informatico: obiettivi,
materiali, attività pratiche, strumenti digitali e valutazione. Il contesto include
una proposta in 30 passaggi, consigli didattici e attività di follow-up."
Mention proposals, hypotheticals and attribution when omitting them would change
the meaning; a proposed workshop is not an adopted or completed workshop.
No fixed taxonomy, empty sections or full procedure in the recap. Combine
complementary information and avoid repetition. Use only knowledge represented
in understanding. Keep complete ordered steps, tools and activities in item.text,
not merely in evidence quotes: a short recap never licenses dropping details.
Build understanding.items first, then write recap. For supporting_statements,
copy the COMPLETE exact value of understanding.items[i].text for each item used
in the recap. Do NOT copy understanding.items[i].evidence[j].quote: evidence quotes
are original source words, whereas item.text is the synthesized statement.
Do not paraphrase, shorten, translate or add Markdown to the copied item.text.
Example: if an item has text="The assistant suggests Carnaroli rice." and
 evidence=[{"quote":"Try **Carnaroli** rice."}], its supporting_statements entry
must be "The assistant suggests Carnaroli rice.", NEVER "Try **Carnaroli** rice.".
Before returning, check that every supporting_statements string equals exactly
one understanding.items[].text and that no supporting string is repeated.
These are support declarations, not new facts, IDs or fabricated citations.
If no useful understanding is supported, return empty items and recap=null.
'''


def schema(atomic_schema):
    return dict(type='object', additionalProperties=False,
        required=['format', 'understanding', 'recap'], properties=dict(
            format=dict(type='string', enum=[FORMAT]), understanding=deepcopy(atomic_schema),
            recap=dict(anyOf=[deepcopy(RECAP_SCHEMA), dict(type='null')])))


def decode(text):
    output = decode_output(text)
    object_fields(output, ('format', 'understanding', 'recap'))
    if output['format'] != FORMAT:
        raise ValueError('Explicit consolidation format required')
    atomic, recap = output['understanding'], output['recap']
    object_fields(atomic, ('format', 'items'))
    if not isinstance(atomic['items'], list):
        raise ValueError('Detailed understanding required')
    if not atomic['items'] and recap is None:
        return atomic, None
    object_fields(recap, ('title', 'text', 'supporting_statements'))
    title, summary = nonempty(recap['title']), nonempty(recap['text'])
    if not title.strip() or len(title)>120 or not summary.strip() or len(summary)>1500 or len(summary.split())>100 or '\0' in title+summary:
        raise ValueError('Bounded nonempty recap required')
    support = recap['supporting_statements']
    texts = [i.get('text') for i in atomic['items'] if isinstance(i, dict)]
    if (not isinstance(support, list) or not 1<=len(support)<=100
        or any(not isinstance(t, str) or texts.count(t)!=1 for t in support)
        or len(set(support))!=len(support)):
        raise ValueError('Exact unambiguous detailed recap support required')
    return atomic, dict(title=title, text=summary, supporting_statements=support,
        provider_output_sha256=digest(output))


def bind(recap, revisions, version_id):
    if recap is None:
        raise ValueError('A successful consolidation requires its recap')
    rows = deepcopy(revisions)
    support = [r['id'] for text in recap['supporting_statements'] for r in rows if r['content']['text']==text]
    if len(support)!=len(recap['supporting_statements']):
        raise ValueError('Recap support changed during canonical validation')
    rows[0]['content']['extraction']['recap'] = dict(format='qh.context-recap/1',
        version_id=version_id, presentation_version=PRESENTATION_VERSION, title=recap['title'], text=recap['text'],
        basis_revision_ids=[r['id'] for r in rows], support_revision_ids=support,
        provider_output_sha256=recap['provider_output_sha256'])
    return rows


def from_version(rows, current):
    if not current:
        return None
    for row in rows:
        recap = row['content'].get('extraction', {}).get('recap')
        if not recap:
            continue
        if (recap.get('format')!='qh.context-recap/1' or recap.get('version_id')!=current['id']
            or set(recap.get('basis_revision_ids', []))!=set(current['revision_ids'])
            or not recap.get('support_revision_ids')
            or not set(recap['support_revision_ids'])<=set(current['revision_ids'])):
            raise ValueError('Recap must belong to this exact consolidated version')
        return {k:recap[k] for k in ('version_id', 'title', 'text', 'support_revision_ids')}
    return None
