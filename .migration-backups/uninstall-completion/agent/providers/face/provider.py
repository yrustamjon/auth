"""Compatibility wrapper for the deployed webcam face-verification flow."""

from collections.abc import Mapping
from typing import Any

from core.auth.base import AuthProvider
from core.auth.capabilities import ProviderCapabilities
from core.auth.errors import AuthenticationError
from core.auth.models import AuthContext, AuthResult, CredentialInfo


class BioGuardFaceProvider(AuthProvider):
    """Submit the existing camera frame to the existing backend endpoint.

    This provider does not claim liveness detection, hardware backing, or
    phishing resistance. It simply normalizes the deployed backend response.
    """

    def __init__(self, api_client: Any):
        self._api_client = api_client

    @property
    def provider_id(self) -> str:
        return "bioguard_face"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(biometric=True)

    def is_available(self) -> bool:
        # The existing UI performs a camera availability check before capture.
        return True

    def register(self, context: AuthContext) -> CredentialInfo | None:
        return None

    def authenticate(self, context: AuthContext) -> AuthResult:
        image = context.metadata.get("image")
        if not isinstance(image, str) or not image:
            raise AuthenticationError("Webcam face authentication requires an image")
        if not context.user_id:
            raise AuthenticationError("Webcam face authentication requires a username")

        response = self._api_client.check_face(
            session_id=context.session_id,
            username=context.user_id,
            device_id=context.device_id,
            image=image,
        )
        if not isinstance(response, Mapping):
            raise AuthenticationError("Face backend returned an invalid response")

        status = str(response.get("status", ""))
        detail = response.get("detail")
        metadata = {"detail": detail} if isinstance(detail, str) else {}
        return AuthResult(
            provider_id=self.provider_id,
            success=status == "verified",
            status=status,
            metadata=metadata,
        )

    def get_credential_info(self) -> CredentialInfo | None:
        return None
