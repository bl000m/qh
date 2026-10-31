"""Process-local connection pools owned by the FastAPI lifespan.

Reuse transport only: every lease gets a separate transaction and every query
retains its owner predicates. Different connection options never share a pool.
Standalone maintenance remains unpooled outside an application lifespan.
"""
from contextlib import contextmanager
from threading import RLock

import psycopg
from psycopg.rows import dict_row
from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg
from sqlalchemy.exc import TimeoutError as PoolTimeout
from sqlalchemy.pool import QueuePool

_lock = RLock()
_runtimes = {}


@contextmanager
def runtime_connections(url):
    with _lock:
        state = _runtimes.setdefault(url, dict(users=0, pools={}, closing=False))
        state['users'] += 1
    try:
        yield
    finally:
        with _lock:
            state['users'] -= 1
            if not state['users']:
                state['closing'] = True
                del _runtimes[url]
                for pool in state['pools'].values():
                    pool.dispose()


def _connect(url, kwargs):
    return psycopg.connect(host=url.host, port=url.port, dbname=url.database,
        user=url.username, password=url.password, connect_timeout=5,
        row_factory=dict_row, **kwargs)


def _pool(url, kwargs):
    # Preserve explicit autocommit maintenance semantics, outside pooled leases.
    if kwargs.get('autocommit'):
        return None
    with _lock:
        state = _runtimes.get(url)
        if state is None:
            return None
        key = tuple(sorted(kwargs.items()))
        if key not in state['pools']:
            state['pools'][key] = QueuePool(lambda: _connect(url, kwargs),
                pool_size=4, max_overflow=4, timeout=5, recycle=300,
                use_lifo=True, pre_ping=True, reset_on_return='rollback',
                dialect=PGDialect_psycopg(dbapi=psycopg))
        return state['pools'][key], state


@contextmanager
def connection(url, **kwargs):
    pooled = _pool(url, kwargs)
    if pooled is None:
        c = _connect(url, kwargs)
        try:
            with c:
                yield c
        finally:
            c.close()
        return
    pool, state = pooled
    try:
        lease = pool.connect()
    except PoolTimeout:
        raise psycopg.OperationalError('PostgreSQL connection unavailable') from None
    try:
        # pre_ping reconnects only before work begins. Never retry a transaction,
        # including when its commit outcome is uncertain.
        with lease.dbapi_connection.transaction():
            yield lease.dbapi_connection
    except BaseException:
        lease.invalidate()
        raise
    finally:
        if state['closing']:
            lease.invalidate()
        lease.close()
