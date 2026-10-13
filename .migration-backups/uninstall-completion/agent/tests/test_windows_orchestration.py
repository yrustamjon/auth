import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from core.auth.models import AuthResult
from core.network.errors import BackendResponseError


TEST_APPDATA = tempfile.mkdtemp(prefix="bioguard-orchestration-test-")
os.environ["APPDATA"] = TEST_APPDATA


def load_windows_api_module():
    """Load orchestration without crypto or Windows hardware dependencies."""
    certificate_stub = types.ModuleType("core.cert")
    certificate_stub.is_activated = lambda: True
    certificate_stub.get_org_slug = lambda: ""

    previous_certificate = sys.modules.get("core.cert")
    sys.modules["core.cert"] = certificate_stub
    sys.modules.pop("app.controller", None)
    try:
        return importlib.import_module("app.controller")
    finally:
        if previous_certificate is None:
            sys.modules.pop("core.cert", None)
        else:
            sys.modules["core.cert"] = previous_certificate


class ImmediateThread:
    def __init__(self, *, target, daemon):
        self._target = target

    def start(self):
        self._target()


class RecordingWindow:
    def __init__(self):
        self.javascript = []

    def evaluate_js(self, code: str):
        self.javascript.append(code)


class RecordingAuthenticationManager:
    def __init__(self):
        self.calls = []

    def authenticate(self, context, policy, requested_provider_id=None):
        self.calls.append((context, policy, requested_provider_id))
        return AuthResult(
            provider_id="bioguard_face",
            success=False,
            status="mismatch",
            metadata={"detail": "not matched"},
        )


class FakeApiClient:
    def is_online(self):
        return True


class FakePlatformAdapter:
    def lock_session(self):
        return None

    def unlock_session(self):
        return None


class WindowsOrchestrationTests(unittest.TestCase):
    def test_prerelease_controls_work_without_environment_mode_flags(self):
        from unittest.mock import Mock
        module = load_windows_api_module()
        api = module.BioGuardAPI.__new__(module.BioGuardAPI)
        api.hide_lock = Mock()
        api._platform = Mock()
        api._window = Mock()
        with patch.object(module, 'DEV_MODE', False), patch.object(module, 'DEMO_MODE', False):
            api.dev_unlock()
            api.dev_exit()
        api.hide_lock.assert_called_once_with()
        api._platform.stop_autolock.assert_called_once_with()
        api._platform.unlock_session.assert_called_once_with()
        api._window.destroy.assert_called_once_with()

    def test_personal_session_uses_returned_owner_for_all_biometric_contexts(self):
        module = load_windows_api_module()
        class PersonalClient(FakeApiClient):
            def start_session(self, username, device_id):
                return {'session_id': 'personal-session', 'username': 'personal-owner'}
        manager = RecordingAuthenticationManager()
        api = module.BioGuardAPI(RecordingWindow(), api_client=PersonalClient(),
            authentication_manager=manager, platform_adapter=FakePlatformAdapter())
        with patch.object(module.threading, 'Thread', ImmediateThread), patch.object(api, 'start_internet_monitor'):
            api.start_session()
            api.capture_face('fixture')
        self.assertEqual(manager.calls[0][0].user_id, 'personal-owner')
        self.assertEqual(api._remote_context('fingerprint').user_id, 'personal-owner')

    def test_session_enrollment_conflict_explains_pending_registration(self):
        module = load_windows_api_module()
        class EnrollmentPendingClient(FakeApiClient):
            def start_session(self, username, device_id):
                raise BackendResponseError("Backend returned HTTP 409", status_code=409,
                    response_body='{"status":"enrollment_required","code":"AGENT_ENROLLMENT_REQUIRED","detail":"Agent enrollment required"}')
        window = RecordingWindow()
        api = module.BioGuardAPI(window, api_client=EnrollmentPendingClient(),
            platform_adapter=FakePlatformAdapter())
        api._session_id = "old-session"
        with patch.object(module.threading, "Thread", ImmediateThread):
            api.start_session()
        self.assertIsNone(api._session_id)
        self.assertEqual(window.javascript[-1], "App.onEnrollmentRequired()")
        self.assertTrue(api._enrollment_required)
        self.assertNotIn("onSessionReady", window.javascript[-1])

    def test_webcam_face_flow_routes_through_authentication_manager(self):
        """Would fail if the Windows UI bypassed provider policy/normalization."""
        module = load_windows_api_module()
        manager = RecordingAuthenticationManager()
        window = RecordingWindow()
        api = module.BioGuardAPI(
            window,
            api_client=FakeApiClient(),
            authentication_manager=manager,
            platform_adapter=FakePlatformAdapter(),
        )
        api._session_id = "session-1"

        with patch.object(module.threading, "Thread", ImmediateThread):
            api.capture_face("base64-image")

        context, policy, requested_provider_id = manager.calls[0]
        self.assertEqual(context.metadata, {"image": "base64-image"})
        self.assertEqual(context.session_id, "session-1")
        self.assertEqual(policy.allowed_provider_ids, frozenset({"bioguard_face"}))
        self.assertEqual(requested_provider_id, "bioguard_face")
        self.assertIn("App.onFaceRetry('not matched')", window.javascript)


if __name__ == "__main__":
    unittest.main()
