"""Structural outbound rules only: the owner shares the whole canonical understanding.

No keyword, regex, date, number or category filtering (owner decision 2026-10-31):
sharing is an explicit owner choice, not an anonymisation. Original quotations,
sources and internal identifiers are never part of the recipient payload.
"""
from app.core.uum import PRIMARY_DIMENSIONS
from app.projections.disclosure import GUARD_VERSION, TEXT_REVIEW
from app.projections.recap import projected_recap, recap_status


class OutboundDisclosureGuard:
    def apply(self, revisions, policy):
        items, exclusions, anchors = [], [], []
        sources = {ref: 'S'+str(i+1) for i, ref in enumerate(sorted({
            p.revision_id for r in revisions for p in r.provenance}))}
        relations = {}
        for row in revisions:
            reference = 'R'+str(len(items)+1)
            item, reason = self._item(row, reference, sources)
            if reason:
                exclusions.append(dict(revision_id=row.revision_id, reason=reason))
                continue
            items.append(item)
            anchors.append(dict(reference=reference, item_id=row.item_id, revision_id=row.revision_id))
            if row.relation is not None:
                relations[reference] = row.relation
        items, anchors = self._relations(items, anchors, relations, exclusions)
        payload = dict(format=GUARD_VERSION, items=items)
        recap = projected_recap(revisions, anchors)
        if recap:
            payload['recap'] = recap
        return payload, dict(exclusions=exclusions, anchors=anchors, recap_status=recap_status(revisions, recap),
            masks=[], risks=[TEXT_REVIEW] if items else [],
            warning='Toute la compréhension de ce Context Space sera partagée, y compris les informations '
                'personnelles éventuellement présentes. Ce partage n’est pas une anonymisation.')

    @staticmethod
    def _item(row, reference, sources):
        text = row.content.get('text')
        if row.validation_state not in ('confirmed', 'proposed'):
            return None, 'ineligible_state'
        if not isinstance(text, str) or not text.strip() or len(text) > 16000:
            return None, 'unsupported_content'
        item = dict(reference=reference, text=text, validation_state=row.validation_state,
            origin_kind=row.origin_kind, sources=sorted({sources[p.revision_id] for p in row.provenance}))
        primary = row.content.get('primary_dimension')
        if (isinstance(primary, dict) and primary.get('value') in PRIMARY_DIMENSIONS
                and primary.get('certainty') in ('asserted', 'tentative')
                and primary.get('review_state') in ('proposed', 'accepted')):
            item['primary_dimension'] = {k: primary[k] for k in ('value', 'certainty', 'review_state')}
        return item, None

    @staticmethod
    def _relations(items, anchors, relations, exclusions):
        retained = {a['reference']: a for a in anchors}
        while True:
            keys = {(a['item_id'], a['revision_id']): ref for ref, a in retained.items()}
            dangling = [ref for ref, r in relations.items() if ref in retained and any(
                (getattr(r, side+'_item_id'), getattr(r, side+'_revision_id')) not in keys for side in ('source', 'target'))]
            if not dangling:
                break
            for ref in dangling:
                exclusions.append(dict(revision_id=retained.pop(ref)['revision_id'], reason='endpoint_not_disclosable'))
        # Recipient-local aliases reveal neither canonical IDs nor gaps left by exclusions.
        refs = {ref: 'R'+str(i+1) for i, ref in enumerate(retained)}
        source_refs = sorted({s for item in items if item['reference'] in retained for s in item['sources']})
        sources = {s: 'S'+str(i+1) for i, s in enumerate(source_refs)}
        result = []
        for item in items:
            ref = item['reference']
            if ref not in retained:
                continue
            if ref in relations:
                r = relations[ref]
                item['relation'] = {side: refs[keys[(getattr(r, side+'_item_id'), getattr(r, side+'_revision_id'))]]
                    for side in ('source', 'target')}
            item['reference'] = refs[ref]
            item['sources'] = [sources[s] for s in item['sources']]
            result.append(item)
        return result, [{**a, 'reference': refs[ref]} for ref, a in retained.items()]
