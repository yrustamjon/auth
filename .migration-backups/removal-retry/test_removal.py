import unittest
from unittest.mock import Mock

from core.network.errors import BackendUnavailableError, BackendResponseError


class MemoryReceipt:
    def __init__(self):
        self.value = None
        self.events = []

    def load(self):
        return self.value

    def save(self, value):
        self.events.append('persist')
        self.value = dict(value)

    def clear(self):
        self.events.append('clear')
        self.value = None


class RemovalControllerTests(unittest.TestCase):
    def controller(self):
        from services.removal import RemovalController
        self.store = MemoryReceipt()
        self.api = Mock()
        self.cleanup = Mock()
        self.api.post.return_value = {'state': 'removal_pending'}
        return RemovalController(self.api, 'pc-test', self.store, self.cleanup)

    def test_offline_check_does_not_clean_or_begin(self):
        controller = self.controller()
        self.api.post.side_effect = BackendUnavailableError('offline')
        with self.assertRaises(BackendUnavailableError):
            controller.check('a' * 43)
        self.cleanup.assert_not_called()
        self.assertEqual(self.api.post.call_args.args[0], '/api/agent/removal/check/')

    def test_persists_recovery_before_begin_and_never_persists_code(self):
        controller = self.controller()
        def post(path, data, **kwargs):
            self.assertIsNotNone(self.store.value)
            self.assertNotIn('code', self.store.value)
            self.assertNotIn('a' * 43, str(self.store.value))
            return {'operation_id': self.store.value['operation_id'], 'state': 'removal_pending'}
        self.api.post.side_effect = post
        controller.begin('a' * 43)
        self.cleanup.assert_not_called()

    def test_lost_begin_response_retains_recovery(self):
        controller = self.controller()
        self.api.post.side_effect = BackendUnavailableError('lost response')
        with self.assertRaises(BackendUnavailableError):
            controller.begin('a' * 43)
        self.assertIsNotNone(self.store.value)
        self.cleanup.assert_not_called()

    def test_offline_status_never_cleans(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.api.post.side_effect = BackendUnavailableError('offline')
        with self.assertRaises(BackendUnavailableError):
            controller.cleanup_and_complete()
        self.cleanup.assert_not_called()

    def test_cleanup_failure_keeps_receipt_and_never_completes(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.cleanup.side_effect = OSError('locked file')
        self.api.reset_mock()
        with self.assertRaises(OSError):
            controller.cleanup_and_complete()
        self.assertIsNotNone(self.store.value)
        self.assertEqual([call.args[0] for call in self.api.post.call_args_list], ['/api/agent/removal/status/'])

    def test_cleanup_before_completion_and_clear_after_ack(self):
        controller = self.controller()
        controller.begin('a' * 43)
        events = []
        self.cleanup.side_effect = lambda: events.append('clean')
        def post(path, data, **kwargs):
            if path.endswith('complete/'):
                self.assertEqual(events, ['clean'])
                return {'state': 'removed'}
            return {'state': 'removal_pending'}
        self.api.post.side_effect = post
        controller.cleanup_and_complete()
        self.assertIsNone(self.store.value)

    def test_recovery_signing_does_not_load_device_private_key(self):
        controller = self.controller()
        controller.begin('a' * 43)
        controller.resume()
        kwargs = self.api.post.call_args.kwargs
        headers = kwargs['request_signer']('POST', '/api/agent/removal/status/', b'{}')
        self.assertEqual(headers['X-Cert-ID'], 'removal:' + self.store.value['operation_id'])
        self.assertEqual(headers['X-PC-ID'], 'pc-test')

    def test_removed_operation_never_cleans_a_new_installation(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.api.post.return_value = {'state': 'removed'}
        controller.cleanup_and_complete()
        self.cleanup.assert_not_called()
        self.assertIsNone(self.store.value)

    def test_pending_receipt_for_other_device_is_rejected(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.store.value['device_uuid'] = 'another-pc'
        with self.assertRaises(ValueError):
            controller.resume()
        self.cleanup.assert_not_called()

    def test_unapproved_state_cannot_clean(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.api.post.return_value = {'state': 'active'}
        with self.assertRaises(ValueError):
            controller.cleanup_and_complete()
        self.cleanup.assert_not_called()

    def test_complete_lost_response_retains_receipt_and_local_cleanup_state(self):
        controller = self.controller()
        controller.begin('a' * 43)
        self.api.post.side_effect = [{'state': 'removal_pending'}, BackendUnavailableError('lost ack')]
        with self.assertRaises(BackendUnavailableError):
            controller.cleanup_and_complete()
        self.assertTrue(self.store.value['local_cleanup_done'])
        self.api.post.side_effect = [{'state': 'removal_pending'}, {'state': 'removed'}]
        controller.cleanup_and_complete()
        self.cleanup.assert_called_once()

    def test_no_receipt_cannot_resume(self):
        controller = self.controller()
        with self.assertRaises(ValueError):
            controller.resume()
        self.api.post.assert_not_called()

    def test_completed_receipt_starts_fresh_removal_after_reinstallation(self):
        controller = self.controller()
        controller.begin('a' * 43)
        old = dict(self.store.value)
        self.store.value['local_cleanup_done'] = True
        def post(path, data, **kwargs):
            if path.endswith('status/'):
                return {'state': 'removed'}
            if data['operation_id'] == old['operation_id']:
                raise BackendResponseError('existing operation', status_code=409)
            return {'operation_id': data['operation_id'], 'state': 'removal_pending'}
        self.api.post.side_effect = post
        result = controller.begin('b' * 43)
        self.assertEqual(result['state'], 'removal_pending')
        self.assertNotEqual(self.store.value['operation_id'], old['operation_id'])
        self.assertNotEqual(self.store.value['public_key'], old['public_key'])
        self.assertFalse(self.store.value['local_cleanup_done'])

    def test_retry_recovers_pending_operation_without_claiming_code_again(self):
        controller = self.controller()
        controller.begin('a' * 43)
        old = dict(self.store.value)
        def post(path, data, **kwargs):
            if path.endswith('begin/'):
                raise BackendResponseError('already claimed', status_code=409)
            return {'operation_id': old['operation_id'], 'state': 'removal_pending'}
        self.api.post.side_effect = post
        self.assertEqual(controller.begin('a' * 43)['state'], 'removal_pending')
        self.assertEqual(self.store.value, old)

    def test_offline_existing_receipt_is_preserved(self):
        controller = self.controller()
        controller.begin('a' * 43)
        old = dict(self.store.value)
        self.api.post.side_effect = BackendUnavailableError('offline')
        with self.assertRaises(BackendUnavailableError):
            controller.begin('b' * 43)
        self.assertEqual(self.store.value, old)

    def test_unclaimed_persisted_receipt_can_retry_begin(self):
        controller = self.controller()
        self.api.post.side_effect = BackendUnavailableError('lost before claim')
        with self.assertRaises(BackendUnavailableError):
            controller.begin('a' * 43)
        old = dict(self.store.value)
        self.api.post.side_effect = [
            BackendResponseError('not found', status_code=404),
            {'operation_id': old['operation_id'], 'state': 'removal_pending'},
        ]
        self.assertEqual(controller.begin('a' * 43)['state'], 'removal_pending')
        self.assertEqual(self.store.value, old)
