import unittest
from unittest.mock import Mock, patch
import sys

from platform_adapters.windows import service_security


class ServiceAdministrationTests(unittest.TestCase):
    def test_missing_vm_flag_never_calls_service_mutation(self):
        native = Mock()
        with patch.dict(sys.modules, {'win32serviceutil': native}):
            for command in ('install', 'start', 'stop', 'remove'):
                with self.subTest(command=command), self.assertRaises(SystemExit):
                    service_security.service_cli(Mock(), [command])
        native.InstallService.assert_not_called()
        native.StartService.assert_not_called()
        native.StopService.assert_not_called()
        native.RemoveService.assert_not_called()

    def test_status_is_read_only_without_vm_flag(self):
        native = Mock()
        with patch.dict(sys.modules, {'win32serviceutil': native}), patch('builtins.print'):
            self.assertEqual(service_security.service_cli(Mock(), ['status']), 0)
        native.QueryServiceStatus.assert_called_once_with('BioGuardAuthority')
        native.InstallService.assert_not_called()

    def test_non_elevated_vm_mutation_is_rejected(self):
        native = Mock()
        windll = Mock()
        windll.shell32.IsUserAnAdmin.return_value = False
        with patch.dict(sys.modules, {'win32serviceutil': native}), patch('ctypes.windll', windll, create=True):
            with self.assertRaises(SystemExit):
                service_security.service_cli(Mock(), ['install', '--vm-test'])
        native.InstallService.assert_not_called()

    def test_workspace_install_path_is_rejected(self):
        with self.assertRaises(ValueError):
            service_security.validate_install_tree('C:/Users/User/Desktop/BioGuardService.exe', 'C:/Program Files')

    def test_protected_files_have_administrative_owner_not_original_user(self):
        security = Mock(SE_FILE_OBJECT=1, DACL_SECURITY_INFORMATION=4,
                        PROTECTED_DACL_SECURITY_INFORMATION=0x80000000, OWNER_SECURITY_INFORMATION=1)
        with patch.dict(sys.modules, {'win32security': security}):
            service_security._protect_files(['file'], 'S-1-5-80-1')
        call = security.SetNamedSecurityInfo.call_args.args
        self.assertEqual(call[3], security.ConvertStringSidToSid.return_value)
        self.assertTrue(call[2] & 1)
        security.ConvertStringSidToSid.assert_called_once_with('S-1-5-32-544')

    def test_non_crash_service_failures_trigger_recovery(self):
        service = Mock(SC_MANAGER_CONNECT=1, SERVICE_ALL_ACCESS=2,
                       SERVICE_CONFIG_SERVICE_SID_INFO=5, SERVICE_SID_TYPE_UNRESTRICTED=1,
                       SERVICE_CONFIG_FAILURE_ACTIONS=2, SERVICE_CONFIG_FAILURE_ACTIONS_FLAG=4,
                       SC_ACTION_RESTART=1, SC_ACTION_NONE=0)
        security = Mock(DACL_SECURITY_INFORMATION=4)
        with patch.dict(sys.modules, {'win32service': service, 'win32security': security}), \
             patch.object(service_security, '_service_sid', return_value='S-1-5-80-1'):
            service_security._configure_service()
        service.ChangeServiceConfig2.assert_any_call(service.OpenService.return_value, 4, True)


if __name__ == '__main__':
    unittest.main()

class ServiceInstallationTests(unittest.TestCase):
    def run_install(self, failure=False):
        native=Mock()
        shell=Mock();shell.SHGetFolderPath.return_value='C:/Program Files'
        events=[]
        native.InstallService.side_effect=lambda *a,**kw:events.append(('install',kw))
        native.RemoveService.side_effect=lambda *a:events.append(('remove',a))
        windll=Mock();windll.shell32.IsUserAnAdmin.return_value=True
        def protect(*args): events.append(('protect',args))
        def configure():
            events.append(('configure',None))
            if failure: raise OSError('security configuration failed')
        with patch.dict(sys.modules,{'win32serviceutil':native,'win32service':Mock(SERVICE_DEMAND_START=3),
            'win32com':Mock(),'win32com.shell':Mock(shell=shell,shellcon=Mock()),
            'win32com.shell.shell':shell,'win32com.shell.shellcon':Mock()}), \
            patch('ctypes.windll',windll,create=True),patch.object(sys,'frozen',True,create=True), \
            patch.object(service_security,'validate_install_tree',return_value=['exe']), \
            patch.object(service_security,'_service_sid',side_effect=lambda: events.append(('sid',None)) or 'S-1-5-80-1'), \
            patch.object(service_security,'_protect_files',side_effect=protect), \
            patch.object(service_security,'_configure_service',side_effect=configure):
            if failure:
                with self.assertRaises(OSError):service_security.service_cli(Mock(),['install','--vm-test'])
            else: service_security.service_cli(Mock(),['install','--vm-test'])
        return events

    def test_create_manual_service_before_resolving_sid_then_protect_and_configure(self):
        events=self.run_install()
        self.assertEqual([event[0] for event in events],['install','sid','protect','configure'])
        self.assertEqual(events[0][1]['startType'],3)
        self.assertEqual(events[0][1]['userName'],'NT AUTHORITY\\LocalService')

    def test_security_failure_removes_partial_service(self):
        self.assertEqual(self.run_install(True)[-1][0],'remove')

    def test_automatic_start_is_applied_after_recovery_and_acl(self):
        service=Mock(SC_MANAGER_CONNECT=1,SERVICE_ALL_ACCESS=2,SERVICE_CONFIG_SERVICE_SID_INFO=5,
            SERVICE_SID_TYPE_UNRESTRICTED=1,SERVICE_CONFIG_FAILURE_ACTIONS=2,SERVICE_CONFIG_FAILURE_ACTIONS_FLAG=4,
            SC_ACTION_RESTART=1,SC_ACTION_NONE=0,SERVICE_NO_CHANGE=0xffffffff,SERVICE_AUTO_START=2)
        security=Mock(DACL_SECURITY_INFORMATION=4)
        with patch.dict(sys.modules,{'win32service':service,'win32security':security}),patch.object(service_security,'_service_sid',return_value='sid'):
            service_security._configure_service()
        service.ChangeServiceConfig.assert_called_once()
        self.assertEqual(service.ChangeServiceConfig.call_args.args[2],2)
