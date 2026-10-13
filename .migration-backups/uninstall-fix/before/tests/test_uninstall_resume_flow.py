import unittest
from unittest.mock import Mock
from core.network.errors import BackendResponseError, BackendUnavailableError
from services.removal import RemovalController
from services.lifecycle_broker import LifecycleBroker
from tests.test_removal import MemoryReceipt


class UninstallResumeFlowTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryReceipt()
        self.api=Mock()
        self.cleanup=Mock()
        self.controller=RemovalController(self.api,'pc-test',self.store,self.cleanup)

    def test_check_recovers_existing_approved_operation_without_reclaiming_code(self):
        self.api.post.return_value={'state':'removal_pending'}
        self.controller.begin('a'*43)
        def post(path,data,**kwargs):
            if path.endswith('/check/'):
                raise BackendResponseError('DEVICE_NOT_REMOVABLE',status_code=403)
            return {'state':'removal_pending','operation_id':self.store.value['operation_id']}
        self.api.reset_mock();self.api.post.side_effect=post
        result=self.controller.check('a'*43)
        self.assertEqual(result['state'],'removal_pending')
        self.assertEqual([c.args[0] for c in self.api.post.call_args_list],['/api/agent/removal/status/'])
        self.cleanup.assert_not_called()

    def test_expired_draft_does_not_block_a_new_valid_code(self):
        self.store.value=dict(self.controller._draft())
        self.api.post.side_effect=[BackendResponseError('not found',status_code=404),{'state':'active'}]
        self.assertEqual(self.controller.check('b'*43)['state'],'active')
        self.assertTrue(self.api.post.call_args.args[0].endswith('/check/'))

    def test_check_does_not_treat_offline_receipt_as_approval(self):
        self.store.value=dict(self.controller._draft())
        self.api.post.side_effect=BackendUnavailableError('offline')
        with self.assertRaises(BackendUnavailableError):self.controller.check('a'*43)
        self.cleanup.assert_not_called()

    def test_broker_check_opens_uninstall_for_already_approved_operation(self):
        removal=Mock()
        removal.check.return_value={'state':'removal_pending'}
        broker=LifecycleBroker('uninstall',None,removal,'S-1-5-21-123','Ali')
        broker.dispatch('check','a'*43);broker.join()
        self.assertEqual(broker.snapshot()['state'],'approved')
        removal.begin.assert_not_called()

    def test_lost_begin_reply_recovers_approval_without_false_error(self):
        self.api.post.side_effect=[BackendUnavailableError('reply lost'),{'state':'removal_pending'}]
        self.assertEqual(self.controller.begin('a'*43)['state'],'removal_pending')
        self.cleanup.assert_not_called()

    def test_begin_still_fails_if_recovery_cannot_prove_approval(self):
        self.api.post.side_effect=[BackendUnavailableError('reply lost'),BackendResponseError('not found',status_code=404)]
        with self.assertRaises(BackendUnavailableError):self.controller.begin('a'*43)
        self.assertIsNotNone(self.store.value)

    def test_bad_code_response_is_not_replaced_with_automatic_approval(self):
        self.api.post.side_effect=BackendResponseError('INVALID_REMOVAL_CODE',status_code=403)
        with self.assertRaises(BackendResponseError):self.controller.begin('wrong')
        self.assertEqual(self.api.post.call_count,1)

    def test_code_error_explains_removal_code_without_echoing_server_secrets(self):
        removal=Mock()
        removal.check.side_effect=BackendResponseError('SECRET',status_code=403,response_body='{"detail":"INVALID_REMOVAL_CODE","token":"SECRET"}')
        broker=LifecycleBroker('uninstall',None,removal,'S-1-5-21-123','Ali')
        broker.dispatch('check','SECRET');broker.join()
        self.assertIn('Org token emas',broker.snapshot()['message'])
        self.assertNotIn('SECRET',str(broker.snapshot()))

    def test_unknown_server_error_does_not_expose_raw_body(self):
        removal=Mock()
        removal.check.side_effect=BackendResponseError('SECRET',status_code=500,response_body='{"detail":"SECRET"}')
        broker=LifecycleBroker('uninstall',None,removal,'S-1-5-21-123','Ali')
        broker.dispatch('check','SECRET');broker.join()
        self.assertNotIn('SECRET',str(broker.snapshot()))
