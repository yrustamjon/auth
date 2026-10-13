"""Operating-system-independent authentication contracts and orchestration."""

from .base import AuthProvider
from .capabilities import AuthenticationStrength, ProviderCapabilities
from .manager import AuthenticationManager
from .models import AuthContext, AuthResult, AuthenticationPolicy

__all__ = [
    "AuthContext",
    "AuthenticationManager",
    "AuthenticationPolicy",
    "AuthenticationStrength",
    "AuthProvider",
    "AuthResult",
    "ProviderCapabilities",
]
