"""Request-local provider protocol; canonical evidence still uses exact QH-32 quotes."""
from copy import deepcopy

from app.understanding.citations import resolve_output_citations
from app.understanding.extractor import object_fields
from app.understanding.quote_schema import exact_quotes

FORMAT = 'qh.atomic-understanding.refs/1'


class PassageReferences:
    def __init__(self, packet, atomic_schema, *, validation_source=None):
        self.packet = deepcopy(packet)
        self.canonical_format = atomic_schema['properties']['format']['enum'][0]
        source = dict(id=packet['source_revision_id'], content=packet['text'], origin=dict(turns=packet['turns']))
        quotes = exact_quotes(packet, validation_source=validation_source)
        passages = []
        for offset in range(0, len(quotes), 100):
            evidence = [dict(source_revision_id=source['id'], quote=q) for q in quotes[offset:offset+100]]
            resolved, _ = resolve_output_citations(dict(items=[dict(evidence=evidence)]), source=source)
            passages.extend(resolved['items'][0]['evidence'])
        self.passages = {f'p{i+1:03d}': p for i, p in enumerate(passages)}
        self.schema = deepcopy(atomic_schema)
        self.schema['properties']['format']['enum'] = [FORMAT]
        for shape in self.schema['properties']['items']['items']['anyOf']:
            evidence = shape['properties'].pop('evidence')
            shape['properties']['evidence_refs'] = dict(type='array', minItems=evidence['minItems'],
                maxItems=evidence['maxItems'],
                items=dict(type='string', enum=list(self.passages)))
            shape['required'] = ['evidence_refs' if field=='evidence' else field for field in shape['required']]

    def disclosure(self):
        # Nonoverlapping segments show references beside their original words.
        # Joining segment.text reconstructs the entire original source exactly once.
        return dict(**{k:deepcopy(v) for k,v in self.packet.items() if k!='text'}, segments=self._segments(),
            # Turn identity and speaker are already given by the enclosing turn's
            # offsets; repeating a turn UUID for every passage adds no evidence.
            passages=[dict(ref=ref, start=p['start'], end=p['end'])
            for ref, p in self.passages.items()])

    def _segments(self):
        events = {0: [set(), set()], len(self.packet['text']): [set(), set()]}
        for ref, passage in self.passages.items():
            events.setdefault(passage['start'], [set(), set()])[0].add(ref)
            events.setdefault(passage['end'], [set(), set()])[1].add(ref)
        boundaries, active, segments = sorted(events), set(), []
        for start, end in zip(boundaries, boundaries[1:]):
            opening, closing = events[start]
            active.difference_update(closing)
            active.update(opening)
            segments.append(dict(text=self.packet['text'][start:end], passage_refs=sorted(active)))
        return segments

    def expand(self, output):
        object_fields(output, ('format', 'items'))
        if output['format']!=FORMAT or not isinstance(output['items'], list) or len(output['items'])>self.schema['properties']['items']['maxItems']:
            raise ValueError('Bounded passage-reference output required')
        items = []
        for item in output['items']:
            shape = self.schema['properties']['items']['items']['anyOf'][0 if isinstance(item, dict) and item.get('primary_dimension') is None else 1]
            object_fields(item, shape['required'])
            refs = item['evidence_refs']
            limit = shape['properties']['evidence_refs']['maxItems']
            if (not isinstance(refs, list) or not 1<=len(refs)<=limit
                or any(not isinstance(ref, str) or ref not in self.passages for ref in refs)
                or len(set(refs))!=len(refs)):
                raise ValueError('Distinct references from the authorized passage catalogue required')
            # No model-supplied text, source ID or offsets can enter canonical evidence.
            items.append(dict(**{k:deepcopy(v) for k,v in item.items() if k!='evidence_refs'},
                evidence=[dict(quote=self.passages[ref]['quote']) for ref in refs]))
        return dict(format=self.canonical_format, items=items)
