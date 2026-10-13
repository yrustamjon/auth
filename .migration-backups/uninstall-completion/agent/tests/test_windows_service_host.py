import importlib
import sys
import threading
import types
import unittest
from unittest.mock import patch


class ServiceHostTests(unittest.TestCase):
    def setUp(self):
        class Framework:
            def __init__(self, args):
                self.reports = []
            def ReportServiceStatus(self, status):
                self.reports.append(status)
        self.modules = {
            'win32serviceutil': types.SimpleNamespace(ServiceFramework=Framework),
            'win32service': types.SimpleNamespace(SERVICE_STOP_PENDING=3),
        }
        self.context = patch.dict(sys.modules, self.modules)
        self.context.start()
        self.host = importlib.import_module('platform_adapters.windows.service_host')

    def tearDown(self):
        sys.modules.pop('platform_adapters.windows.service_host', None)
        self.context.stop()

    def test_stop_and_shutdown_signal_without_grant(self):
        service = self.host.BioGuardService(['BioGuardAuthority'])
        self.assertFalse(service.stop_event.is_set())
        service.SvcStop()
        self.assertTrue(service.stop_event.is_set())
        self.assertEqual(service.reports, [3])
        self.assertEqual(service.authority.snapshot(1).state, 'MFA_PENDING')
        service.SvcShutdown()

    def test_restart_has_new_generation_and_no_attempt(self):
        first = self.host.BioGuardService(['BioGuardAuthority'])
        first.authority.begin_attempt(1, 'S-1-5-21-1')
        second = self.host.BioGuardService(['BioGuardAuthority'])
        self.assertNotEqual(first.authority.generation, second.authority.generation)
        self.assertIsNone(second.authority.snapshot(1).attempt_id)

    def test_server_failure_signals_cleanup_and_propagates(self):
        service = self.host.BioGuardService(['BioGuardAuthority'])
        def failure(stop, authority):
            raise OSError('pipe failed')
        with patch('platform_adapters.windows.service_host.make_server') as factory:
            factory.return_value.serve.side_effect = failure
            with self.assertRaises(OSError):
                service.SvcDoRun()
        self.assertTrue(service.stop_event.is_set())

    def test_server_receives_service_owned_state(self):
        service = self.host.BioGuardService(['BioGuardAuthority'])
        with patch('platform_adapters.windows.service_host.make_server') as factory:
            service.SvcDoRun()
            factory.return_value.serve.assert_called_once_with(service.stop_event, service.authority)
        self.assertTrue(service.stop_event.is_set())


if __name__ == '__main__':
    unittest.main()
