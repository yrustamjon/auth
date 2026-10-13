import os
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

try:
    import win32api,win32con,win32service
    NATIVE=os.name=='nt'
except ImportError:NATIVE=False


@unittest.skipUnless(NATIVE,'Windows and pywin32 required')
class SupervisorWindowsTests(unittest.TestCase):
    def test_emergency_remove_does_not_require_intact_agent_files(self):
        from platform_adapters.windows import supervisor_service as module
        with patch('ctypes.windll.shell32.IsUserAnAdmin',return_value=True),patch.object(module,'installed_context',side_effect=OSError('missing files')) as context,patch.object(module.win32serviceutil,'QueryServiceStatus',return_value=(0,win32service.SERVICE_STOPPED)),patch.object(module.win32serviceutil,'RemoveService') as remove:
            module.cli('remove')
            context.assert_not_called();remove.assert_called_once_with('BioGuardSupervisor')

    def test_exact_process_handle_reports_live_process_and_closes(self):
        from platform_adapters.windows.supervisor_process import ProcessRef
        handle=win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION|win32con.SYNCHRONIZE,False,os.getpid())
        process=ProcessRef(handle,os.getpid())
        self.assertIsNone(process.poll());process.close();self.assertIsNone(process.handle)

    def test_user_launch_uses_target_session_token_and_user_environment(self):
        from platform_adapters.windows.supervisor_service import launch_watchdog
        token=Mock();process=Mock();thread=Mock()
        with patch('win32ts.WTSQueryUserToken',return_value=token) as get_token,patch('win32profile.CreateEnvironmentBlock',return_value={'USERPROFILE':'fixture'}),patch('win32process.CreateProcessAsUser',return_value=(process,thread,123,456)) as create:
            child=launch_watchdog(Path('C:/Program Files/AD BioGuard'),7)
            get_token.assert_called_once_with(7)
            self.assertEqual(create.call_args.args[9].lpDesktop,'winsta0\\default')
            self.assertEqual(create.call_args.args[7],{'USERPROFILE':'fixture'})
            self.assertEqual(child.pid,123)
            token.Close.assert_called_once();thread.Close.assert_called_once();child.close()
