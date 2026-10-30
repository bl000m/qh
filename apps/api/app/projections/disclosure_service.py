"""Automatic scope → existing Projection Engine → Guard → exact owner approval."""
from dataclasses import replace
from datetime import datetime, timezone
import json
from uuid import uuid4

from app.projections.disclosure import (
    AccessPolicy, ApprovedSnapshot, DisclosureDecisionRequired, DisclosurePreview, TEXT_REVIEW,
    preview_fingerprint, validate_preview,
)
from app.projections.disclosure_guard import OutboundDisclosureGuard, redact, HIGH_RISK
from app.projections.drafts import DraftSpec, ProjectionConflict, ProjectionNotFound, ProjectionUnavailable
from app.projections.recap import recap_status


class DisclosureService:
    def __init__(self, *, drafts, repository, guard=None, clock=None):
        self.drafts, self.repository = drafts, repository
        self.guard = guard or OutboundDisclosureGuard()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _fresh(self, policy, created_at=None):
        now = self.clock()
        if policy.expires_at <= now or (created_at and (now-created_at).total_seconds() >= 900):
            raise ProjectionConflict('Disclosure expired; prepare a new preview')

    @staticmethod
    def _scope(selection, policy):
        selected, excluded = {}, []
        for row in selection.candidates:
            if row.key in policy.excluded:
                excluded.append(dict(revision_id=row.key.revision_id,
                    reason='owner_restriction'))
            else:
                selected[row.key] = row
        # Remove dangling relations to a fixed point; never expand scope to endpoints.
        while True:
            dangling = [k for k, row in selected.items() if not set(row.endpoints) <= set(selected)]
            if not dangling:
                break
            for key in dangling:
                selected.pop(key)
                excluded.append(dict(revision_id=key.revision_id, reason='endpoint_outside_scope'))
        return tuple(sorted(selected)), excluded

    async def prepare(self, subject, scope, policy):
        await self.drafts._allow(subject, scope)
        if not isinstance(policy, AccessPolicy):
            raise ValueError('Explicit access policy required')
        self._fresh(policy)
        selection = await self.repository.select(subject, scope)
        if selection.context_id != scope:
            raise ProjectionUnavailable('Disclosure unavailable')
        if not set(policy.semantic_documents + policy.original_documents)<=set(selection.document_sources):
            raise ProjectionNotFound('Document unavailable')
        keys, excluded = self._scope(selection, policy)
        draft, rows = None, ()
        if keys:
            draft = await self.drafts.create(subject, scope, DraftSpec(recipient_kind='subject',
                recipient=policy.recipient_email, purpose=policy.purpose, included=keys,
                expires_at=policy.expires_at))
            rows = (await self.drafts.resolve(subject, scope, draft.id, draft.version)).revisions
        # The independently approved Space introduction retains ALL its exact
        # supports and Guard checks. PDF selection restricts detailed knowledge,
        # never re-summarizes or repairs an unsafe introduction.
        general, general_report = self.guard.apply(rows, policy)
        draft_rows = rows
        rows, document_exclusions = self._document_scope(rows, policy, selection.document_sources)
        payload, report = self.guard.apply(rows, policy)
        payload.pop('recap', None)
        if general.get('recap'):
            payload['recap'] = general['recap']
            report['risks'] = sorted(set(report['risks']) | set(general_report['risks']))
            if not payload['items']:
                self._introduction_only(draft_rows, payload, report, general_report)
        payload.pop('document_recaps', None)
        payload['semantic_document_count'] = len(policy.semantic_documents)
        report['recap_status'] = recap_status(rows, payload.get('recap'))
        title = redact(selection.name)[0]
        payload['name'] = title if not HIGH_RISK.search(title) else 'Contexte partagé'
        report['exclusions'] = excluded + document_exclusions + report['exclusions']
        report['status'] = 'review_required' if payload['items'] else 'no_disclosable_items'
        report['message'] = ('Examinez la divulgation proposée.' if report['status']=='review_required' else
            'Aucune information communicable dans ce périmètre.')
        if len(json.dumps(payload).encode()) > 262144:
            raise ProjectionUnavailable('Disclosure exceeds bounded preview size')
        result = DisclosurePreview(id=str(uuid4()), context_id=scope, owner_id=subject,
            draft_id=draft.id if draft else None, policy=policy, selection_stamp=selection.stamp,
            payload_json=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            report_json=json.dumps(report, ensure_ascii=False, sort_keys=True), fingerprint='', created_at=self.clock())
        result = replace(result, fingerprint=preview_fingerprint(result))
        await self.drafts._allow(subject, scope)
        prepared = await self.repository.prepare(result)
        validate_preview(prepared, subject, scope)
        await self.drafts._allow(subject, scope)
        return prepared

    @staticmethod
    def _introduction_only(rows, payload, report, general_report):
        """Snapshot representation of the exact recap; never a new canonical item."""
        masked = {m['reference'] for m in general_report['masks']}
        safe = {a['revision_id']:a for a in general_report['anchors'] if a['reference'] not in masked}
        for row in rows:
            extraction = row.content.get('extraction', {})
            components = [c for c in extraction.get('recap_components', []) if c.get('kind')=='general']
            root = extraction.get('recap', {})
            if root and not root.get('modular'):
                components.append(root)
            for component in components:
                if any(component.get(k)!=payload['recap'][k] for k in ('title','text')):
                    continue
                anchor = next((safe[ref] for ref in component.get('support_revision_ids', []) if ref in safe), None)
                if anchor:
                    payload['items'] = [dict(reference='R1', text=payload['recap']['text'],
                        validation_state='proposed', origin_kind='ai', sources=[])]
                    report['anchors'] = [dict(anchor, reference='R1')]
                    report['introduction_only'] = True
                    return
        raise ProjectionUnavailable('Verified introduction support unavailable')

    @staticmethod
    def _document_scope(rows, policy, document_sources):
        selected, excluded = [], []
        unauthorized = set(document_sources) - set(policy.semantic_documents)
        for row in rows:
            sources = {p.revision_id for p in row.provenance}
            sources.update(c.get('source_revision_id') for c in row.content.get('citations', []))
            if sources & unauthorized:
                excluded.append(dict(revision_id=row.revision_id, reason='document_information_not_authorized'))
            else:
                selected.append(row)
        return tuple(selected), excluded

    async def preview(self, subject, scope, preview_id):
        await self.drafts._allow(subject, scope)
        result = await self.repository.preview(subject, scope, preview_id)
        validate_preview(result, subject, scope)
        await self.drafts._allow(subject, scope)
        return result

    async def approve(self, subject, scope, preview_id, fingerprint, *, exceptions=()):
        preview = await self.preview(subject, scope, preview_id)
        self._fresh(preview.policy, preview.created_at)
        if preview.fingerprint != fingerprint:
            raise ProjectionConflict('Disclosure changed')
        if not preview.payload['items'] or preview.draft_id is None:
            raise ProjectionNotFound('No disclosable items')
        risks = set(preview.report['risks'])
        if (not isinstance(exceptions, tuple) or len(set(exceptions)) != len(exceptions)
                or set(exceptions) != risks or not risks <= {TEXT_REVIEW}):
            raise DisclosureDecisionRequired('Explicit decision on the named preview risks required')
        # Revalidate graph, pinned draft and canonical selection before approval.
        if preview.draft_id is not None:
            await self.drafts.resolve(subject, scope, preview.draft_id, 1)
        current = await self.repository.select(subject, scope)
        if current.stamp != preview.selection_stamp:
            raise ProjectionConflict('Context changed; prepare a new preview')
        await self.drafts._allow(subject, scope)
        snapshot = await self.repository.approve(preview, tuple(sorted(exceptions)))
        self._snapshot_checked(snapshot, subject, scope)
        if (snapshot.preview_id != preview.id or snapshot.fingerprint != preview.fingerprint
                or snapshot.payload != preview.payload or snapshot.policy != preview.policy):
            raise ProjectionUnavailable('Disclosure unavailable')
        await self.drafts._allow(subject, scope)
        return snapshot

    async def snapshot(self, subject, scope, snapshot_id):
        await self.drafts._allow(subject, scope)
        result = await self.repository.snapshot(subject, scope, snapshot_id)
        self._snapshot_checked(result, subject, scope, snapshot_id)
        await self.drafts._allow(subject, scope)
        return result

    @staticmethod
    def _snapshot_checked(snapshot, subject, scope, snapshot_id=None):
        if (not isinstance(snapshot, ApprovedSnapshot) or snapshot.owner_id != subject
                or snapshot.context_id != scope or (snapshot_id is not None and snapshot.id != snapshot_id)):
            raise ProjectionUnavailable('Disclosure unavailable')
