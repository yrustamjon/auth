import json
import os
import sys
import struct
import unittest

VM_ENABLED = sys.platform == 'win32' and os.environ.get('ADBIOGUARD_VM_TESTS') == '1'


@unittest.skipUnless(VM_ENABLED, 'Requires explicitly prepared disposable Windows VM (ADBIOGUARD_VM_TESTS=1)')
class ServiceIntegrationTests(unittest.TestCase):
    def test_ordinary_user_cannot_stop_reconfigure_or_delete_service(self):
        import ctypes
        import pywintypes
        import win32service
        self.assertFalse(ctypes.windll.shell32.IsUserAnAdmin(), 'Run this acceptance test as an ordinary VM user')
        manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        try:
            query = win32service.OpenService(manager, 'BioGuardAuthority', win32service.SERVICE_QUERY_STATUS)
            win32service.CloseServiceHandle(query)
            for right in (win32service.SERVICE_STOP, win32service.SERVICE_CHANGE_CONFIG,
                          0x10000, 0x40000, 0x80000):
                with self.subTest(right=right):
                    try:
                        handle = win32service.OpenService(manager, 'BioGuardAuthority', right)
                    except pywintypes.error as error:
                        self.assertEqual(error.winerror, 5)
                    else:
                        win32service.CloseServiceHandle(handle)
                        self.fail('Ordinary user received a forbidden service right')
        finally:
            win32service.CloseServiceHandle(manager)

    def test_authenticated_pipe_reports_pending_and_rejects_unlock(self):
        import win32api
        import win32con
        import win32file
        import win32pipe
        import win32security
        from platform_adapters.windows.service_security import CLIENT_PIPE_ACCESS
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        try:
            session = win32security.GetTokenInformation(token, win32security.TokenSessionId)
        finally:
            token.Close()
        name = r'\\.\pipe\BioGuardAuthority-v1-' + str(session)
        win32pipe.WaitNamedPipe(name, 5000)
        handle = win32file.CreateFile(name, CLIENT_PIPE_ACCESS, 0, None, win32con.OPEN_EXISTING,
                                     0x00100000 | 0x00010000, None)  # SECURITY_SQOS_PRESENT | IDENTIFICATION
        try:
            def read_exact(size):
                value = b''
                while len(value) < size:
                    _, part = win32file.ReadFile(handle, size - len(value))
                    self.assertTrue(part, 'Disconnected pipe')
                    value += part
                return value
            def response():
                size = struct.unpack('!I', read_exact(4))[0]
                self.assertLessEqual(size, 65536)
                return json.loads(read_exact(size))
            win32file.WriteFile(handle, b'BIOGUARD/1')
            hello = response()
            request = dict(version=1, request_id='vm-status', command='status',
                           session_id=session, user_sid=hello['user_sid'], generation=hello['generation'])
            win32file.WriteFile(handle, json.dumps(request).encode())
            status = response()
            self.assertTrue(status['ok'])
            self.assertEqual(status['state'], 'MFA_PENDING')
            request.update(request_id='vm-unlock', command='unlock')
            win32file.WriteFile(handle, json.dumps(request).encode())
            self.assertEqual(response()['error'], 'UNSUPPORTED_COMMAND')
        finally:
            handle.Close()
