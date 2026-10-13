import unittest

from core.auth.base import AuthProvider
from core.auth.capabilities import AuthenticationStrength, ProviderCapabilities
from core.auth.errors import PolicyViolationError, ProviderUnavailableError
from core.auth.manager import AuthenticationManager
from core.auth.models import AuthContext, AuthResult, AuthenticationPolicy


class FakeProvider(AuthProvider):
    def __init__(
        self,
        provider_id: str,
        capabilities: ProviderCapabilities,
        *,
        available: bool = True,
    ):
        self._provider_id = provider_id
        self._capabilities = capabilities
        self.available = available

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def is_available(self) -> bool:
        return self.available

    def register(self, context: AuthContext) -> None:
        return None

    def authenticate(self, context: AuthContext) -> AuthResult:
        return AuthResult(
            provider_id=self.provider_id,
            success=True,
            status="verified",
        )

    def get_credential_info(self):
        return None


HARDWARE_CAPABILITIES = ProviderCapabilities(
    hardware_backed=True,
    phishing_resistant=True,
    biometric=True,
    user_verification=True,
    offline_capable=True,
)
FACE_CAPABILITIES = ProviderCapabilities(
    biometric=True,
    user_verification=True,
)


class AuthenticationManagerTests(unittest.TestCase):
    def setUp(self):
        self.hardware = FakeProvider("hardware", HARDWARE_CAPABILITIES)
        self.face = FakeProvider("face", FACE_CAPABILITIES)
        self.manager = AuthenticationManager([self.face, self.hardware])
        self.context = AuthContext(device_id="device-1", session_id="session-1")

    def test_selects_highest_priority_allowed_provider(self):
        """Would fail if registration order could override backend priority."""
        policy = AuthenticationPolicy(
            allowed_provider_ids=frozenset({"face", "hardware"}),
            authentication_priority=("hardware", "face"),
        )

        result = self.manager.authenticate(self.context, policy)

        self.assertEqual(result.provider_id, "hardware")
        self.assertTrue(result.success)

    def test_skips_unavailable_provider_when_policy_allows_fallback(self):
        """Would fail if an unavailable strong provider prevented approved fallback."""
        self.hardware.available = False
        policy = AuthenticationPolicy(
            allowed_provider_ids=frozenset({"face", "hardware"}),
            authentication_priority=("hardware", "face"),
            allow_fallback=True,
        )

        result = self.manager.authenticate(self.context, policy)

        self.assertEqual(result.provider_id, "face")

    def test_refuses_fallback_when_policy_disallows_it(self):
        """Would fail if an attacker could force an unapproved provider downgrade."""
        self.hardware.available = False
        policy = AuthenticationPolicy(
            allowed_provider_ids=frozenset({"face", "hardware"}),
            authentication_priority=("hardware", "face"),
            allow_fallback=False,
        )

        with self.assertRaises(ProviderUnavailableError):
            self.manager.authenticate(self.context, policy)

    def test_rejects_provider_below_minimum_authentication_strength(self):
        """Would fail if biometric face auth satisfied a hardware-backed policy."""
        policy = AuthenticationPolicy(
            allowed_provider_ids=frozenset({"face"}),
            authentication_priority=("face",),
            minimum_auth_strength=AuthenticationStrength.HARDWARE_BACKED,
        )

        with self.assertRaises(PolicyViolationError):
            self.manager.authenticate(self.context, policy)


if __name__ == "__main__":
    unittest.main()
