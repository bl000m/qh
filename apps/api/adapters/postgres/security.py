"""Read-only identity/owner lookup. No runtime provisioning or migrations."""

from uuid import UUID
import asyncio

import psycopg
from sqlalchemy.engine import URL
from psycopg.rows import tuple_row
from adapters.postgres.connections import connection

from adapters.oidc import IdentityUnavailable
from app.core.models import ContextId, SubjectId


class PostgresSecurityReader:
    def __init__(self, *, url: URL) -> None:
        self._url = url

    async def _read(self, query: str, parameters: tuple):
        return await asyncio.to_thread(self._read_on, query, parameters)

    def _read_on(self, query, parameters):
        try:
            with connection(self._url) as c:
                c.execute("SET LOCAL statement_timeout = '5s'")
                with c.cursor(row_factory=tuple_row) as cursor:
                    cursor.execute(query, parameters)
                    return cursor.fetchone()
        except psycopg.Error:
            raise IdentityUnavailable("Identity storage unavailable") from None

    async def resolve_identity(self, issuer: str, subject: str) -> SubjectId | None:
        row = await self._read(
            "SELECT u.id FROM user_identities i JOIN users u ON u.id=i.user_id "
            "WHERE i.issuer=%s AND i.subject=%s AND u.status='active'", (issuer, subject),
        )
        return SubjectId(str(row[0])) if row else None

    async def owner_for(self, context_id: ContextId) -> SubjectId | None:
        try:
            value = UUID(context_id)
        except ValueError:
            return None
        row = await self._read(
            "SELECT cs.owner_id FROM context_spaces cs JOIN users u ON u.id=cs.owner_id "
            "WHERE cs.id=%s AND cs.status='active' AND u.status='active'", (value,),
        )
        return SubjectId(str(row[0])) if row else None
