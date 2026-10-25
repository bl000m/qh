"""CSPRNG proofs and private keyed OTP verifiers; no token/code logging."""
import hashlib
import hmac
import secrets


class SecureGuestProofs:
    def __init__(self, pepper):
        if not isinstance(pepper, bytes) or len(pepper) < 32:
            raise ValueError('Private guest verifier key must contain at least 32 bytes')
        self._pepper = pepper

    def token(self):
        return secrets.token_urlsafe(32)

    def code(self):
        return f'{secrets.randbelow(100000000):08d}'

    def token_hash(self, token, kind):
        if kind not in ('invitation', 'session') or not isinstance(token, str) or len(token) > 256:
            raise ValueError('Bounded guest proof required')
        return hashlib.sha256((kind+':'+token).encode()).hexdigest()

    def code_hash(self, token_hash, challenge_id, code):
        if not isinstance(code, str) or len(code) > 64:
            raise ValueError('Bounded verification code required')
        return hmac.new(self._pepper, ('code:'+token_hash+':'+challenge_id+':'+code).encode(), hashlib.sha256).hexdigest()

    def peer_hash(self, peer, phase):
        return hmac.new(self._pepper, ('peer:'+phase+':'+peer).encode(), hashlib.sha256).hexdigest()
