"""Explicit application-boundary assembly, never enabled by startup/default env."""
from dataclasses import dataclass,field,replace
import os
from pathlib import Path
import stat

from adapters.context.projection_drafts import NativeDraftResolver
from adapters.guest_security import SecureGuestProofs
from adapters.postgres.disclosure import PostgresDisclosureRepository
from adapters.postgres.projection_drafts import PostgresDraftRepository
from adapters.sandbox_mail import SandboxSMTPMailer
from adapters.llm.guest_offline import OfflineSnapshotProvider
from app.chat.guest import GuestSnapshotChat
from app.policy.services import projection_authorizer,guest_authorizer
from app.projections.engine import ProjectionDraftService
from app.projections.disclosure_service import DisclosureService
from app.projections.guest_service import GuestInvitationService


@dataclass(frozen=True,slots=True,kw_only=True)
class SharingSettings:
    origin:str
    verifier_key:bytes=field(repr=False)


def private_sharing_settings():
    path=Path('/run/qh-sharing/verifier.key')
    metadata=path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077 or metadata.st_size!=32:
        raise ValueError('Private 32-byte sharing verifier key required')
    return SharingSettings(origin=os.environ['QH_SHARING_ORIGIN'],verifier_key=path.read_bytes())


def bind_sharing(services,runtime,repository,settings):
    drafts=ProjectionDraftService(repository=PostgresDraftRepository(url=runtime.url),
        authorize=projection_authorizer(services.policy),resolver=NativeDraftResolver(
            repository_for=runtime.repository,projector=runtime.projector))
    sharing=DisclosureService(drafts=drafts,repository=PostgresDisclosureRepository(url=runtime.url,projector=runtime.projector))
    guest=GuestInvitationService(disclosures=sharing,repository=repository,
        proofs=SecureGuestProofs(settings.verifier_key),mailer=SandboxSMTPMailer(),authorize=guest_authorizer(services.policy))
    return replace(services,sharing=sharing,guest=guest,guest_chat=GuestSnapshotChat(guest=guest,provider=OfflineSnapshotProvider()))
