"""Metadata only on existing canonical tables; owner predicates fence stale policy reads."""

from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from sqlalchemy.engine import URL

from app.core.models import ContextId, ContextSpace, ContextStorageUnavailable, SubjectId

FIELDS = "cs.id, cs.owner_id, cs.name, cs.status, cs.created_at, cs.updated_at"


def space(row):
    return ContextSpace(**dict(row, id=ContextId(str(row["id"])), owner_id=SubjectId(str(row["owner_id"]))))


class PostgresContextSpaceRepository:
    def __init__(self, *, url: URL):
        self._url = url

    async def _execute(self, query, parameters, *, many=False):
        try:
            async with await psycopg.AsyncConnection.connect(
                host=self._url.host, port=self._url.port, dbname=self._url.database,
                user=self._url.username, password=self._url.password, connect_timeout=5,
                row_factory=dict_row,
            ) as connection:
                await connection.execute("SET statement_timeout = '5s'")
                cursor = await connection.execute(query, parameters)
                return await cursor.fetchall() if many else await cursor.fetchone()
        except psycopg.Error:
            raise ContextStorageUnavailable("Context storage unavailable") from None

    async def create(self, *, subject_id, name):
        row = await self._execute(
            "INSERT INTO context_spaces AS cs (id,owner_id,name) "
            "SELECT %s,u.id,%s FROM users u WHERE u.id=%s AND u.status='active' "
            "RETURNING " + FIELDS, (uuid4(), name, UUID(subject_id)),
        )
        if row is None:
            raise PermissionError("Access denied")
        return space(row)

    async def list_ids(self, *, subject_id, limit, after_id):
        after = UUID(after_id) if after_id is not None else None
        rows = await self._execute(
            "SELECT cs.id FROM context_spaces cs JOIN users u ON u.id=cs.owner_id "
            "WHERE cs.owner_id=%s AND cs.status='active' AND u.status='active' "
            "AND (%s::uuid IS NULL OR cs.id>%s::uuid) ORDER BY cs.id LIMIT %s",
            (UUID(subject_id), after, after, limit), many=True,
        )
        return tuple(ContextId(str(row["id"])) for row in rows)

    async def read(self, *, subject_id, context_id):
        row = await self._execute(
            "SELECT " + FIELDS + " FROM context_spaces cs JOIN users u ON u.id=cs.owner_id "
            "WHERE cs.id=%s AND cs.owner_id=%s AND cs.status='active' AND u.status='active'",
            (UUID(context_id), UUID(subject_id)),
        )
        return space(row) if row else None

    async def rename(self, *, subject_id, context_id, name):
        row = await self._execute(
            "UPDATE context_spaces AS cs SET name=%s,updated_at=clock_timestamp() "
            "FROM users u WHERE cs.id=%s AND cs.owner_id=%s AND u.id=cs.owner_id "
            "AND cs.status='active' AND u.status='active' RETURNING " + FIELDS,
            (name, UUID(context_id), UUID(subject_id)),
        )
        return space(row) if row else None
