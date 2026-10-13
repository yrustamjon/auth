"""Safe native IPC/DPAPI checks; never installs or removes the actual agent."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch

try:
    import win32api, win32con, win32file, win32pipe, win32security
    NATIVE = os.name == 'nt'
except ImportError:
    NATIVE = False


def current_sid_fixture():
    from platform_adapters.windows.lifecycle import current_sid
    return current_sid()


@unittest.skipUnless(NATIVE, 'Windows and pywin32 required')
class WindowsLifecycleTests(unittest.TestCase):
    def test_prepared_recovery_does_not_read_exclusively_locked_uninstall_log(self):
        from platform_adapters.windows.lifecycle import prepare_native_recovery
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            install = base / 'install'
            install.mkdir()
            (install / 'unins000.exe').write_bytes(b'fixture-exe')
            data = install / 'unins000.dat'
            data.write_bytes(b'fixture-dat')
            helper = base / 'fixture-helper.exe'
            helper.write_bytes(b'fixture-helper')
            with patch.dict(os.environ, ProgramData=str(base)), patch(
                    'platform_adapters.windows.lifecycle.validate_install_path', return_value=install), patch(
                    'platform_adapters.windows.lifecycle.is_elevated', return_value=True), patch(
                    'platform_adapters.windows.lifecycle.native_recovery_generation', return_value='fixture', create=True), patch(
                    'platform_adapters.windows.lifecycle.store_native_recovery_generation', create=True), patch(
                    'win32security.SetFileSecurity'), patch('sys.executable', str(helper)):
                prepare_native_recovery(str(install), current_sid_fixture())
                handle = win32file.CreateFile(str(data), win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                    0, None, win32con.OPEN_EXISTING, 0, None)
                try:
                    with self.assertRaises(PermissionError):
                        data.read_bytes()
                    prepare_native_recovery(str(install), current_sid_fixture())
                    from platform_adapters.windows.lifecycle import check_native_recovery
                    with patch('platform_adapters.windows.lifecycle.native_recovery_generation', return_value='new-install'):
                        with self.assertRaises(OSError):
                            check_native_recovery(str(install), current_sid_fixture())
                    archive = base / 'AD BioGuard' / 'native-removal' / 'unins000.dat'
                    archive.write_bytes(b'tampered')
                    with self.assertRaises(OSError):
                        check_native_recovery(str(install), current_sid_fixture())
                finally:
                    handle.Close()

    def test_cleanup_removes_prepared_activation_key_journal(self):
        from platform_adapters.windows.lifecycle import cleanup_user_credentials
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            appdata, local, install = base / 'roaming', base / 'local', base / 'install'
            install.mkdir()
            for folder in (appdata / 'ADBioGuard', local / 'AD BioGuard', local / 'ADBioGuardSetup'):
                folder.mkdir(parents=True)
                (folder / 'key.dpapi').write_bytes(b'fixture')
            with patch.dict(os.environ, APPDATA=str(appdata), LOCALAPPDATA=str(local)), patch(
                    'platform_adapters.windows.lifecycle.validate_install_path', return_value=install):
                cleanup_user_credentials(str(install))
            self.assertFalse((local / 'ADBioGuardSetup').exists())

    def test_process_identity_uses_actual_windows_api(self):
        from platform_adapters.windows.lifecycle_pipe import process_image_path, process_session
        import ctypes
        buffer = ctypes.create_unicode_buffer(32768)
        ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, os.getpid())
        try:
            # A venv's sys.executable can name a launcher rather than the loaded
            # process image. Compare against the independent module-image API.
            self.assertEqual(Path(process_image_path(handle)).resolve(), Path(buffer.value).resolve())
            self.assertGreater(process_session(os.getpid()), 0)
        finally:
            handle.Close()

    def test_protected_receipt_roundtrip_and_corruption(self):
        from platform_adapters.windows.lifecycle import ProtectedReceipt
        with tempfile.TemporaryDirectory() as directory, patch('platform_adapters.windows.lifecycle.recovery_dir', return_value=Path(directory)):
            store = ProtectedReceipt(r'C:\Program Files\AD BioGuard')
            store.save({'version': 1, 'device_uuid': 'fixture', 'private_key': 'PRIVATE-FIXTURE'})
            self.assertNotIn(b'PRIVATE-FIXTURE', store.path.read_bytes())
            self.assertEqual(store.load()['device_uuid'], 'fixture')
            store.path.write_bytes(b'corrupt')
            with self.assertRaises(OSError):
                store.load()

    def test_duplicate_desktop_token_and_environment_api(self):
        import win32profile
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY | win32con.TOKEN_DUPLICATE)
        primary = None
        try:
            primary = win32security.DuplicateTokenEx(token, win32security.SecurityImpersonation,
                win32con.TOKEN_ALL_ACCESS, win32security.TokenPrimary)
            env = win32profile.CreateEnvironmentBlock(primary, False)
            self.assertIsInstance(env, dict)
            self.assertTrue(any(key.upper() == 'USERPROFILE' for key in env))
        finally:
            if primary: primary.Close()
            token.Close()

    def test_real_local_pipe_transmits_unicode_without_secret_files(self):
        from services.lifecycle_broker import LifecycleBroker
        from platform_adapters.windows.lifecycle import current_sid
        from platform_adapters.windows.lifecycle_pipe import pipe_path, serve
        name = 'BioGuardLifecycle-' + str(uuid.uuid4())
        broker = LifecycleBroker('install', lambda token: {'organization': 'O‘zbek tashkilot', 'device_uuid': 'fixture'}, None, current_sid(), 'Fixture')
        errors = []
        def server():
            try:
                serve(name, os.getpid(), broker)
            except Exception as error:
                errors.append(error)
        with patch('platform_adapters.windows.lifecycle.is_elevated', return_value=False):
            thread = threading.Thread(target=server, daemon=True)
            thread.start()
            client = None
            try:
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    try:
                        client = win32file.CreateFile(pipe_path(name), win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                            0, None, win32con.OPEN_EXISTING, 0, None)
                        break
                    except Exception:
                        time.sleep(.025)
                self.assertIsNotNone(client, errors)
                win32pipe.SetNamedPipeHandleState(client, win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_NOWAIT, None, None)
                win32file.WriteFile(client, 'activate\tMEMORY-ONLY'.encode('utf-16-le'))
                response = None
                while time.monotonic() < deadline:
                    try:
                        _, response = win32file.ReadFile(client, 65536)
                        break
                    except Exception:
                        time.sleep(.025)
                self.assertIsNotNone(response, errors)
                self.assertNotIn('MEMORY-ONLY', response.decode('utf-16-le'))
                win32file.WriteFile(client, 'cancel\t'.encode('utf-16-le'))
            finally:
                if client: client.Close()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
