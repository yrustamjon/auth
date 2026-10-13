"""Strict, non-privileged protocol for an authenticated local pipe connection."""
from dataclasses import dataclass
import json
import re
import threading

from services.authorization import IdentityMismatchError, SessionAuthority

MAX_FRAME_BYTES = 64 * 1024
MAX_REQUESTS_PER_CONNECTION = 256
COMMANDS = frozenset({"status", "begin_attempt", "cancel_attempt"})


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class PeerIdentity:
    session_id: int
    user_sid: str


@dataclass(frozen=True)
class Request:
    request_id: str
    command: str
    session_id: int
    user_sid: str
    generation: str
    attempt_id: str | None = None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("INVALID_REQUEST")
        result[key] = value
    return result


def decode_request(data: bytes) -> Request:
    if not isinstance(data, bytes) or not data or len(data) > MAX_FRAME_BYTES:
        raise ProtocolError("INVALID_FRAME")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ProtocolError("INVALID_REQUEST") from error
    required = {"version", "request_id", "command", "session_id", "user_sid", "generation"}
    if not isinstance(value, dict) or not required <= value.keys():
        raise ProtocolError("INVALID_REQUEST")
    command = value["command"]
    if not isinstance(command, str) or command not in COMMANDS:
        raise ProtocolError("UNSUPPORTED_COMMAND")
    fields = required | ({"attempt_id"} if command == "cancel_attempt" else set())
    if value.keys() != fields or type(value["version"]) is not int or value["version"] != 1:
        raise ProtocolError("INVALID_REQUEST")
    if type(value["session_id"]) is not int or not 0 < value["session_id"] < 2**32:
        raise ProtocolError("INVALID_REQUEST")
    if not isinstance(value["user_sid"], str) or not re.fullmatch(r"S-1-(?:\d+-)*\d+", value["user_sid"]) or len(value["user_sid"]) > 184:
        raise ProtocolError("INVALID_REQUEST")
    for name, limit in (("request_id", 64), ("generation", 128), ("attempt_id", 128)):
        if name in value and (not isinstance(value[name], str) or
                             not re.fullmatch(r"[A-Za-z0-9_-]{1," + str(limit) + r"}", value[name])):
            raise ProtocolError("INVALID_REQUEST")
    return Request(value["request_id"], command, value["session_id"], value["user_sid"],
                   value["generation"], value.get("attempt_id"))


class RequestHistory:
    """Never evict accepted IDs; require reconnect after a bounded number."""
    def __init__(self):
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def consume(self, request_id: str) -> str | None:
        with self._lock:
            if request_id in self._seen:
                return "REPLAYED_REQUEST"
            if len(self._seen) >= MAX_REQUESTS_PER_CONNECTION:
                return "CONNECTION_LIMIT"
            self._seen.add(request_id)
            return None


def dispatch_request(request: Request, peer: PeerIdentity, authority: SessionAuthority,
                     history: RequestHistory) -> dict:
    def reject(code):
        return {"ok": False, "request_id": request.request_id, "error": code}
    if (peer.session_id <= 0 or request.session_id != peer.session_id or
            request.user_sid != peer.user_sid):
        return reject("IDENTITY_MISMATCH")
    if request.generation != authority.generation:
        return reject("STALE_GENERATION")
    error = history.consume(request.request_id)
    if error:
        return reject(error)
    current = authority.snapshot(peer.session_id)
    if current.user_sid is not None and current.user_sid != peer.user_sid:
        return reject("IDENTITY_MISMATCH")
    try:
        if request.command == "begin_attempt":
            authority.begin_attempt(peer.session_id, peer.user_sid)
        elif request.command == "cancel_attempt":
            if not authority.cancel_attempt(peer.session_id, peer.user_sid, request.attempt_id):
                return reject("STALE_ATTEMPT")
        elif request.command != "status":
            return reject("UNSUPPORTED_COMMAND")
    except IdentityMismatchError:
        return reject("IDENTITY_MISMATCH")
    result = authority.snapshot(peer.session_id)
    return {"ok": True, "request_id": request.request_id, "generation": result.generation,
            "state": result.state, "attempt_id": result.attempt_id}
