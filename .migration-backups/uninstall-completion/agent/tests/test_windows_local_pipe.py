import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch
import threading


class PipeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.token = Mock()
        self.pipe = Mock()
        self.security = Mock(TokenUser=1, TokenSessionId=2, TokenImpersonationLevel=3,
                             SecurityIdentification=1)
        self.security.OpenThreadToken.return_value = self.token
        self.security.GetTokenInformation.side_effect = lambda token, kind: {
            1: ('sid', 0), 2: 7, 3: 2}[kind]
        self.security.ConvertSidToStringSid.return_value = 'S-1-5-21-1'
        class NativeError(OSError):
            pass
        native_types = Mock(error=NativeError)
        self.context = patch.dict(sys.modules, {
            'win32pipe': self.pipe, 'win32security': self.security,
            'win32api': Mock(), 'win32con': Mock(TOKEN_QUERY=8),
            'win32file': Mock(), 'win32event': Mock(WAIT_TIMEOUT=258), 'pywintypes': native_types,
            'win32ts': Mock(),
        })
        self.context.start()
        self.module = importlib.import_module('platform_adapters.windows.local_pipe')

    def tearDown(self):
        sys.modules.pop('platform_adapters.windows.local_pipe', None)
        self.context.stop()

    def test_identity_comes_from_token_and_reverts(self):
        identity = self.module.peer_identity('handle')
        self.assertEqual((identity.session_id, identity.user_sid), (7, 'S-1-5-21-1'))
        self.pipe.ImpersonateNamedPipeClient.assert_called_once_with('handle')
        self.security.RevertToSelf.assert_called_once()
        self.token.Close.assert_called_once()

    def test_failed_token_query_reverts_and_closes(self):
        self.security.GetTokenInformation.side_effect = OSError('bad token')
        with self.assertRaises(OSError):
            self.module.peer_identity('handle')
        self.security.RevertToSelf.assert_called_once()
        self.token.Close.assert_called_once()

    def test_failed_impersonation_never_queries_or_dispatches(self):
        self.pipe.ImpersonateNamedPipeClient.side_effect = OSError('denied')
        with self.assertRaises(OSError):
            self.module.peer_identity('handle')
        self.security.OpenThreadToken.assert_not_called()

    def test_session_zero_and_anonymous_rejected(self):
        for session, level in ((0, 2), (7, 0)):
            self.security.GetTokenInformation.side_effect = lambda token, kind: {
                1: ('sid', 0), 2: session, 3: level}[kind]
            with self.assertRaises(PermissionError):
                self.module.peer_identity('handle')

    def test_already_connected_pipe_does_not_wait_on_unsignalled_event(self):
        result = self.module._operation('handle', Mock(), lambda ov: 535)
        self.assertEqual(result, (None, 0))
        self.module.win32event.WaitForSingleObject.assert_not_called()

    def test_revert_failure_is_fatal_not_a_client_rejection(self):
        self.security.RevertToSelf.side_effect = OSError('revert failed')
        with self.assertRaises(RuntimeError):
            self.module.peer_identity('handle')
        self.token.Close.assert_called_once()

    def test_stop_cancels_and_drains_pending_io_before_closing_event(self):
        stop = threading.Event()
        stop.set()
        self.module.win32event.WaitForSingleObject.return_value = 258
        order = []
        self.module.win32file.CancelIoEx.side_effect = lambda *args: order.append('cancel')
        self.module.win32file.GetOverlappedResult.side_effect = lambda *args: order.append('drain')
        self.module.win32event.CreateEvent.return_value.Close.side_effect = lambda: order.append('close')
        with self.assertRaises(TimeoutError):
            self.module._operation('handle', stop, lambda ov: 997)
        self.assertEqual(order, ['cancel', 'drain', 'close'])

    def test_oversized_read_is_rejected_before_protocol_dispatch(self):
        with patch.object(self.module, '_operation', return_value=((0, b'x' * 65537), 65537)):
            with self.assertRaises(self.module.ProtocolError):
                self.module._read('handle', threading.Event())


if __name__ == '__main__':
    unittest.main()
