"""Authentication provider contract.

Provider internals may differ, but providers never expose biometric templates or
private credentials through this interface.
"""

from abc import ABC, abstractmethod

from .capabilities import ProviderCapabilities
from .models import AuthContext, AuthResult, CredentialInfo


class AuthProvider(ABC):
    """An authenticator that returns normalized evidence to the agent core."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Stable server-recognized identifier for this provider."""

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Provider properties used for local eligibility decisions."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the provider can currently perform an interaction."""

    @abstractmethod
    def register(self, context: AuthContext) -> CredentialInfo | None:
        """Register provider credentials when a backend contract permits it."""

    @abstractmethod
    def authenticate(self, context: AuthContext) -> AuthResult:
        """Perform authentication and return a normalized result."""

    @abstractmethod
    def get_credential_info(self) -> CredentialInfo | None:
        """Return non-secret credential metadata, if present."""
