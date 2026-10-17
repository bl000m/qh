"""Lossless internal provider context; not a public DTO or persistence format.

Semantic content/state stay explicit on every revision. Only identical administrative
metadata and repeated canonical source objects are factored out. Authorization and
source ownership are established by canonical hydration before this pure formatter.
"""
from copy import deepcopy
from dataclasses import fields
import json

from app.core.models import CanonicalRevision, CanonicalSource

FORMAT = 'qh.chat.context/1'
COMMON_FIELDS = frozenset((
    'context_space_id', 'revision_no', 'type_version', 'origin_kind',
    'validated_by', 'validated_at', 'current_revision_id', 'based_on_revision_id',
))
REVISION_FIELDS = frozenset(f.name for f in fields(CanonicalRevision))
SOURCE_FIELDS = frozenset(f.name for f in fields(CanonicalSource))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',', ':'))


def source_catalog(rows):
    sources, identities, fingerprints = {}, {}, {}
    for row in rows:
        seen = set()
        for source in row['provenance']:
            if (set(source) != SOURCE_FIELDS or not isinstance(source['origin'], dict)
                    or type(source['revision_no']) is not int or source['revision_no'] < 1
                    or any(not isinstance(source[k], str) or not source[k]
                           for k in ('source_id', 'source_revision_id'))):
                raise ValueError('Invalid canonical source')
            ref = source['source_revision_id']
            identity = (source['source_id'], source['revision_no'])
            fingerprint = encoded(source)
            if (ref in seen or ref in sources and fingerprints[ref] != fingerprint
                    or identity in identities and identities[identity] != ref):
                raise ValueError('Conflicting canonical source identity')
            seen.add(ref)
            sources[ref], identities[identity], fingerprints[ref] = source, ref, fingerprint
    return sources


def compact_context(context_id, rows, *, partial):
    if any(set(row) != REVISION_FIELDS or row['context_space_id'] != context_id for row in rows):
        raise ValueError('Invalid canonical context scope')
    sources = source_catalog(rows)
    common = {key: rows[0][key] for key in sorted(COMMON_FIELDS)
              if rows and all(encoded(row[key]) == encoded(rows[0][key]) for row in rows)}
    packed = [{**{k: v for k, v in row.items() if k not in common and k != 'provenance'},
               'provenance': [s['source_revision_id'] for s in row['provenance']]}
              for row in rows]
    # allow_nan=False also rejects nonfinite values in arbitrary extension content.
    return json.dumps(dict(format=FORMAT, context_space_id=context_id,
                           partial_coverage=partial, common_metadata=common,
                           sources=sources, revisions=packed),
                      ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def expand_context(packet):
    """Reconstruct exact JSON records for the mock, offline audit and round-trip tests."""
    if (not isinstance(packet, dict) or set(packet) != {
            'format', 'context_space_id', 'partial_coverage', 'common_metadata', 'sources', 'revisions'}
            or packet['format'] != FORMAT or type(packet['partial_coverage']) is not bool
            or not isinstance(packet['context_space_id'], str) or not packet['context_space_id']
            or not isinstance(packet['common_metadata'], dict)
            or packet['common_metadata'].keys() - COMMON_FIELDS
            or not isinstance(packet['sources'], dict) or not isinstance(packet['revisions'], list)):
        raise ValueError('Invalid compact context')
    common, sources = packet['common_metadata'], packet['sources']
    rows, used, ids = [], set(), set()
    for packed in packet['revisions']:
        if not isinstance(packed, dict) or common.keys() & packed.keys():
            raise ValueError('Conflicting shared metadata')
        row = deepcopy(common | packed)
        if (set(row) != REVISION_FIELDS or row['context_space_id'] != packet['context_space_id']
                or not isinstance(row['revision_id'], str) or not row['revision_id']
                or row['revision_id'] in ids or not isinstance(row['provenance'], list)
                or any(not isinstance(ref, str) or ref not in sources for ref in row['provenance'])):
            raise ValueError('Invalid compact revision')
        ids.add(row['revision_id'])
        for ref in row['provenance']:
            if not isinstance(sources[ref], dict) or sources[ref].get('source_revision_id') != ref:
                raise ValueError('Invalid compact source reference')
        used.update(row['provenance'])
        row['provenance'] = [deepcopy(sources[ref]) for ref in row['provenance']]
        rows.append(row)
    if used != sources.keys():
        raise ValueError('Unreferenced source disclosure')
    source_catalog(rows)
    return rows
