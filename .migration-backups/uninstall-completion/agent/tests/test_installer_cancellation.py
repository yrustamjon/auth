"""Source regression checks; native installer interaction still requires a VM."""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'builders/windows/bioguard_installer.iss'

def source_code():
    code = SOURCE.read_text(encoding='utf-8')
    include = SOURCE.with_name('installer_network.iss')
    if include.exists():
        code += '\n' + include.read_text(encoding='utf-8')
    return code


class InstallerCancellationTests(unittest.TestCase):
    def test_activation_page_and_gate_precede_file_copy(self):
        code = source_code()
        self.assertIn('CreateInputQueryPage(wpWelcome', code)
        self.assertIn('function PrepareToInstall', code)
        self.assertIn("BrokerState <> 'ready'", code)
        run = code.split('[Run]', 1)[1].split('[Code]', 1)[0]
        self.assertNotIn('--installer-activation', run)

    def test_native_cancel_and_optional_agent_launch_are_preserved(self):
        code = source_code()
        self.assertIn('AllowCancelDuringInstall=yes', code)
        self.assertIn('nowait postinstall skipifsilent runasoriginaluser', code)
        self.assertNotIn('CancelButtonClick', code)
        self.assertIn('KillTimer', code)
        self.assertIn('ewNoWait', code)

    def test_tokens_are_sent_over_pipe_not_helper_arguments(self):
        code = source_code()
        self.assertIn('BrokerCommand', code)
        self.assertIn("BrokerCommand('activate', ActivationPage.Values[0])", code)
        self.assertNotIn('Parameters: "--installer-activation"', code)
        self.assertIn('GetNamedPipeServerProcessId', code)


if __name__ == '__main__':
    unittest.main()
