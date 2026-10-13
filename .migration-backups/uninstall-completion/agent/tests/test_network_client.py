import importlib
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from core.network.client import BioGuardApiClient
from core.network.errors import BackendUnavailableError


class RecordingTransport:
    def __init__(self, response: bytes):
        self.response = response
        self.requests = []

    def __call__(self, request, timeout: float) -> bytes:
        self.requests.append((request, timeout))
        return self.response


class NetworkClientTests(unittest.TestCase):
    def test_ngrok_requests_skip_browser_warning(self):
        transport = RecordingTransport(b'{"status":"ok"}')
        client = BioGuardApiClient("https://sibilantly-penanceless-young.ngrok-free.dev", transport=transport)
        self.assertTrue(client.is_online())
        self.assertEqual(transport.requests[0][0].get_header("Ngrok-skip-browser-warning"), "true")

    def test_html_warning_page_does_not_count_as_online(self):
        transport = RecordingTransport(b'<!DOCTYPE html><html><body>ngrok warning</body></html>')
        self.assertFalse(BioGuardApiClient("https://backend.example", transport=transport).is_online())

    def test_post_preserves_legacy_json_payload_and_signed_headers(self):
        """Would fail if centralization changed a deployed request body or headers."""
        transport = RecordingTransport(b'{"session_id":"s-1"}')
        client = BioGuardApiClient(
            "https://backend.example",
            signed_headers_provider=lambda: {"X-PC-ID": "device-1"},
            transport=transport,
        )

        result = client.post("/api/agent/session/start/", {
            "username": "alice",
            "pc_id": "device-1",
        })

        request, timeout = transport.requests[0]
        self.assertEqual(result, {"session_id": "s-1"})
        self.assertEqual(request.full_url, "https://backend.example/api/agent/session/start/")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {"username": "alice", "pc_id": "device-1"})
        self.assertEqual(request.get_header("X-pc-id"), "device-1")
        self.assertEqual(timeout, 10)

    def test_network_failure_is_a_typed_backend_unavailable_error(self):
        """Would fail if callers received a raw transport error or silent fallback."""
        def offline_transport(request, timeout: float) -> bytes:
            raise urllib.error.URLError("offline")

        client = BioGuardApiClient("https://backend.example", transport=offline_transport)

        with self.assertRaises(BackendUnavailableError):
            client.get("/api/health/", timeout=3)

    def test_legacy_api_post_delegates_without_changing_its_return_value(self):
        """Would fail if legacy `api_post` callers lost their public behavior."""
        with tempfile.TemporaryDirectory() as app_data:
            with patch.dict(os.environ, {"APPDATA": app_data}, clear=False):
                sys.modules.pop("core.config", None)
                sys.modules.pop("api.client", None)
                legacy = importlib.import_module("api.client")

        class LegacyCompatibleClient:
            def __init__(self):
                self.path = None
                self.payload = None

            def post(self, path, payload):
                self.path = path
                self.payload = payload
                return {"status": "verified"}

        client = LegacyCompatibleClient()
        with patch.object(legacy, "get_default_client", return_value=client):
            result = legacy.api_post("/api/face/agent/check/", {"image": "encoded"})

        self.assertEqual(result, {"status": "verified"})
        self.assertEqual(client.path, "/api/face/agent/check/")
        self.assertEqual(client.payload, {"image": "encoded"})


if __name__ == "__main__":
    unittest.main()
