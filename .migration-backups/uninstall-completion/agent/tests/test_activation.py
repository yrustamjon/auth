import os
import importlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# `core.config` creates a compatibility device UUID at import time. Configure
# its storage before importing activation so this test stays hermetic.
TEST_APPDATA = tempfile.mkdtemp(prefix="bioguard-activation-test-")
os.environ["APPDATA"] = TEST_APPDATA


def load_activation_module():
    """Load the activation request logic without requiring crypto in this unit test."""
    certificate_stub = types.ModuleType("core.cert")
    certificate_stub.generate_keypair = lambda: ("unused-public", "unused-private")
    certificate_stub.save_cert = lambda certificate, private_key: None
    certificate_stub.is_activated = lambda: False

    previous_certificate = sys.modules.get("core.cert")
    sys.modules["core.cert"] = certificate_stub
    sys.modules.pop("core.activation", None)
    try:
        return importlib.import_module("core.activation")
    finally:
        if previous_certificate is None:
            sys.modules.pop("core.cert", None)
        else:
            sys.modules["core.cert"] = previous_certificate


class RecordingApiClient:
    def __init__(self):
        self.path = None
        self.payload = None
        self.timeout = None

    def post(self, path, payload, *, timeout, request_signer=None):
        self.path = path
        self.payload = payload
        self.timeout = timeout
        return {"certificate": {"cert_id": "cert-1"}}


class ActivationTests(unittest.TestCase):
    def setUp(self):
        context=patch('storage.legacy_windows_cert.validate_protection')
        context.start();self.addCleanup(context.stop)

    def test_forced_org_activation_contacts_backend_with_existing_certificate(self):
        activation = load_activation_module()
        client = RecordingApiClient()
        with (
            patch.object(activation, "is_activated", return_value=True),
            patch.object(activation, "get_default_client", return_value=client),
        ):
            result = activation.activate_org("activation-code", force=True)
        self.assertEqual(result["certificate"]["cert_id"], "cert-1")
        self.assertEqual(client.path, "/api/agent/activate/")

    def test_forced_personal_activation_contacts_backend_with_existing_certificate(self):
        activation = load_activation_module()
        client = RecordingApiClient()
        with (
            patch.object(activation, "is_activated", return_value=True),
            patch.object(activation, "get_default_client", return_value=client),
        ):
            result = activation.activate_personal("user@example.com", "password", force=True)
        self.assertEqual(result["certificate"]["cert_id"], "cert-1")
        self.assertEqual(client.path, "/api/agent/activate/personal/")

    def test_org_activation_uses_central_client_with_legacy_payload(self):
        """Would fail if activation bypassed the common client or changed fields."""
        client = RecordingApiClient()
        activation = load_activation_module()
        with (
            patch.object(activation, "is_activated", return_value=False),
            patch.object(activation, "generate_keypair", return_value=("public", "private")),
            patch.object(activation, "get_default_client", return_value=client),
            patch.object(activation, "save_cert") as save_cert,
        ):
            result = activation.activate_org("activation-code")

        self.assertEqual(result, {"certificate": {"cert_id": "cert-1"}})
        self.assertEqual(client.path, "/api/agent/activate/")
        self.assertEqual(client.timeout, 15)
        self.assertEqual(client.payload["activation_code"], "activation-code")
        self.assertEqual(client.payload["public_key"], "public")
        save_cert.assert_called_once_with({"cert_id": "cert-1"}, "private")


if __name__ == "__main__":
    unittest.main()

class ActivationStorageFailureTests(unittest.TestCase):
    def test_unavailable_protected_storage_never_consumes_backend_token(self):
        activation = load_activation_module()
        with patch.object(activation,'is_activated',return_value=False), \
             patch('storage.legacy_windows_cert.validate_protection',side_effect=OSError('DPAPI unavailable')), \
             patch.object(activation,'get_default_client') as client:
            with self.assertRaises(activation.ActivationError):
                activation.activate_org('synthetic-token')
        client.assert_not_called()
