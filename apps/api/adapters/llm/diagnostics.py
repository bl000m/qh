"""Private one-hour diagnostics, never prompts, headers, logs or canonical data."""
import fcntl
import json
import os
from pathlib import Path
import time
from uuid import UUID, uuid4


class PrivateDiagnostics:
    retention = 3600
    max_records = 100
    max_bytes = 1_048_576

    def __init__(self, path, *, clock=time.time):
        self.path, self.clock = Path(path), clock
        self.path.mkdir(mode=0o700, exist_ok=True)
        if self.path.is_symlink() or self.path.stat().st_mode & 0o077:
            raise ValueError('Private diagnostics directory required')
        self.purge_expired()

    def _locked(self, operation):
        fd = os.open(self.path / '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            now = self.clock()
            # A process crash can leave a private atomic-write temporary file.
            for orphan in self.path.glob('*.tmp'):
                orphan.unlink()  # Exclusive directory lock: no active writer here.
            for path in self.path.glob('*.json'):
                value = self._read(path)
                if value['expires_at'] <= now:
                    path.unlink()
            return operation()

    def _read(self, path):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            if os.fstat(stream.fileno()).st_mode & 0o077:
                raise ValueError('Private diagnostic record required')
            return json.load(stream)

    def _write(self, value):
        data = json.dumps(value, ensure_ascii=False).encode()
        if len(data) > self.max_bytes:
            raise ValueError('Diagnostic response exceeds private storage bound')
        target = self.path / (value['id'] + '.json')
        temp = self.path / (value['id'] + '.tmp')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)

    def purge_expired(self):
        self._locked(lambda: None)

    def begin(self, *, subject, scope, kind):
        def create():
            if len(list(self.path.glob('*.json'))) >= self.max_records:
                raise ValueError('Private diagnostics capacity reached; delete records before sending')
            now = self.clock()
            value = dict(id=str(uuid4()), subject=subject, context_id=scope, kind=kind,
                created_at=now, expires_at=now+self.retention, outcome='in_progress',
                checks=[], raw_response=None, accounting=None)
            self._write(value)
            return value['id']
        return self._locked(create)

    def update(self, identity, **fields):
        def save():
            path = self.path / (str(UUID(identity)) + '.json')
            if path.exists():
                value = self._read(path)
                value.update(fields)
                self._write(value)
        return self._locked(save)

    def check(self, identity, rule, passed, reason=None):
        def save():
            path = self.path / (str(UUID(identity)) + '.json')
            if path.exists():
                value = self._read(path)
                value['checks'].append(dict(rule=rule, result='PASS' if passed else 'FAIL', reason=reason))
                self._write(value)
        return self._locked(save)

    def records(self, *, subject, scope):
        return self._locked(lambda: sorted(
            [v for p in self.path.glob('*.json') if
             (v := self._read(p))['subject'] == subject and v['context_id'] == scope],
            key=lambda v: v['created_at'], reverse=True))

    def delete(self, *, subject, scope, identity):
        def remove():
            path = self.path / (str(UUID(identity)) + '.json')
            if path.exists():
                value = self._read(path)
                if value['subject'] == subject and value['context_id'] == scope:
                    path.unlink()
        self._locked(remove)


class DiagnosticCall:
    """Request-local observer. No shared last_exchange or raw exception messages."""
    def __init__(self, store, subject, scope, kind):
        self.store, self.subject, self.scope, self.kind = store, subject, scope, kind
        self.identity = None
        self.pending_checks = []

    def begin(self):
        self.identity = self.store.begin(subject=self.subject, scope=self.scope, kind=self.kind)
        for rule, passed, reason in self.pending_checks:
            self.check(rule, passed, reason)
        self.pending_checks.clear()

    def check(self, rule, passed, reason=None):
        if self.identity:
            self.store.check(self.identity, rule, passed, reason)
        else:
            self.pending_checks.append((rule, passed, reason))

    def capture(self, raw):
        if not self.identity:
            return
        # Never persist request/system prompt, credentials or provider headers.
        exchange = raw.last_exchange or {}
        response = exchange.get('response')
        text = json.dumps(response, ensure_ascii=False)
        redacted = bool(raw._key and raw._key in text)
        if redacted:
            response = json.loads(text.replace(raw._key, '[REDACTED]'))
        index = getattr(raw, 'last_attempt', None)
        row = raw.budget.read(lambda s: s['calls'][index]) if index is not None else None
        self.store.update(self.identity, raw_response=response, secret_redacted=redacted,
            attempt_index=index, accounting=row, http_status=exchange.get('http_status',
                (raw.last_failure or {}).get('http_status')), latency_seconds=exchange.get('latency_seconds'))

    def finish(self, outcome, phase):
        if self.identity:
            self.store.update(self.identity, outcome=outcome, phase=phase)
