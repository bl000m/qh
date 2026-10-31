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
from app.projections.document_scope import document_scope, empty_projection, is_empty_projection


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
        rows, document_exclusions = document_scope(rows, policy, selection.document_sources)
        payload, report = self.guard.apply(rows, policy)
        payload['semantic_document_count'] = len(selection.document_sources) if policy.knowledge_scope=='context' else len(policy.semantic_documents)
        report['document_scope_version'] = 3 if policy.knowledge_scope=='context' else 2
        report['recap_status'] = recap_status(rows, payload.get('recap'))
        title = redact(selection.name)[0]
        payload['name'] = title if not HIGH_RISK.search(title) else 'Contexte partagé'
        report['exclusions'] = excluded + document_exclusions + report['exclusions']
        report['status'] = 'review_required' if payload['items'] else 'no_disclosable_items'
        report['message'] = ('Examinez la divulgation proposée.' if report['status']=='review_required' else
            'Aucune information communicable dans ce périmètre.')
        if not payload['items']:
            payload = empty_projection(payload['name'])
            report['message'] = payload['notice']
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
        if not is_empty_projection(preview.payload) and (not preview.payload['items'] or preview.draft_id is None):
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
