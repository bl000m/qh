"""Request-local model aliases; never canonical identities or heuristic repairs."""
import json

from app.chat.serialization import compact_context, expand_context, encoded

FORMAT = 'qh.chat.context/2'


def aliases_for(context_id, rows):
    ids = [row['revision_id'] for row in rows]
    if (len(rows) > 40 or any(row['context_space_id'] != context_id for row in rows)
            or any(not isinstance(ref, str) or not ref for ref in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError('Invalid alias scope or revision identity')
    # Stable for exactly the provided set, independent of retrieval/response order.
    return {f'R{i}': ref for i, ref in enumerate(sorted(ids), 1)}


def encode_model_context(context_id, rows, *, partial):
    packet = json.loads(compact_context(context_id, rows, partial=partial))
    packet.update(format=FORMAT, allowed_reference_aliases=aliases_for(context_id, rows))
    return json.dumps(packet, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def expand_model_context(packet):
    """Strict round-trip plus a bijection over exactly the transmitted revisions."""
    if (not isinstance(packet, dict) or set(packet) != {
            'format', 'context_space_id', 'partial_coverage', 'common_metadata',
            'sources', 'revisions', 'allowed_reference_aliases'} or packet['format'] != FORMAT
            or not isinstance(packet['allowed_reference_aliases'], dict)):
        raise ValueError('Invalid model reference protocol')
    legacy = {key: value for key, value in packet.items() if key != 'allowed_reference_aliases'}
    legacy['format'] = 'qh.chat.context/1'
    rows = expand_context(legacy)
    expected = aliases_for(packet['context_space_id'], rows)
    if encoded(packet['allowed_reference_aliases']) != encoded(expected):
        raise ValueError('Ambiguous or foreign alias mapping')
    return rows
