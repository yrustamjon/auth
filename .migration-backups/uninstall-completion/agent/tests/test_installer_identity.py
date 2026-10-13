from pathlib import Path
import unittest

class InstallerIdentityTests(unittest.TestCase):
    def test_pre_directory_activation_does_not_expand_uninitialized_app(self):
        source=(Path(__file__).resolve().parents[1]/'builders/windows/bioguard_installer.iss').read_text()
        initialization=source.split('procedure InitializeWizard;',1)[1].split('procedure CurPageChanged',1)[0]
        self.assertNotIn("ExpandConstant('{app}')", initialization)
        self.assertNotIn('ExecAsOriginalUser(', initialization)
        page_change=source.split('procedure CurPageChanged',1)[1].split('function NextButtonClick',1)[0]
        self.assertIn('WizardDirValue',page_change)
        self.assertIn('ExecAsOriginalUser',page_change)
        self.assertIn('InstallBrokerStarted',page_change)

    def test_activation_and_launch_preserve_original_desktop_user_through_uac(self):
        source=(Path(__file__).resolve().parents[1]/'builders/windows/bioguard_installer.iss').read_text()
        self.assertIn('ExecAsOriginalUser',source)
        self.assertIn('runasoriginaluser',source)
        self.assertIn('TargetUserSID',source)
        self.assertIn('Root: HKU',source)
        self.assertNotIn('Root: HKCU',source)

    def test_agent_and_lifecycle_helper_do_not_request_elevation(self):
        root=Path(__file__).resolve().parents[1]
        for name in ('bioguard.spec','bioguard-lifecycle.spec'):
            self.assertIn('uac_admin=False',(root/'builders/windows'/name).read_text())
