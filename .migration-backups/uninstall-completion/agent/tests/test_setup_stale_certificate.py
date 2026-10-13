import unittest
from unittest.mock import Mock, patch
from core.network.errors import BackendResponseError


class StaleCertificateTests(unittest.TestCase):
    def test_rejected_old_certificate_uses_new_token_with_fresh_enrollment(self):
        from app.lifecycle_entry import activation_status
        client = Mock()
        ready = {'state': 'active', 'device_uuid': 'pc'}
        client.post.side_effect = [BackendResponseError('rejected', status_code=403), ready]
        with patch('api.client.get_default_client', return_value=client), \
             patch('core.cert.load_cert', return_value={'cert_id': 'old'}), \
             patch('core.config.DEVICE_UUID', 'pc'), \
             patch('platform_adapters.windows.lifecycle.ProtectedSetup'), \
             patch('services.setup_enrollment.SetupEnrollment') as setup, \
             patch('core.activation.activate_org') as activate:
            self.assertEqual(activation_status('new-token'), ready)
            callback = setup.call_args.args[3]
            callback('new-token', keypair=('public', 'private'))
            activate.assert_called_once_with('new-token', force=True, keypair=('public', 'private'))

    def test_server_failure_does_not_replace_existing_certificate(self):
        from app.lifecycle_entry import activation_status
        client = Mock()
        client.post.side_effect = BackendResponseError('busy', status_code=503)
        with patch('api.client.get_default_client', return_value=client), \
             patch('core.cert.load_cert', return_value={'cert_id': 'old'}), \
             patch('platform_adapters.windows.lifecycle.ProtectedSetup'), \
             patch('services.setup_enrollment.SetupEnrollment') as setup:
            with self.assertRaises(BackendResponseError):
                activation_status('new-token')
            setup.return_value.activate.assert_not_called()
