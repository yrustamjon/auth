from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SupervisorPackagingTests(unittest.TestCase):
    def test_installer_bundles_service_watchdog_and_recovery(self):
        text=(ROOT/'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        for name in ('BioGuardSupervisor.exe','BioGuardWatchdog.exe','recover-supervisor.cmd'):
            self.assertIn(name,text)
        remove=text.split('procedure CurUninstallStepChanged',1)[1]
        self.assertLess(remove.index('--stop-supervisor'),remove.index('--stop-agent'))
        self.assertLess(remove.index("BrokerCommand('resume'"),remove.index('--stop-supervisor'))

    def test_build_workflow_builds_both_components(self):
        text=(ROOT/'.github/workflows/build.yml').read_text(encoding='utf-8')
        self.assertIn('bioguard-watchdog.spec',text)
        self.assertIn('bioguard-supervisor.spec',text)

    def test_emergency_stop_is_documented_and_nondestructive(self):
        text=(ROOT/'builders/windows/recover-supervisor.cmd').read_text(encoding='utf-8')
        self.assertIn('--stop-supervisor',text)
        self.assertNotIn('del ',text.lower())
        self.assertNotIn('taskkill',text.lower())
