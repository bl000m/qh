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
                                     'name': name, 'description': ''} for i, name in enumerate(LABELS)],
            'memberships': {}, 'primary_domains': {}, 'space_descriptions': {}, 'usage': {}}


def validate(document):
    if not {'version', 'domains', 'memberships', 'primary_domains'} <= set(document) or set(document) - {'version', 'domains', 'memberships', 'primary_domains', 'space_descriptions'}:
        raise ValueError('Invalid organization')
    if type(document['version']) is not int or document['version'] < 0:
        raise ValueError('Invalid organization version')
    domains, memberships = document['domains'], document['memberships']
    if not isinstance(domains, list) or len(domains) > 50 or not isinstance(memberships, dict) or len(memberships) > 1000:
        raise ValueError('Organization limit exceeded')
    ids = set()
    for domain in domains:
        if not isinstance(domain, dict) or not {'id', 'name'} <= set(domain) or set(domain) - {'id', 'name', 'description'}:
            raise ValueError('Invalid domain')
        id = str(UUID(domain['id']))
        if id != domain['id'] or id in ids or not isinstance(domain['name'], str) or not domain['name'].strip() or len(domain['name']) > 100 or '\0' in domain['name']:
            raise ValueError('Invalid domain')
        if 'description' in domain:
            validate_description(domain['description'])
        ids.add(id)
    for space, assigned in memberships.items():
        if str(UUID(space)) != space or not isinstance(assigned, list) or any(not isinstance(v, str) for v in assigned) or len(assigned) != len(set(assigned)) or not set(assigned) <= ids:
            raise ValueError('Invalid memberships')
    primary = document['primary_domains']
    if not isinstance(primary, dict) or set(primary) != {s for s, ids in memberships.items() if ids}:
        raise ValueError('Every classified Space requires one primary domain')
    if any(primary[s] not in memberships[s] for s in primary):
        raise ValueError('Primary domain must be a membership')
    descriptions = document.get('space_descriptions', {})
    if not isinstance(descriptions, dict) or len(descriptions) > 1000:
        raise ValueError('Invalid descriptions')
    for scope, description in descriptions.items():
        if str(UUID(scope)) != scope:
            raise ValueError('Invalid Space')
        validate_description(description)
    return deepcopy(document)


def validate_description(value):
    if not isinstance(value, str) or len(value) > 500 or '\0' in value:
        raise ValueError('Invalid description')


class OrganizationRepository(Protocol):
    async def read(self, subject): ...
    async def replace(self, subject, document): ...
    async def opened(self, subject, scope, event_id): ...
    async def create_space(self, subject, name, primary_domain_id): ...
    async def resume(self, subject, sort, domain, limit, after): ...


class EnvironmentService:
    def __init__(self, *, repository: OrganizationRepository, policy, context=None):
        self.repository, self.policy, self.context = repository, policy, context

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
        await self._allow(subject, tuple(set(document['memberships']) | set(document.get('space_descriptions', {}))))
        return document

    async def replace(self, subject, document):
        await self._allow(subject)
        document = validate(document)
        await self._allow(subject, tuple(set(document['memberships']) | set(document.get('space_descriptions', {}))))
        return await self.repository.replace(subject, document)

    async def opened(self, subject, scope, event_id):
        await self._allow(subject, (scope,))
        UUID(event_id)
        return await self.repository.opened(subject, scope, event_id)

    async def create_space(self, subject, name, primary_domain_id):
        await self._allow(subject)
        allowed = await self.policy.evaluate(PolicyRequest(subject_id=subject, action=PolicyAction.CREATE_CONTEXT))
        if not allowed.allowed:
            raise PermissionError('Owner access required')
        from app.context.service import validate_name
        validate_name(name)
        UUID(primary_domain_id)
        return await self.repository.create_space(subject, name, primary_domain_id)

    async def resume(self, subject, sort, domain, limit, after):
        from app.core.models import ContextSpacePage
        await self._allow(subject)
        if sort not in ('recent', 'used') or not 1 <= limit <= 100:
            raise ValueError('Invalid resume page')
        if domain not in (None, 'unclassified'):
            UUID(domain)
        ids = await self.repository.resume(subject, sort, domain, limit+1, after)
        items = tuple([await self.context.get_space(subject_id=subject, context_id=id) for id in ids[:limit]])
        return ContextSpacePage(items=items, next_after_id=items[-1].id if len(ids)>limit else None)
