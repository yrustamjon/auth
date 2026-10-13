"""Typed values used by the backend client without backend implementation."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class BackendRequest:
    """A request description useful for tests and future audit integration."""

    method: str
    path: str
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class BackendResponse:
    """Normalized non-secret response metadata."""

    status_code: int | None
    payload: Mapping[str, Any] = field(default_factory=dict)
