"""Small explicit outbound rules; never certify arbitrary text as anonymous."""
import re

from app.core.uum import PRIMARY_DIMENSIONS
from app.projections.disclosure import GUARD_VERSION, TEXT_REVIEW
from app.projections.recap import projected_recap, projected_components, recap_status


MASKS = (
    ('email', re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', re.UNICODE)),
    ('url', re.compile(r'https?://[^\s<>]+', re.I)),
    ('number', re.compile(r'(?<!\w)\+?\d[\d .()/\-]{5,}\d(?!\w)')),
    ('identifier', re.compile(r'\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){10,30}\b')),
)
# These deny recognisable fixture hazards; absence of a match is NEVER a safety proof.
HIGH_RISK = re.compile(r'\b(cancer|diab[eè]te|diagnosti\w*|m[eé]dica\w*|password|mot de passe|'
    r'secret|api[_ -]?key|sexualit\w*|suicid\w*)\b', re.I)


def redact(text):
    masked = []
    for name, pattern in MASKS:
        text, count = pattern.subn('[MASQUÉ]', text)
        if count:
            masked.append(name)
    return text, masked


def introductory_support(text):
    """Only unmasked, non-sensitive statements may support an introduction."""
    return (not HIGH_RISK.search(text) and not redact(text)[1]
        and not any(ord(c)<32 and c not in '\n\t' for c in text))


class OutboundDisclosureGuard:
    def apply(self, revisions, policy):
        items, exclusions, masks, anchors = [], [], [], []
        sources = {ref: 'S'+str(i+1) for i, ref in enumerate(sorted({
            p.revision_id for r in revisions for p in r.provenance}))}
        relations = {}
        for row in revisions:
            reference = 'R'+str(len(items)+1)
            item, reason, redactions = self._item(row, policy, reference, sources)
            if reason:
                exclusions.append(dict(revision_id=row.revision_id, reason=reason))
            else:
                items.append(item)
                anchors.append(dict(reference=reference, item_id=row.item_id, revision_id=row.revision_id))
                if row.relation is not None:
                    relations[reference] = row.relation
                if redactions:
                    masks.append(dict(reference=reference, rules=sorted(set(redactions))))
        items, anchors, masks = self._relations(items, anchors, masks, relations, exclusions)
        payload = dict(format=GUARD_VERSION, items=items)
        recap, document_recaps = projected_components(revisions, anchors, masks, redact, HIGH_RISK)
        if recap is None:
            recap = projected_recap(revisions, anchors, masks, redact, HIGH_RISK, items)
        if document_recaps:
            payload['document_recaps'] = document_recaps
        if recap:
            payload['recap'] = recap
        return payload, dict(exclusions=exclusions, anchors=anchors, recap_status=recap_status(revisions, recap or document_recaps),
            masks=masks, risks=[TEXT_REVIEW] if items else [],
            warning='Texte libre non certifié anonyme, y compris par combinaison d’attributs. '
                'Examinez les textes minimisés pour ce destinataire avant toute divulgation.')

    def _item(self, row, policy, reference, sources):
        content = row.content
        text = content.get('text')
        if row.validation_state not in ('confirmed', 'proposed'):
            return None, 'ineligible_state', []
        if not isinstance(text, str) or not text.strip() or len(text) > 16000:
            return None, 'unsupported_content', []
        if HIGH_RISK.search(text) or any(ord(c) < 32 and c not in '\n\t' for c in text):
            return None, 'recognised_high_risk', []
        safe, masks = redact(text)
        item = dict(reference=reference, text=safe, validation_state=row.validation_state,
            origin_kind=row.origin_kind, sources=sorted({sources[p.revision_id] for p in row.provenance}))
        primary = content.get('primary_dimension')
        if (isinstance(primary, dict) and primary.get('value') in PRIMARY_DIMENSIONS
                and primary.get('certainty') in ('asserted', 'tentative')
                and primary.get('review_state') in ('proposed', 'accepted')):
            item['primary_dimension'] = {k: primary[k] for k in ('value', 'certainty', 'review_state')}
        if policy.include_quotes:
            quotes, reason, quote_masks = self._quotes(content, row, sources)
            if reason:
                return None, reason, []
            item['citations'] = quotes
            masks += quote_masks
        return item, None, masks

    @staticmethod
    def _relations(items, anchors, masks, relations, exclusions):
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
            for quote in item.get('citations', []):
                quote['source'] = sources[quote['source']]
            result.append(item)
        return result, [{**a, 'reference': refs[ref]} for ref, a in retained.items()], [
            {**m, 'reference': refs[m['reference']]} for m in masks if m['reference'] in retained]

    @staticmethod
    def _quotes(content, row, sources):
        citations = content.get('citations', [])
        if not isinstance(citations, list) or len(citations) > 100:
            return [], 'unsupported_citations', []
        allowed = {p.revision_id for p in row.provenance}
        result, masks = [], []
        for citation in citations:
            if not isinstance(citation, dict):
                return [], 'unsupported_citations', []
            source, quote = citation.get('source_revision_id'), citation.get('quote')
            if source not in allowed or not isinstance(quote, str) or not 1 <= len(quote) <= 16000:
                return [], 'unsupported_citations', []
            if HIGH_RISK.search(quote):
                return [], 'recognised_high_risk_citation', []
            safe, rules = redact(quote)
            result.append(dict(source=sources[source], quote=safe, redacted=bool(rules)))
            masks += rules
        return result, None, masks
