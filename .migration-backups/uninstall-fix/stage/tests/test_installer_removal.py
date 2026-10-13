from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerRemovalTests(unittest.TestCase):
    def test_recovery_snapshot_is_prepared_after_installation(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertIn('procedure CurStepChanged', source)
        install = source.split('procedure CurStepChanged', 1)[1].split('procedure StopBroker', 1)[0]
        self.assertIn('ssPostInstall', install)
        self.assertIn('--prepare-native-recovery', install)
        self.assertIn('RecoveryGeneration', source)

    def test_async_ready_verification_survives_state_polling(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertIn("if Command = 'verify' then VerificationInFlight := True", source)
        self.assertIn("if VerificationInFlight and (BrokerState <> 'pending')", source)
        self.assertIn("WizardForm.NextButton.Enabled := VerifyDone and (BrokerState = 'ready')", source)

    def test_native_retry_retains_identity_and_trusted_launcher(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertNotIn('Flags: uninsdeletekey', source)
        self.assertIn('--prepare-native-recovery', source)
        self.assertIn('native-removal\\BioGuardLifecycle.exe', source)

    def test_uninstall_requires_online_approval_and_keeps_identity(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertIn('function InitializeUninstall', source)
        self.assertIn('--launch-target-user', source)
        self.assertIn("BrokerState <> 'approved'", source)
        self.assertIn('TargetUserSID', source)

    def test_uninstall_does_not_kill_by_name_or_delete_elevated_user_credentials(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertNotIn('taskkill', source)
        self.assertNotIn("{userappdata}\\ADBioGuard", source)
        self.assertNotIn("{localappdata}\\AD BioGuard", source)
        self.assertIn("BrokerCommand('cleanup', '')", source)

    def test_separate_helper_is_built_and_bundled(self):
        source = (ROOT / 'builders/windows/bioguard_installer.iss').read_text(encoding='utf-8')
        self.assertIn('BioGuardLifecycle.exe', source)
        self.assertIn('dontcopy', source)
        workflow = (ROOT / '.github/workflows/build.yml').read_text()
        self.assertIn('bioguard-lifecycle.spec', workflow)
