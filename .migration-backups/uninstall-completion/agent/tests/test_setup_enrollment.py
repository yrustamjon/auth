import unittest
from unittest.mock import Mock
from core.network.errors import BackendUnavailableError, BackendResponseError


class SetupEnrollmentTests(unittest.TestCase):
    def controller(self):
        from services.setup_enrollment import SetupEnrollment
        self.store = Mock()
        self.store.load.return_value = None
        self.client = Mock()
        self.activate, self.save_cert = Mock(), Mock()
        self.activate.return_value = {'certificate': {'cert_id': 'new', 'pc_id': 'fixture'}}
        return SetupEnrollment('fixture', self.store, self.client, self.activate, self.save_cert)

    def test_persist_key_before_token_consumption(self):
        controller = self.controller()
        self.activate.side_effect = lambda token, **kwargs: (
            self.assertTrue(self.store.save.called) or {'certificate': {'cert_id': 'new', 'pc_id': 'fixture'}})
        controller.activate('secret')
        persisted = self.store.save.call_args.args[0]
        self.assertNotIn('secret', str(persisted))
        self.assertIn('private_key', persisted)
        self.store.clear.assert_called_once()

    def test_lost_response_keeps_prepared_key(self):
        controller = self.controller()
        self.activate.side_effect = BackendUnavailableError('lost')
        with self.assertRaises(BackendUnavailableError):
            controller.activate('secret')
        self.store.clear.assert_not_called()

    def test_committed_activation_can_be_recovered_without_token(self):
        controller = self.controller()
        from services.removal import recovery_keypair
        private, public = recovery_keypair()
        self.store.load.return_value = {'device_uuid': 'fixture', 'private_key': private, 'public_key': public}
        self.client.post.return_value = {'certificate': {'pc_id': 'fixture', 'cert_id': 'recovered'}}
        self.assertTrue(controller.recover())
        self.activate.assert_not_called()
        self.save_cert.assert_called_once_with({'pc_id': 'fixture', 'cert_id': 'recovered'}, private)
        self.store.clear.assert_called_once()

    def test_missing_commit_does_not_clear_prepared_key(self):
        controller = self.controller()
        self.store.load.return_value = {'device_uuid': 'fixture', 'private_key': 'unused', 'public_key': 'unused'}
        self.client.post.side_effect = BackendResponseError('missing', status_code=404)
        self.assertFalse(controller.recover())
        self.store.clear.assert_not_called()

    def test_recovery_refuses_wrong_device_response(self):
        controller = self.controller()
        self.store.load.return_value = {'device_uuid': 'fixture', 'private_key': 'unused', 'public_key': 'unused'}
        self.client.post.return_value = {'certificate': {'pc_id': 'other', 'cert_id': 'not-ours'}}
        with self.assertRaises(ValueError):
            controller.recover()
        self.save_cert.assert_not_called()
