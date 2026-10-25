"""Durable, atomic guest authentication; owner and snapshot gates on every read."""
import asyncio
from datetime import datetime, timedelta, timezone
import hmac
import json
from uuid import uuid4

from adapters.postgres.canonical import CanonicalRepository
from app.core.models import GuestAccess
from app.projections.drafts import ProjectionNotFound, identifier
from app.projections.guest import CodeDelivery, GuestDenied, GuestSnapshot, GuestUnavailable


class PostgresGuestRepository:
    def __init__(self, *, url, clock=None):
        self.url = url
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _run(self, subject, operation):
        repository = CanonicalRepository(url=self.url, subject_id=subject or '',
            connection_options='-c statement_timeout=5000 -c lock_timeout=5000')
        try:
            with repository.connect() as c:
                return operation(repository, c, self.clock())
        except (ProjectionNotFound, GuestDenied, GuestUnavailable):
            raise
        except PermissionError:
            raise ProjectionNotFound('Projection not found') from None
        except Exception:
            raise GuestUnavailable('Guest access unavailable') from None

    @staticmethod
    def _invitation(c, token_hash, now):
        return c.execute('''
            SELECT i.*,s.policy->>'recipient_email' AS email,s.policy->'rights' AS rights,s.policy->>'provider' AS provider
            FROM guest_invitations i JOIN approved_snapshots s ON s.id=i.snapshot_id
            JOIN context_spaces cs ON cs.id=i.context_space_id JOIN users u ON u.id=cs.owner_id
            WHERE i.token_hash=%s AND i.revoked_at IS NULL AND i.expires_at>%s
                AND cs.status='active' AND u.status='active' FOR UPDATE OF i FOR SHARE OF cs,u
        ''', (token_hash, now)).fetchone()

    async def create(self, subject, scope, snapshot_id, token_hash):
        def insert(repository, c, now):
            repository._authorize(c, (scope,), lock=True)
            row = c.execute('SELECT policy FROM approved_snapshots WHERE id=%s AND context_space_id=%s',
                (snapshot_id, scope)).fetchone()
            if row is None:
                raise ProjectionNotFound('Projection not found')
            expiry = datetime.fromisoformat(row['policy']['expires_at'])
            if expiry <= now:
                raise GuestDenied('Vérification impossible.')
            created = c.execute('INSERT INTO guest_invitations (id,context_space_id,snapshot_id,token_hash,expires_at,created_at) '
                'VALUES (%s,%s,%s,%s,%s,%s) RETURNING id,expires_at',
                (str(uuid4()), scope, snapshot_id, token_hash, expiry, now)).fetchone()
            return dict(id=str(created['id']), expires_at=created['expires_at'])
        return await asyncio.to_thread(self._run, subject, insert)

    async def list(self, subject, scope):
        def read(repository, c, now):
            repository._authorize(c, (scope,), lock=True)
            rows = c.execute('SELECT i.id,i.snapshot_id,i.expires_at,i.revoked_at,i.created_at,'
                "s.policy->>'recipient_email' AS recipient_email,s.policy->'rights' AS rights "
                'FROM guest_invitations i JOIN approved_snapshots s ON s.id=i.snapshot_id '
                'WHERE i.context_space_id=%s ORDER BY i.created_at DESC,i.id LIMIT 101', (scope,)).fetchall()
            return dict(items=[{**row, 'id': str(row['id']), 'snapshot_id': str(row['snapshot_id'])}
                for row in rows[:100]], has_more=len(rows) > 100)
        return await asyncio.to_thread(self._run, subject, read)

    async def revoke(self, subject, scope, invitation_id):
        def update(repository, c, now):
            repository._authorize(c, (scope,), lock=True)
            row = c.execute('UPDATE guest_invitations SET revoked_at=COALESCE(revoked_at,%s) '
                'WHERE id=%s AND context_space_id=%s RETURNING id', (now, invitation_id, scope)).fetchone()
            if row is None:
                raise ProjectionNotFound('Projection not found')
        return await asyncio.to_thread(self._run, subject, update)

    async def limit(self, key_hash, maximum):
        def consume(repository, c, now):
            # This table is disposable throttling state, not canonical or audit history.
            c.execute("DELETE FROM guest_request_limits WHERE window_start<%s", (now-timedelta(hours=1),))
            row = c.execute('''
                INSERT INTO guest_request_limits VALUES (%s,%s,1)
                ON CONFLICT(key_hash) DO UPDATE SET
                    window_start=CASE WHEN guest_request_limits.window_start<=%s THEN %s ELSE guest_request_limits.window_start END,
                    requests=CASE WHEN guest_request_limits.window_start<=%s THEN 1 ELSE LEAST(guest_request_limits.requests+1,%s) END
                RETURNING requests
            ''', (key_hash, now, now-timedelta(minutes=1), now, now-timedelta(minutes=1), maximum+1)).fetchone()
            return row['requests'] <= maximum
        return await asyncio.to_thread(self._run, None, consume)

    async def issue(self, token_hash, email, challenge_id, code_hash):
        def insert(repository, c, now):
            row = self._invitation(c, token_hash, now)
            if (row is None or not isinstance(email, str) or email != row['email'] or row['send_count'] >= 3
                    or row['failed_verifications'] >= 10
                    or (row['last_sent_at'] and row['last_sent_at']+timedelta(seconds=60) > now)):
                return None
            c.execute('UPDATE guest_challenges SET invalidated_at=%s WHERE invitation_id=%s '
                'AND invalidated_at IS NULL AND used_at IS NULL', (now, row['id']))
            expiry = min(now+timedelta(minutes=5), row['expires_at'])
            c.execute('INSERT INTO guest_challenges (id,invitation_id,code_hash,expires_at,created_at) VALUES (%s,%s,%s,%s,%s)',
                (challenge_id, row['id'], code_hash, expiry, now))
            c.execute('UPDATE guest_invitations SET send_count=send_count+1,last_sent_at=%s WHERE id=%s', (now, row['id']))
            return CodeDelivery(challenge_id=challenge_id, recipient=row['email'], expires_at=expiry)
        return await asyncio.to_thread(self._run, None, insert)

    async def delivered(self, challenge_id, sent):
        def mark(repository, c, now):
            c.execute("UPDATE guest_challenges SET delivery_state=%s WHERE id=%s AND delivery_state='pending'",
                ('sent' if sent else 'failed', challenge_id))
        return await asyncio.to_thread(self._run, None, mark)

    async def verify(self, token_hash, challenge_id, code_hash, session_hash):
        def consume(repository, c, now):
            invite = self._invitation(c, token_hash, now)
            if invite is None or invite['failed_verifications'] >= 10:
                return None
            challenge = c.execute('SELECT * FROM guest_challenges WHERE id=%s AND invitation_id=%s FOR UPDATE',
                (challenge_id, invite['id'])).fetchone()
            if (challenge is None or challenge['used_at'] or challenge['invalidated_at'] or challenge['attempts'] >= 5
                    or challenge['expires_at'] <= now or challenge['delivery_state'] != 'sent'):
                return None
            if not hmac.compare_digest(challenge['code_hash'], code_hash):
                # Return a denial AFTER committing counters, never raise/rollback here.
                c.execute('UPDATE guest_challenges SET attempts=attempts+1 WHERE id=%s', (challenge_id,))
                c.execute('UPDATE guest_invitations SET failed_verifications=failed_verifications+1 WHERE id=%s', (invite['id'],))
                return None
            session_id = str(uuid4())
            expiry = min(now+timedelta(minutes=30), invite['expires_at'])
            c.execute('UPDATE guest_challenges SET used_at=%s WHERE id=%s', (now, challenge_id))
            c.execute('INSERT INTO guest_sessions (id,invitation_id,challenge_id,token_hash,expires_at,created_at) '
                'VALUES (%s,%s,%s,%s,%s,%s)', (session_id, invite['id'], challenge_id, session_hash, expiry, now))
            return GuestAccess(session_id=session_id, invitation_id=str(invite['id']), context_id=str(invite['context_space_id']),
                snapshot_id=str(invite['snapshot_id']), rights=tuple(invite['rights']), expires_at=expiry,provider=invite['provider'])
        return await asyncio.to_thread(self._run, None, consume)

    @staticmethod
    def _active(c, now, *, session_hash=None, session_id=None):
        row = c.execute('''
            SELECT g.id,g.invitation_id,g.expires_at,i.context_space_id,i.snapshot_id,s.policy->'rights' AS rights,s.policy->>'provider' AS provider
            FROM guest_sessions g JOIN guest_invitations i ON i.id=g.invitation_id
            JOIN approved_snapshots s ON s.id=i.snapshot_id
            JOIN context_spaces cs ON cs.id=i.context_space_id JOIN users u ON u.id=cs.owner_id
            WHERE '''+('g.token_hash=%s' if session_hash is not None else 'g.id=%s')+'''
                AND g.revoked_at IS NULL AND i.revoked_at IS NULL AND g.expires_at>%s AND i.expires_at>%s
                AND cs.status='active' AND u.status='active' FOR SHARE OF g,i,cs,u
        ''', (session_hash if session_hash is not None else session_id, now, now)).fetchone()
        if row is None:
            return None
        return GuestAccess(session_id=str(row['id']), invitation_id=str(row['invitation_id']),
            context_id=str(row['context_space_id']), snapshot_id=str(row['snapshot_id']), rights=tuple(row['rights']),
            expires_at=row['expires_at'],provider=row['provider'])

    async def authenticate(self, session_hash):
        return await asyncio.to_thread(self._run, None,
            lambda r, c, now: self._active(c, now, session_hash=session_hash))

    async def guest_for(self, session_id):
        identifier(session_id)
        return await asyncio.to_thread(self._run, None, lambda r, c, now: self._active(c, now, session_id=session_id))

    async def payload(self, grant, right):
        def read(repository, c, now):
            current = self._active(c, now, session_id=grant.session_id)
            if current != grant or right not in ('READ', 'ASK_AI') or right not in current.rights:
                raise GuestDenied('Vérification impossible.')
            # Session/invitation/owner locks fence revocation through this final safe read.
            row = c.execute('SELECT id,context_space_id,payload FROM approved_snapshots WHERE id=%s AND context_space_id=%s',
                (current.snapshot_id, current.context_id)).fetchone()
            return GuestSnapshot(context_id=str(row['context_space_id']), snapshot_id=str(row['id']),
                payload_json=json.dumps(row['payload'],ensure_ascii=False,sort_keys=True))
        return await asyncio.to_thread(self._run, None, read)

    async def logout(self, session_hash):
        def revoke(repository, c, now):
            c.execute('UPDATE guest_sessions SET revoked_at=COALESCE(revoked_at,%s) WHERE token_hash=%s', (now, session_hash))
        return await asyncio.to_thread(self._run, None, revoke)
