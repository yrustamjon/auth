"""Typed values exchanged by providers and the authentication core."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .capabilities import AuthenticationStrength


@dataclass(frozen=True)
class AuthChallenge:
    """Future backend-issued challenge. Phase 2 does not create one locally."""

    challenge_id: str
    value: str
    expires_at: datetime
    allowed_provider_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthContext:
    """Non-secret context supplied by orchestration to a provider."""

    device_id: str
    user_id: str | None = None
    session_id: str | None = None
    challenge: AuthChallenge | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthResult:
    """Provider-neutral authentication result; assertion contents stay opaque."""

    provider_id: str
    success: bool
    status: str
    credential_id: str | None = None
    assertion: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CredentialInfo:
    """Non-secret credential metadata, if a provider has registered one."""

    provider_id: str
    credential_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthenticationPolicy:
    """Locally applied subset of backend policy used to prevent downgrade."""

    allowed_provider_ids: frozenset[str] | None = None
    authentication_priority: tuple[str, ...] = ()
    minimum_auth_strength: AuthenticationStrength = AuthenticationStrength.BASIC
    allow_fallback: bool = False
