"""Policy-aware authentication-provider selection."""

from collections.abc import Iterable

from .base import AuthProvider
from .errors import (
    InvalidAuthenticationResultError,
    PolicyViolationError,
    ProviderUnavailableError,
)
from .models import AuthContext, AuthResult, AuthenticationPolicy


class AuthenticationManager:
    """Selects an available policy-compliant provider without OS dependencies."""

    def __init__(self, providers: Iterable[AuthProvider]):
        self._providers: dict[str, AuthProvider] = {}
        for provider in providers:
            if provider.provider_id in self._providers:
                raise ValueError(f"Duplicate authentication provider: {provider.provider_id}")
            self._providers[provider.provider_id] = provider

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(self._providers)

    def select_provider(
        self,
        policy: AuthenticationPolicy,
        requested_provider_id: str | None = None,
    ) -> AuthProvider:
        """Return the first available provider permitted by policy.

        Fallback is considered only when the policy explicitly allows it.
        """
        candidate_ids = self._candidate_ids(policy, requested_provider_id)
        unavailable_ids: list[str] = []
        strength_rejected_ids: list[str] = []

        for provider_id in candidate_ids:
            provider = self._providers.get(provider_id)
            if provider is None or not self._is_allowed(provider_id, policy):
                continue
            if not provider.capabilities.meets_minimum(policy.minimum_auth_strength):
                strength_rejected_ids.append(provider_id)
                continue
            if not provider.is_available():
                unavailable_ids.append(provider_id)
                continue
            return provider

        if strength_rejected_ids:
            raise PolicyViolationError(
                "No allowed provider meets the minimum authentication strength"
            )
        if unavailable_ids:
            raise ProviderUnavailableError("No policy-compliant provider is available")
        raise PolicyViolationError("No registered provider is permitted by policy")

    def authenticate(
        self,
        context: AuthContext,
        policy: AuthenticationPolicy,
        requested_provider_id: str | None = None,
    ) -> AuthResult:
        provider = self.select_provider(policy, requested_provider_id)
        result = provider.authenticate(context)
        if result.provider_id != provider.provider_id:
            raise InvalidAuthenticationResultError(
                "Provider result identity does not match selected provider"
            )
        return result

    def _candidate_ids(
        self,
        policy: AuthenticationPolicy,
        requested_provider_id: str | None,
    ) -> tuple[str, ...]:
        ordered = list(policy.authentication_priority)
        ordered.extend(
            provider_id for provider_id in self._providers if provider_id not in ordered
        )

        if requested_provider_id is None:
            if policy.allow_fallback:
                return tuple(ordered)
            return tuple(ordered[:1])
        if not policy.allow_fallback:
            return (requested_provider_id,)
        return tuple(
            [requested_provider_id]
            + [provider_id for provider_id in ordered if provider_id != requested_provider_id]
        )

    @staticmethod
    def _is_allowed(provider_id: str, policy: AuthenticationPolicy) -> bool:
        return (
            policy.allowed_provider_ids is None
            or provider_id in policy.allowed_provider_ids
        )
