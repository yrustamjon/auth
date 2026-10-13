import unittest
from unittest.mock import Mock


class LifecycleBrokerTests(unittest.TestCase):
    def test_delayed_verify_returns_pending_then_ready_without_repeating_request(self):
        import threading
        broker = self.broker()
        release = threading.Event()
        def delayed(token):
            release.wait(2)
            return {'organization': 'Example', 'device_uuid': 'pc'}
        self.activation.side_effect = delayed
        try:
            self.assertEqual(broker.dispatch('verify')['state'], 'pending')
            self.assertEqual(broker.dispatch('state')['state'], 'pending')
        finally:
            release.set()
            broker.join()
        self.assertEqual(broker.dispatch('state')['state'], 'ready')
        self.activation.assert_called_once_with(None)

    def broker(self, mode='install'):
        from services.lifecycle_broker import LifecycleBroker
        self.activation = Mock(return_value={'organization': 'Example', 'device_uuid': 'pc'})
        self.removal = Mock()
        return LifecycleBroker(mode, self.activation, self.removal, 'S-1-5-21-123', 'Ali')

    def test_initial_activation_does_not_silently_skip_status(self):
        broker = self.broker()
        broker.dispatch('inspect')
        broker.join()
        self.activation.assert_called_once_with(None)
        self.assertEqual(broker.snapshot()['state'], 'ready')

    def test_failed_activation_does_not_allow_installation(self):
        broker = self.broker()
        self.activation.side_effect = ValueError('offline SECRET')
        broker.dispatch('activate', 'SECRET')
        broker.join()
        reply = broker.snapshot()
        self.assertEqual(reply['state'], 'error')
        self.assertNotIn('SECRET', str(reply))

    def test_status_poll_does_not_repeat_backend_calls(self):
        broker = self.broker()
        broker.dispatch('activate', 'token')
        broker.join()
        for _ in range(3):
            broker.dispatch('state')
        self.activation.assert_called_once_with('token')

    def test_uninstall_check_is_not_begin(self):
        broker = self.broker('uninstall')
        self.removal.check.return_value = {'organization': 'Example'}
        broker.dispatch('check', 'code')
        broker.join()
        self.removal.begin.assert_not_called()
        self.assertEqual(broker.snapshot()['state'], 'checked')

    def test_uninstall_cannot_complete_before_begin(self):
        broker = self.broker('uninstall')
        with self.assertRaises(ValueError):
            broker.dispatch('cleanup')
        self.removal.cleanup_and_complete.assert_not_called()

    def test_resume_requires_online_pending_state(self):
        broker = self.broker('uninstall')
        self.removal.resume.return_value = {'state': 'active'}
        broker.dispatch('resume')
        broker.join()
        self.assertEqual(broker.snapshot()['state'], 'error')

    def test_operation_result_keeps_target_identity(self):
        broker = self.broker()
        self.assertEqual(broker.snapshot()['target_sid'], 'S-1-5-21-123')
        self.assertEqual(broker.snapshot()['target_user'], 'Ali')

    def test_broker_modes_do_not_accept_other_operations(self):
        broker = self.broker()
        with self.assertRaises(ValueError):
            broker.dispatch('begin', 'code')
        self.removal.begin.assert_not_called()
