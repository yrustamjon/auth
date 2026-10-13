import unittest
from unittest.mock import Mock, patch
from app.installer_activation import provision


class InstallerActivationTests(unittest.TestCase):
    def test_pasted_token_uses_existing_activation_without_manual_device_fields(self):
        activate = Mock(return_value={'certificate': {'cert_id': 'example'}})
        self.assertEqual(provision('  org-token\r\n', activate), activate.return_value)
        activate.assert_called_once_with('org-token')

    def test_blank_token_does_not_contact_server(self):
        activate = Mock()
        with self.assertRaises(ValueError):
            provision('   ', activate)
        activate.assert_not_called()

    def test_installer_entrypoint_does_not_start_normal_agent(self):
        import main
        with patch('sys.argv', ['BioGuard.exe', '--installer-activation']), \
                patch('app.installer_activation.run') as setup, \
                patch('app.bootstrap.run') as agent:
            main.main()
        setup.assert_called_once_with()
        agent.assert_not_called()
