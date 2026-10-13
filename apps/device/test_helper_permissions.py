import stat
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from django.test import TestCase, override_settings
from apps.device.browser_enrollment import create_session, helper_bundle


class MacHelperPermissionsTests(TestCase):
    def test_mac_launcher_preserves_executable_unix_permissions(self):
        session, _, _, token = create_session(browser_key='mac-browser', source_ip='127.0.0.1')
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'macos-arm64').write_bytes(b'mac-helper')
            with override_settings(DEVICE_REGISTRATION_HELPER_DIR=directory):
                bundle = helper_bundle(session_id=session.id, browser_key='mac-browser',
                                      scan_token=token, platform='macos', architecture='arm64')
        with ZipFile(BytesIO(bundle)) as archive:
            launcher = archive.getinfo('run-registration.command')
            self.assertEqual(launcher.create_system, 3)
            mode = launcher.external_attr >> 16
            self.assertTrue(stat.S_ISREG(mode))
            self.assertEqual(stat.S_IMODE(mode), 0o755)
            self.assertNotIn(b'\r', archive.read(launcher))
