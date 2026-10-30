"""Constrain consolidation evidence before generation using the existing resolver."""
from copy import deepcopy

from app.understanding.citations import CitationResolutionError, resolve_output_citations


def exact_quote_schema(atomic_schema, packet):
    quotes = exact_quotes(packet)
    schema = deepcopy(atomic_schema)
    for shape in schema['properties']['items']['items']['anyOf']:
        shape['properties']['evidence']['items']['properties']['quote']['enum'] = quotes
    return schema


def exact_quotes(packet, *, validation_source=None):
    # The Engine has already authorized this exact source packet. Retain full
    # turns for qualifications across lines, plus individual original lines for
    # concise multi-part evidence. No source edits, semantic splitting or repairs.
    source = dict(id=packet['source_revision_id'], content=packet['text'],
        origin=dict(turns=packet['turns']))
    candidates = {}
    for turn in packet['turns']:
        text = packet['text'][turn['start']:turn['end']]
        for quote in [text, *text.splitlines()]:
            if quote.strip():
                candidates[quote] = None
    quotes = _unique_quotes(list(candidates), source)
    if validation_source is not None:
        if validation_source['id'] != source['id']:
            raise ValueError('Same original source required for chunk evidence')
        quotes = _unique_quotes(quotes, validation_source)
    if not quotes:
        raise ValueError('No unique original quotation available for consolidation')
    return quotes


def _unique_quotes(candidates, source):
    quotes = []
    # Reuse QH-32's exact overlapping-match and original-turn rules; ambiguous
    # candidates never reach the provider's choices. This is not output repair.
    for offset in range(0, len(candidates), 100):
        batch = candidates[offset:offset+100]
        output = dict(items=[dict(evidence=[dict(source_revision_id=source['id'], quote=q) for q in batch])])
        rejected = set()
        try:
            resolve_output_citations(output, source=source)
        except CitationResolutionError as exc:
            rejected = {issue['evidence_index'] for issue in exc.issues}
        quotes.extend(q for index, q in enumerate(batch) if index not in rejected)
    return quotes
