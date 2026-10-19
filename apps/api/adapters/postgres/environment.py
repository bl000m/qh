"""One versioned organization document per active authenticated owner."""
import asyncio

import psycopg
from psycopg.types.json import Jsonb

from adapters.postgres.canonical import CanonicalRepository
from app.core.models import ContextStorageUnavailable
from app.environment.service import OrganizationConflict, defaults


class PostgresOrganizationRepository:
    def __init__(self, *, url):
        self.url = url

    def _operation(self, subject, document=None):
        repo = CanonicalRepository(url=self.url, subject_id=subject,
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')
        try:
            with repo.connect() as c:
                # Also serializes the initial insert (there is no document row yet).
                if not c.execute("SELECT id FROM users WHERE id=%s AND status='active' FOR UPDATE", (subject,)).fetchone():
                    raise PermissionError('Owner access required')
                row = c.execute('SELECT version,document FROM owner_organization WHERE owner_id=%s', (subject,)).fetchone()
                current = dict(row['document'], version=row['version']) if row else defaults()
                if document is None:
                    if current['memberships']:
                        repo._authorize(c, current['memberships'], lock=True)
                    return current
                if document['version'] != current['version']:
                    raise OrganizationConflict('Organization changed; reload before editing')
                if document['memberships']:
                    repo._authorize(c, document['memberships'], lock=True)
                version = current['version'] + 1
                body = {k: document[k] for k in ('domains', 'memberships')}
                c.execute('INSERT INTO owner_organization(owner_id,version,document) VALUES (%s,%s,%s) '
                          'ON CONFLICT(owner_id) DO UPDATE SET version=EXCLUDED.version,document=EXCLUDED.document',
                          (subject, version, Jsonb(body)))
                return dict(body, version=version)
        except psycopg.Error:
            raise ContextStorageUnavailable('Organization unavailable') from None

    async def read(self, subject):
        return await asyncio.to_thread(self._operation, subject)

    async def replace(self, subject, document):
        return await asyncio.to_thread(self._operation, subject, document)
