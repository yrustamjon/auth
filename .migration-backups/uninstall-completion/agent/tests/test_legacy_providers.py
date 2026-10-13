import unittest

from core.auth.models import AuthContext
from providers.face.provider import BioGuardFaceProvider
from providers.remote_approval.provider import RemoteApprovalProvider


class FakeBackendClient:
    api_base = "https://backend.example"

    def __init__(self):
        self.face_call = None
        self.approval_call = None
        self.face_response = {"status": "verified", "detail": "matched"}
        self.approval_response = {"status": "completed"}

    def check_face(self, **kwargs):
        self.face_call = kwargs
        return self.face_response

    def get_remote_approval_status(self, approval_type: str, session_id: str):
        self.approval_call = (approval_type, session_id)
        return self.approval_response


class LegacyProviderTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeBackendClient()
        self.context = AuthContext(
            user_id="alice",
            device_id="device-1",
            session_id="session-1",
        )

    def test_face_provider_keeps_existing_backend_payload_and_normalizes_status(self):
        """Would fail if the provider changed deployed webcam-face fields/statuses."""
        provider = BioGuardFaceProvider(self.client)
        context = AuthContext(
            user_id=self.context.user_id,
            device_id=self.context.device_id,
            session_id=self.context.session_id,
            metadata={"image": "base64-image"},
        )

        result = provider.authenticate(context)

        self.assertEqual(self.client.face_call, {
            "session_id": "session-1",
            "username": "alice",
            "device_id": "device-1",
            "image": "base64-image",
        })
        self.assertTrue(result.success)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.metadata, {"detail": "matched"})

    def test_remote_approval_provider_keeps_qr_url_and_completed_status(self):
        """Would fail if remote approval changed the deployed QR route or status mapping."""
        provider = RemoteApprovalProvider(self.client)
        context = AuthContext(
            user_id=self.context.user_id,
            device_id=self.context.device_id,
            session_id=self.context.session_id,
            metadata={"approval_type": "fingerprint"},
        )

        result = provider.authenticate(context)

        self.assertEqual(
            provider.approval_url(context),
            "https://backend.example/agent/mobile/fingerprint/session-1/",
        )
        self.assertEqual(self.client.approval_call, ("fingerprint", "session-1"))
        self.assertTrue(result.success)
        self.assertEqual(result.status, "completed")


if __name__ == "__main__":
    unittest.main()
