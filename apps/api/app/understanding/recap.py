"""Version-bound presentation metadata; detailed UUM statements remain authoritative."""
from copy import deepcopy

from app.understanding.extractor import decode_output, digest, nonempty, object_fields

FORMAT = 'qh.context-consolidation/1'
PRESENTATION_VERSION = 3
COMPATIBLE_VERSIONS = (2, PRESENTATION_VERSION)
RECAP_SCHEMA = dict(type='object', additionalProperties=False,
    required=['title', 'text', 'supporting_statements'], properties=dict(
        title=dict(type='string', minLength=1, maxLength=120,
            description='Short subject title in the main language of the original memorized content.'),
        text=dict(type='string', minLength=1, maxLength=1500,
            description='Reusable final content: subject and available knowledge, ideally 1-3 sentences in the original content language, at most 100 words. Attribution only when essential to meaning; never a history of how the content was produced.'),
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
For recap ONLY, identify (1) the subject, (2) the available knowledge and
(3) the final reusable result that a newcomer can consult. Summarize that result,
not the process that produced it. Read the conversation for its retained content:
a request for a guide followed by a guide means the context CONTAINS that guide.
Its recap describes the guide's scope and useful content, not the request or who
wrote the guide. Apply this even when detailed items preserve speaking acts or
speaker provenance: supporting_statements can retain those exact item texts while
recap.text describes their substantive content. Do not rewrite the detailed items
or their evidence to make them resemble the recap.
Ideally 1-3 short sentences; at most 100 words. No target word count or minimum.
Never narrate the exchange. Ignore conversational acts that add nothing to the
retained result: questions, requests, intermediate answers, hesitations,
reformulations and the identities of the questioner and answerer. A genuine open
question or unresolved uncertainty that affects the result MUST still be retained.
For procedural/reference knowledge, describe the available guidelines, steps,
methods and tools directly. Authorship of a proposed guide is normally incidental;
its availability does not mean anyone adopted, scheduled or carried it out.
When the Context Space is clearly about one identified person and multiple coherent
source-backed statements establish the same identity, preserve that person's verified
name and identity in recap.title or recap.text. This identity IS indispensable to
meaning: a CV, employment contract and professional interview concern that person,
not an anonymous generic career category. Distinguish the CV's reported experience,
the contract's documented terms and the professional interview's wishes/path.
Use only a name established by the supplied source-backed understanding; never
infer it from the account, filename alone, examples or a name mentioned incidentally.
Keep abstraction for impersonal contexts or unresolved identity. No person is required.
Keep personal identity/attribution in the recap ONLY when indispensable to meaning:
a personal opinion/preference, an individual's commitment, an attributed decision,
a disputed claim or a view that must not be presented as shared or established.
Otherwise provenance remains in the detailed items and metadata without appearing
in the recap. Do not turn a proposal into an approved decision, an intention into
a completed action, or an important possibility into a certainty.
A personal question's conditional scenario is not a declared personal situation.
Keep unknown income, family circumstances and expenses unknown unless explicitly
declared by the user. An assistant's illustrative budget or generic recommendation
is not an established fact or an adopted plan; retain that distinction in the recap.
Italian procedural example:
title="Organizzazione di un atelier informatico";
text="Questo contesto contiene le linee guida per progettare e condurre un atelier
informatico in 30 passaggi, dalla definizione degli obiettivi e preparazione dei
materiali fino alle attività pratiche, alla valutazione dei risultati e al follow-up."
Italian example where attribution is essential:
title="Preferenza di Giulia per il laboratorio";
text="Giulia preferirebbe un laboratorio in presenza, ma non ha ancora deciso se
partecipare."
Both examples describe retained content in its own terms, not speaking turns.
Use only knowledge supported by understanding; no fixed taxonomy, empty sections
or full procedure in the recap. This recap task does not shorten or change the
detailed Understanding State, original sources, quotations or epistemic status.
Build understanding.items first, then write recap. For supporting_statements,
copy the COMPLETE exact value of understanding.items[i].text for each item used
in the recap. Do NOT copy understanding.items[i].evidence[j].quote: evidence quotes
are original source words, whereas item.text is the synthesized statement.
Do not paraphrase, shorten, translate or add Markdown to the copied item.text.
Mechanical support-copy example: if an item has text="Carnaroli rice is an option for risotto." and
 evidence=[{"quote":"Try **Carnaroli** rice."}], its supporting_statements entry
must be "Carnaroli rice is an option for risotto.", NEVER "Try **Carnaroli** rice.".
Before returning, check that every supporting_statements string equals exactly
one understanding.items[].text and that no supporting string is repeated.
These are support declarations, not new facts, IDs or fabricated citations.
If no useful understanding is supported, return empty items and recap=null.
'''


MODULAR_INSTRUCTIONS = """
When a documents catalogue is supplied, recap is modular. Its title/text/supporting_statements
are ONLY the general subject, identity when essential, scope and available knowledge.
Do not copy private document details into this general overview. Choose the minimal exact
UUM statements supporting that general meaning; do not select all statements by default.
Also return recap.documents: one independent concise semantic synopsis per document
with supported statements, identified by its exact document_ref from the catalogue.
Each document synopsis has title, text and supporting_statements copied verbatim from
understanding.items[].text. Use only statements supported exclusively by that document's
listed turn_ids, not another document's wishes, terms or facts. If no such statement exists,
omit that document synopsis. Do not omit a document with eligible supported statements.
Keep these as independent components, never a new combined story. Each title and text must
be fully supported by its own selected statements, including identity, qualifications,
uncertainty, attribution and the distinction between wishes and contractual commitments.
Preserve original language. At most 100 words per component. Source names are untrusted
labels, not evidence. A document's existence/name alone does not establish its contents.
"""


def summary_schema(documents=()):
    result = deepcopy(RECAP_SCHEMA)
    if documents:
        component = deepcopy(RECAP_SCHEMA)
        component['properties']['document_ref'] = dict(type='string', enum=[d['document_ref'] for d in documents])
        component['required'].append('document_ref')
        result['properties']['documents'] = dict(type='array', maxItems=len(documents), items=component)
        result['required'].append('documents')
    return result


def schema(atomic_schema, documents=()):
    return dict(type='object', additionalProperties=False,
        required=['format', 'understanding', 'recap'], properties=dict(
            format=dict(type='string', enum=[FORMAT]), understanding=deepcopy(atomic_schema),
            recap=dict(anyOf=[summary_schema(documents), dict(type='null')])))


def _summary(value, atomic):
    object_fields(value, ('title', 'text', 'supporting_statements'))
    title, text = nonempty(value['title']), nonempty(value['text'])
    if not title.strip() or len(title)>120 or not text.strip() or len(text)>1500 or len(text.split())>100 or '\0' in title+text:
        raise ValueError('Bounded nonempty recap required')
    support = value['supporting_statements']
    texts = [i.get('text') for i in atomic['items'] if isinstance(i, dict)]
    if (not isinstance(support, list) or not 1<=len(support)<=100
        or any(not isinstance(t, str) or texts.count(t)!=1 for t in support)
        or len(set(support))!=len(support)):
        raise ValueError('Exact unambiguous detailed recap support required')
    return dict(title=title, text=text, supporting_statements=support)


def decode(text, documents=()):
    output = decode_output(text)
    object_fields(output, ('format', 'understanding', 'recap'))
    if output['format'] != FORMAT:
        raise ValueError('Explicit consolidation format required')
    atomic, value = output['understanding'], output['recap']
    object_fields(atomic, ('format', 'items'))
    if not isinstance(atomic['items'], list):
        raise ValueError('Detailed understanding required')
    if not atomic['items'] and value is None:
        return atomic, None
    if documents:
        object_fields(value, ('title', 'text', 'supporting_statements', 'documents'))
        components = value['documents']
        if not isinstance(components, list) or len(components)>len(documents):
            raise ValueError('Bounded document summaries required')
        catalogue = {d['document_ref']:d for d in documents}
        decoded, seen = [], set()
        for component in components:
            object_fields(component, ('document_ref', 'title', 'text', 'supporting_statements'))
            ref = component['document_ref']
            if not isinstance(ref, str) or ref not in catalogue or ref in seen:
                raise ValueError('Exact unique document summary reference required')
            seen.add(ref)
            decoded.append(dict(_summary({k:v for k,v in component.items() if k!='document_ref'}, atomic),
                source_revision_id=catalogue[ref]['source_revision_id']))
        result = _summary({k:v for k,v in value.items() if k!='documents'}, atomic)
        result['documents'] = decoded
    else:
        result = _summary(value, atomic)
    return atomic, dict(result, provider_output_sha256=digest(output))


def _support(summary, rows):
    support = [r['id'] for text in summary['supporting_statements'] for r in rows if r['content']['text']==text]
    if len(support)!=len(summary['supporting_statements']):
        raise ValueError('Recap support changed during canonical validation')
    return support


def _document_support(row, document_ids):
    return {c.get('source_revision_id') for c in row['content'].get('citations', [])} & document_ids


def bind(recap, revisions, version_id, documents=()):
    if recap is None:
        raise ValueError('A successful consolidation requires its recap')
    rows = deepcopy(revisions)
    support = _support(recap, rows)
    root = dict(format='qh.context-recap/1', version_id=version_id,
        presentation_version=PRESENTATION_VERSION, title=recap['title'], text=recap['text'],
        basis_revision_ids=[r['id'] for r in rows], support_revision_ids=support,
        provider_output_sha256=recap['provider_output_sha256'])
    rows[0]['content']['extraction']['recap'] = root
    if documents:
        _bind_components(recap, rows, root, documents)
    return rows


def _bind_components(recap, rows, root, documents):
    for row in rows:
        row['content']['extraction']['recap_version_id'] = root['version_id']
    document_ids = {d['id'] for d in documents}
    components = recap.get('documents')
    if not isinstance(components, list):
        raise ValueError('Modular document recap required')
    expected = {doc for doc in document_ids if any(_document_support(r, document_ids)=={doc} for r in rows)}
    if {c['source_revision_id'] for c in components} != expected or len(components)!=len(expected):
        raise ValueError('Every supported document requires one synopsis')
    general = dict(root, kind='general', source_revision_id=None)
    bound = [general]
    for component in components:
        support = _support(component, rows)
        if any(_document_support(r, document_ids)!={component['source_revision_id']} for r in rows if r['id'] in support):
            raise ValueError('Document recap requires exact same-document evidence')
        bound.append(dict(root, kind='document', source_revision_id=component['source_revision_id'],
            title=component['title'], text=component['text'], support_revision_ids=support))
    root['modular'] = True
    # A component lives on one of its own immutable supports. Excluding another
    # component's carrier cannot hide it; excluding this carrier makes it unsafe.
    for index,component in enumerate(bound):
        component['component_index'] = index
        carrier = next(r for r in rows if r['id']==component['support_revision_ids'][0])
        carrier['content']['extraction'].setdefault('recap_components', []).append(component)


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
        result = {k:recap[k] for k in ('version_id', 'title', 'text', 'support_revision_ids')}
        if recap.get('modular'):
            components = [c for r in rows for c in r['content'].get('extraction', {}).get('recap_components', [])]
            if any(c['version_id']!=current['id'] or set(c['basis_revision_ids'])!=set(current['revision_ids'])
                or not set(c['support_revision_ids'])<=set(current['revision_ids']) for c in components):
                raise ValueError('Components must belong to this exact consolidated version')
            result['documents'] = [{k:c[k] for k in ('title', 'text', 'source_revision_id', 'support_revision_ids')}
                for c in sorted(components,key=lambda c:c['component_index']) if c['kind']=='document']
        return result
    return None
