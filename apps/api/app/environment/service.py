"""Personal organization contract, with policy before private metadata access."""
from copy import deepcopy
from typing import Protocol
from uuid import UUID, uuid5, NAMESPACE_URL

from app.policy.models import PolicyAction, PolicyRequest

LABELS = ('Travail & projets', 'Finances & démarches', 'Relations & proches',
          'Santé & bien-être', 'Loisirs & découvertes', 'Vie quotidienne & habitat',
          'Apprentissage & évolution')


class OrganizationConflict(ValueError):
    """The owner's organization changed since it was read."""


def defaults():
    return {'version': 0, 'domains': [{'id': str(uuid5(NAMESPACE_URL, 'qh.domain/'+str(i))),
                                     'name': name} for i, name in enumerate(LABELS)],
            'memberships': {}}


def validate(document):
    if set(document) != {'version', 'domains', 'memberships'}:
        raise ValueError('Invalid organization')
    if type(document['version']) is not int or document['version'] < 0:
        raise ValueError('Invalid organization version')
    domains, memberships = document['domains'], document['memberships']
    if not isinstance(domains, list) or len(domains) > 50 or not isinstance(memberships, dict) or len(memberships) > 1000:
        raise ValueError('Organization limit exceeded')
    ids = set()
    for domain in domains:
        if not isinstance(domain, dict) or set(domain) != {'id', 'name'}:
            raise ValueError('Invalid domain')
        id = str(UUID(domain['id']))
        if id != domain['id'] or id in ids or not isinstance(domain['name'], str) or not domain['name'].strip() or len(domain['name']) > 100 or '\0' in domain['name']:
            raise ValueError('Invalid domain')
        ids.add(id)
    for space, assigned in memberships.items():
        if str(UUID(space)) != space or not isinstance(assigned, list) or any(not isinstance(v, str) for v in assigned) or len(assigned) != len(set(assigned)) or not set(assigned) <= ids:
            raise ValueError('Invalid memberships')
    return deepcopy(document)


class OrganizationRepository(Protocol):
    async def read(self, subject): ...
    async def replace(self, subject, document): ...


class EnvironmentService:
    def __init__(self, *, repository: OrganizationRepository, policy):
        self.repository, self.policy = repository, policy

    async def _allow(self, subject, scopes=()):
        result = await self.policy.evaluate(PolicyRequest(subject_id=subject,
            action=PolicyAction.ORGANIZE_ENVIRONMENT if not scopes else PolicyAction.READ_CONTEXT,
            context_ids=tuple(scopes)))
        if not result.allowed:
            raise PermissionError('Owner access required')

    async def read(self, subject):
        await self._allow(subject)
        document = await self.repository.read(subject)
        # Memberships never disclose foreign identities after ownership revocation.
        await self._allow(subject, tuple(document['memberships']))
        return document

    async def replace(self, subject, document):
        await self._allow(subject)
        document = validate(document)
        await self._allow(subject, tuple(document['memberships']))
        return await self.repository.replace(subject, document)
