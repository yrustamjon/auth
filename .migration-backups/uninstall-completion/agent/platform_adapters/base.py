"""OS-integration contract kept separate from authentication providers."""

from abc import ABC, abstractmethod
from typing import Any, Mapping

from storage.base import SecureStorage


class PlatformAdapter(ABC):
    """Operations supplied by an operating system, not by an authenticator."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Stable name for the operating system integration."""

    @abstractmethod
    def lock_session(self) -> None:
        """Display or request the platform-specific locked state."""

    @abstractmethod
    def unlock_session(self) -> None:
        """Release the platform-specific agent lock UI after authentication."""

    @abstractmethod
    def get_device_metadata(self) -> Mapping[str, Any]:
        """Return non-secret platform/device metadata."""

    @abstractmethod
    def start_service(self) -> None:
        """Start the platform event integration used by this application."""

    @abstractmethod
    def secure_storage(self) -> SecureStorage:
        """Return the platform secure-storage implementation."""

    def start_autolock(self, timeout, on_warn, on_lock) -> None:
        """Start OS-specific idle monitoring."""
        raise NotImplementedError

    def stop_autolock(self) -> None:
        raise NotImplementedError

    def disable_session(self) -> None:
        """Release agent UI for an authorized disable command."""
        raise NotImplementedError

    def restart_agent(self) -> None:
        raise NotImplementedError
