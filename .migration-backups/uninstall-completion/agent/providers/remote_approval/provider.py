"""Compatibility wrapper for existing remote phone biometric approval."""

from collections.abc import Mapping
from typing import Any

from core.auth.base import AuthProvider
from core.auth.capabilities import ProviderCapabilities
from core.auth.errors import AuthenticationError
from core.auth.models import AuthContext, AuthResult, CredentialInfo


class RemoteApprovalProvider(AuthProvider):
    """Poll deployed phone-approval endpoints without claiming key-based proof."""

    _ROUTE_NAMES = {"face": "face", "fingerprint": "fingerprint"}
    _SUCCESS_STATUSES = frozenset({"completed", "verified"})

    def __init__(self, api_client: Any):
        self._api_client = api_client

    @property
    def provider_id(self) -> str:
        return "remote_approval"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(remote_approval=True)

    def is_available(self) -> bool:
        return True

    def register(self, context: AuthContext) -> CredentialInfo | None:
        return None

    def approval_url(self, context: AuthContext) -> str:
        approval_type = self._approval_type(context)
        if not context.session_id:
            raise AuthenticationError("Remote approval requires a backend session")
        return (
            f"{self._api_client.api_base}/agent/mobile/"
            f"{self._ROUTE_NAMES[approval_type]}/{context.session_id}/"
        )

    def authenticate(self, context: AuthContext) -> AuthResult:
        approval_type = self._approval_type(context)
        if not context.session_id:
            raise AuthenticationError("Remote approval requires a backend session")

        response = self._api_client.get_remote_approval_status(
            approval_type,
            context.session_id,
        )
        if isinstance(response, Mapping):
            status = str(response.get("status", ""))
            detail = response.get("detail")
        elif isinstance(response, str):
            status = response
            detail = None
        else:
            raise AuthenticationError("Remote approval backend returned an invalid response")

        metadata = {
            "approval_type": approval_type,
            "qr_url": self.approval_url(context),
        }
        if isinstance(detail, str):
            metadata["detail"] = detail
        return AuthResult(
            provider_id=self.provider_id,
            success=status in self._SUCCESS_STATUSES,
            status=status,
            metadata=metadata,
        )

    def get_credential_info(self) -> CredentialInfo | None:
        return None

    @classmethod
    def _approval_type(cls, context: AuthContext) -> str:
        approval_type = context.metadata.get("approval_type")
        if approval_type not in cls._ROUTE_NAMES:
            raise AuthenticationError("Remote approval type must be face or fingerprint")
        return str(approval_type)
