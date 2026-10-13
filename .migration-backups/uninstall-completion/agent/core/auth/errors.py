"""Explicit errors emitted by the authentication core."""


class AuthenticationError(Exception):
    """Base class for normalized authentication failures."""


class ProviderUnavailableError(AuthenticationError):
    """No permitted provider is currently available."""


class ProviderCancelledError(AuthenticationError):
    """The user cancelled a provider interaction."""


class PolicyViolationError(AuthenticationError):
    """A requested provider cannot meet the applicable policy."""


class InvalidAuthenticationResultError(AuthenticationError):
    """A provider returned a result inconsistent with its identity."""
