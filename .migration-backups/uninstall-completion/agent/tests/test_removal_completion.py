"""Uninstall regressions using isolated files and simulated OS process handles."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.network.client import BioGuardApiClient
from platform_adapters.windows.lifecycle import (
    cleanup_install_cache, cleanup_user_credentials, stop_installed_agent,
)
from services.removal import RemovalController
from tests.test_removal import MemoryReceipt


class RemovalCompletionTests(unittest.TestCase):
    def test_runtime_artifacts_in_bundle_do_not_block_server_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / 'AD BioGuard'
            bundle = root / '_internal'
            (bundle / '.webview_data').mkdir(parents=True)
            (bundle / '.webview_data' / 'cache').write_bytes(b'fixture')
            (bundle / 'bioguard.log').write_text('fixture')
            (root / 'unins000.exe').write_bytes(b'fixture')
            (root / '.webview_data').mkdir()
            (root / 'bioguard.log').write_text('fixture')
            roaming, local = base / 'roaming', base / 'local'
            credentials = roaming / 'ADBioGuard'
            credentials.mkdir(parents=True)
            (credentials / 'key.dpapi').write_bytes(b'fixture')
            requests = []
            def transport(request, timeout):
                requests.append(request.full_url.rsplit('/', 2)[1])
                payload = json.loads(request.data)
                self.assertEqual(payload['device_uuid'], 'fixture-pc')
                return json.dumps({'state': 'removed' if requests[-1] == 'complete' else 'removal_pending'}).encode()
            store = MemoryReceipt()
            controller = RemovalController(BioGuardApiClient('http://localhost', transport=transport),
                'fixture-pc', store, lambda: cleanup_user_credentials(str(root)))
            with patch.dict(os.environ, APPDATA=str(roaming), LOCALAPPDATA=str(local)), patch(
                    'platform_adapters.windows.lifecycle.validate_install_path', return_value=root):
                controller.begin('a' * 43)
                cleanup_install_cache(str(root))
                result = controller.cleanup_and_complete()
            self.assertEqual(result['state'], 'removed')
            self.assertEqual(requests, ['begin', 'status', 'complete'])
            self.assertFalse(credentials.exists())
            self.assertFalse(bundle.exists())
            self.assertIsNone(store.value)

    def test_remaining_bundle_binary_blocks_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'AD BioGuard'
            bundle = root / '_internal'
            bundle.mkdir(parents=True)
            binary = bundle / 'still-loaded.dll'
            binary.write_bytes(b'fixture')
            (bundle / 'bioguard.log').write_text('fixture')
            with patch('platform_adapters.windows.lifecycle.validate_install_path', return_value=root):
                cleanup_install_cache(str(root))
                with self.assertRaises(OSError):
                    cleanup_user_credentials(str(root))
            self.assertEqual(binary.read_bytes(), b'fixture')

    def test_runtime_cleanup_refuses_bundle_reparse_points(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'AD BioGuard'
            bundle = root / '_internal'
            (bundle / '.webview_data').mkdir(parents=True)
            original_is_symlink = Path.is_symlink
            def is_symlink(path):
                return path == bundle or original_is_symlink(path)
            with patch('platform_adapters.windows.lifecycle.validate_install_path', return_value=root), patch.object(
                    Path, 'is_symlink', is_symlink):
                with self.assertRaises(OSError):
                    cleanup_install_cache(str(root))
            self.assertTrue((bundle / '.webview_data').exists())


class InstalledProcessStopTests(unittest.TestCase):
    def test_stop_includes_standalone_watchdog_before_gui_and_preserves_other_installations(self):
        self.run_stop()

    def test_failure_to_stop_matching_watchdog_aborts_native_removal(self):
        self.run_stop(fail_watchdog=True)

    def run_stop(self, *, fail_watchdog=False):
        import win32event
        import win32con
        root = Path(tempfile.gettempdir()) / 'fixture-install' / 'AD BioGuard'
        events = []
        class Handle:
            def __init__(self, pid, path):
                self.pid, self.path, self.alive, self.closed = pid, path, True, False
            def Close(self):
                self.closed = True
        watchdog = Handle(2000001, root / 'BioGuardWatchdog.exe')
        agent = Handle(2000002, root / 'BioGuard.exe')
        other = Handle(2000003, root.parent / 'other' / 'BioGuardWatchdog.exe')
        handles = {handle.pid: handle for handle in (watchdog, agent, other)}
        def terminate(handle, code):
            if fail_watchdog and handle is watchdog:
                raise OSError('fixture refusal')
            events.append(('terminate', handle.pid))
            handle.alive = False
        def close_window(hwnd, message, first, second):
            self.assertEqual(message, win32con.WM_CLOSE)
            events.append(('close', agent.pid))
            agent.alive = False
        with patch('platform_adapters.windows.lifecycle.validate_install_path', return_value=root), patch(
                'win32process.EnumProcesses', return_value=list(handles)), patch(
                'win32api.OpenProcess', side_effect=lambda access, inherit, pid: handles[pid]), patch(
                'platform_adapters.windows.lifecycle_pipe.process_image_path', side_effect=lambda handle: str(handle.path)), patch(
                'win32api.TerminateProcess', side_effect=terminate), patch(
                'win32event.WaitForSingleObject', side_effect=lambda handle, timeout: win32event.WAIT_TIMEOUT if handle.alive else 0), patch(
                'win32gui.EnumWindows', side_effect=lambda callback, unused: callback(agent.pid, unused)), patch(
                'win32process.GetWindowThreadProcessId', side_effect=lambda hwnd: (1, hwnd)), patch(
                'win32gui.PostMessage', side_effect=close_window):
            if fail_watchdog:
                with self.assertRaises(OSError):
                    stop_installed_agent(str(root))
                self.assertTrue(agent.alive)
            else:
                stop_installed_agent(str(root))
                self.assertFalse(watchdog.alive)
                self.assertFalse(agent.alive)
                self.assertEqual(events, [('terminate', watchdog.pid), ('close', agent.pid)])
            self.assertTrue(other.alive)

