"""Essential pool checks on a newly created disposable PostgreSQL database."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import psycopg
import pytest

from adapters.postgres.config import database_url
from adapters.postgres.connections import connection, runtime_connections
from tests.test_migrations import connect, empty_database as empty_database
from tests.test_native_semantics_sql import dedicated_server_only as dedicated_server_only


@pytest.fixture
def pool_database(empty_database):
    url = database_url()
    with connection(url) as c:
        c.execute('CREATE TABLE pool_entries(id integer PRIMARY KEY, value integer '
                  'UNIQUE DEFERRABLE INITIALLY DEFERRED)')
    yield url


def test_reuse_commit_rollback_and_commit_failure_release(pool_database):
    url = pool_database
    with runtime_connections(url):
        with connection(url) as first:
            pid = first.info.backend_pid
            first.execute('INSERT INTO pool_entries VALUES (1,10)')
            first.execute("SET LOCAL application_name='pool-local'")
        with connection(url) as reused:
            assert reused.info.backend_pid == pid
            assert reused.execute('SELECT count(*) AS n FROM pool_entries').fetchone()['n'] == 1
            assert reused.execute('SHOW application_name').fetchone()['application_name'] != 'pool-local'
        with pytest.raises(ValueError):
            with connection(url) as rolled_back:
                rolled_back.execute('INSERT INTO pool_entries VALUES (2,20)')
                raise ValueError('Offline rollback')
        assert rolled_back.closed
        with pytest.raises(psycopg.errors.UniqueViolation):
            with connection(url) as failed_commit:
                failed_commit.execute('INSERT INTO pool_entries VALUES (3,10)')
        assert failed_commit.closed
        with connection(url) as recovered:
            assert recovered.execute('SELECT count(*) AS n FROM pool_entries').fetchone()['n'] == 1
        assert not recovered.closed
    assert recovered.closed


def test_concurrent_leases_do_not_share_transactions_or_local_settings(pool_database):
    barrier = Barrier(2)

    def work(value):
        with connection(pool_database) as c:
            c.execute("SELECT set_config('application_name',%s,true)", (str(value),))
            c.execute('INSERT INTO pool_entries VALUES (%s,%s)', (value, value))
            barrier.wait(timeout=5)
            assert c.execute('SELECT count(*) AS n FROM pool_entries').fetchone()['n'] == 1
            assert c.execute('SHOW application_name').fetchone()['application_name'] == str(value)
            barrier.wait(timeout=5)
            return c.info.backend_pid

    with runtime_connections(pool_database):
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert len(set(executor.map(work, (1, 2)))) == 2
        with connection(pool_database) as c:
            assert c.execute('SELECT count(*) AS n FROM pool_entries').fetchone()['n'] == 2


def test_broken_idle_connection_is_replaced_before_next_transaction(pool_database):
    with runtime_connections(pool_database):
        with connection(pool_database) as stale:
            pid = stale.info.backend_pid
            stale.execute('SELECT 1')
        with connect() as admin:
            assert admin.execute('SELECT pg_terminate_backend(%s)', (pid,)).fetchone()[0]
        with connection(pool_database) as healthy:
            assert healthy.info.backend_pid != pid
            assert healthy.execute('SELECT 1 AS n').fetchone()['n'] == 1
        assert stale.closed


def test_lifespan_cleanup_options_and_outstanding_lease(pool_database):
    url = pool_database
    with pytest.raises(RuntimeError, match='startup'):
        with runtime_connections(url):
            with runtime_connections(url):
                with connection(url) as ordinary:
                    pid = ordinary.info.backend_pid
                with connection(url, options='-c statement_timeout=5000 -c lock_timeout=5000') as bounded:
                    assert bounded.info.backend_pid != pid
                    assert bounded.execute('SHOW statement_timeout').fetchone()['statement_timeout'] == '5s'
            assert not ordinary.closed and not bounded.closed
            raise RuntimeError('startup')
    assert ordinary.closed and bounded.closed
    lifetime = runtime_connections(url)
    lifetime.__enter__()
    lease = connection(url)
    outstanding = lease.__enter__()
    try:
        lifetime.__exit__(None, None, None)
        assert not outstanding.closed
        outstanding.execute('INSERT INTO pool_entries VALUES (1,1)')
    finally:
        lease.__exit__(None, None, None)
    assert outstanding.closed
    with connection(url) as unpooled:
        assert unpooled.execute('SELECT count(*) AS n FROM pool_entries').fetchone()['n'] == 1
    assert unpooled.closed
