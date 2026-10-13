import unittest
from unittest.mock import Mock
from services.supervision import Supervisor


class Process:
    pid=123
    def __init__(self):self.code=None
    def poll(self):return self.code
    def close(self):pass


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.launch=Mock(side_effect=Process)
        self.record=Mock()
        self.find=Mock(return_value=None)
        self.exit_record=Mock(return_value={})
        self.guard=Supervisor(self.find,self.launch,self.record,self.exit_record)

    def tick(self,now=0,allowed=True,pause=False):
        self.guard.tick(now,allowed=allowed,paused=pause)

    def test_unexpected_exit_restarts_and_records_observed_exit(self):
        self.tick();self.guard.process.code=1;self.tick(10);self.tick(20)
        self.assertEqual(self.launch.call_count,2)
        self.assertIn('agent_unexpected_exit',[call.args[0] for call in self.record.call_args_list])

    def test_authorized_pause_does_not_restart(self):
        self.tick();self.guard.process.code=1;self.tick(10,pause=True)
        self.assertEqual(self.launch.call_count,1)
        self.tick(20)
        self.assertEqual(self.launch.call_count,2)

    def test_prerelease_exit_is_respected(self):
        self.tick();self.guard.process.code=0
        self.exit_record.return_value={'pid':123,'reason':'prerelease_exit','running':False}
        self.tick(10);self.tick(30)
        self.assertEqual(self.launch.call_count,1)

    def test_existing_agent_is_attached_without_duplicate_launch(self):
        self.find.return_value=Process()
        self.tick()
        self.launch.assert_not_called()

    def test_denied_policy_prevents_launch(self):
        self.tick(allowed=False)
        self.launch.assert_not_called()

    def test_failures_back_off_instead_of_looping(self):
        self.launch.side_effect=OSError('failure')
        self.tick();self.tick(1);self.tick(2)
        self.assertEqual(self.launch.call_count,1)
        self.assertEqual(self.record.call_args.args[0],'restart_failed')

    def test_old_exit_record_cannot_suppress_different_process(self):
        self.tick();self.guard.process.code=1
        self.exit_record.return_value={'pid':456,'reason':'prerelease_exit','running':False}
        self.tick(10);self.tick(20)
        self.assertEqual(self.launch.call_count,2)

    def test_immediately_crashing_children_back_off(self):
        self.tick();self.guard.process.code=1;self.tick(1);self.tick(2)
        self.assertEqual(self.launch.call_count,1)
        self.tick(11);self.guard.process.code=1;self.tick(12);self.tick(20)
        self.assertEqual(self.launch.call_count,2)
