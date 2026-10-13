"""Provider security metadata used for local policy selection only."""

from dataclasses import dataclass
from enum import IntEnum


class AuthenticationStrength(IntEnum):
    """Coarse local selection levels; backend verification remains authoritative."""

    BASIC = 0
    BIOMETRIC = 1
    HARDWARE_BACKED = 2


@dataclass(frozen=True)
class ProviderCapabilities:
    """Claims a provider can make without exposing provider secrets to the core."""

    hardware_backed: bool = False
    phishing_resistant: bool = False
    biometric: bool = False
    user_verification: bool = False
    offline_capable: bool = False
    remote_approval: bool = False

    @property
    def authentication_strength(self) -> AuthenticationStrength:
        if self.hardware_backed:
            return AuthenticationStrength.HARDWARE_BACKED
        if self.biometric and self.user_verification:
            return AuthenticationStrength.BIOMETRIC
        return AuthenticationStrength.BASIC

    def meets_minimum(self, minimum: AuthenticationStrength) -> bool:
        return self.authentication_strength >= minimum
