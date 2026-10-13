"""Read-only identity/owner lookup. No runtime provisioning or migrations."""

from uuid import UUID

import psycopg
from sqlalchemy.engine import URL

from adapters.oidc import IdentityUnavailable
from app.core.models import ContextId, SubjectId


class PostgresSecurityReader:
    def __init__(self, *, url: URL) -> None:
        self._url = url

    async def _read(self, query: str, parameters: tuple):
        try:
            async with await psycopg.AsyncConnection.connect(
                host=self._url.host, port=self._url.port, dbname=self._url.database,
                user=self._url.username, password=self._url.password, connect_timeout=5,
            ) as connection:
                await connection.execute("SET statement_timeout = '5s'")
                cursor = await connection.execute(query, parameters)
                return await cursor.fetchone()
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
