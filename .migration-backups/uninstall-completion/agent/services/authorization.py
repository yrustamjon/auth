"""Fail-closed session bookkeeping; this foundation cannot issue access grants.

No OS enforcement or biometric proof verification is implemented here yet.
"""
from dataclasses import dataclass
import secrets
import threading


class IdentityMismatchError(ValueError):
    """A session is already bound to another Windows identity."""


@dataclass(frozen=True)
class Attempt:
    session_id: int
    user_sid: str
    attempt_id: str
    generation: str


@dataclass(frozen=True)
class SessionSnapshot:
    session_id: int
    user_sid: str | None
    attempt_id: str | None
    generation: str
    state: str = "MFA_PENDING"


class SessionAuthority:
    def __init__(self, generation: str):
        if not isinstance(generation, str) or not generation or len(generation) > 128:
            raise ValueError("Invalid service generation")
        self.generation = generation
        self._attempts: dict[int, Attempt] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _validate_session(session_id):
        if type(session_id) is not int or session_id <= 0:
            raise ValueError("An interactive Windows session is required")

    def begin_attempt(self, session_id: int, user_sid: str) -> Attempt:
        self._validate_session(session_id)
        if not isinstance(user_sid, str) or not user_sid.startswith("S-1-") or len(user_sid) > 184:
            raise ValueError("Invalid user SID")
        with self._lock:
            previous = self._attempts.get(session_id)
            if previous and previous.user_sid != user_sid:
                raise IdentityMismatchError("Session identity changed")
            attempt = Attempt(session_id, user_sid, secrets.token_hex(32), self.generation)
            self._attempts[session_id] = attempt
            return attempt

    def invalidate_session(self, session_id: int) -> None:
        self._validate_session(session_id)
        with self._lock:
            self._attempts.pop(session_id, None)

    def snapshot(self, session_id: int) -> SessionSnapshot:
        self._validate_session(session_id)
        with self._lock:
            attempt = self._attempts.get(session_id)
            return SessionSnapshot(session_id, attempt.user_sid if attempt else None,
                                   attempt.attempt_id if attempt else None, self.generation)

    def cancel_attempt(self, session_id: int, user_sid: str, attempt_id: str) -> bool:
        """Atomically cancel only the caller's current attempt."""
        self._validate_session(session_id)
        with self._lock:
            current = self._attempts.get(session_id)
            if not current or current.user_sid != user_sid or current.attempt_id != attempt_id:
                return False
            del self._attempts[session_id]
            return True
