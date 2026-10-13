"""Operating-system-independent secure storage contract."""

from abc import ABC, abstractmethod


class SecureStorageError(Exception):
    """Raised when a platform secure-storage operation cannot complete."""


class SecureStorage(ABC):
    """Store opaque bytes without exposing a filesystem storage mechanism."""

    @abstractmethod
    def set_secret(self, key: str, value: bytes) -> None:
        """Persist a secret value for this user/device context."""

    @abstractmethod
    def get_secret(self, key: str) -> bytes | None:
        """Return a secret or ``None`` when no value exists."""

    @abstractmethod
    def delete_secret(self, key: str) -> None:
        """Remove a secret value if it exists."""
