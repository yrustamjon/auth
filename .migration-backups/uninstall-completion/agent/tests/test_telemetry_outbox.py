import tempfile
import unittest
from pathlib import Path
from services.telemetry import EventOutbox, Reporter


class TelemetryOutboxTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/'events.sqlite3'
        self.queue=EventOutbox(self.path)

    def test_unconfirmed_previous_process_is_logged_without_claiming_task_manager(self):
        self.queue.begin()
        next_queue=EventOutbox(self.path);next_queue.begin()
        kinds=[event['kind'] for event in next_queue.pending()]
        self.assertIn('previous_exit_unconfirmed',kinds)
        self.assertNotIn('task_manager_kill',kinds)

    def test_clean_exit_is_not_reported_as_an_unconfirmed_exit(self):
        self.queue.begin();self.queue.finish('prerelease_exit')
        EventOutbox(self.path).begin()
        self.assertNotIn('previous_exit_unconfirmed',[event['kind'] for event in self.queue.pending()])

    def test_failed_send_keeps_durable_queue(self):
        self.queue.begin()
        reporter=Reporter(self.queue,lambda payload:(_ for _ in ()).throw(OSError('offline')))
        reporter.flush()
        self.assertTrue(EventOutbox(self.path).pending())

    def test_only_server_acknowledged_ids_are_removed(self):
        self.queue.begin();pending=self.queue.pending()
        reporter=Reporter(self.queue,lambda payload:{'accepted':[pending[0]['id']]})
        reporter.flush()
        self.assertNotIn(pending[0]['id'],[e['id'] for e in self.queue.pending()])

    def test_exit_is_idempotent(self):
        self.queue.begin();self.queue.finish('prerelease_exit');self.queue.finish('window_closed')
        self.assertEqual(sum(e['kind']=='agent_exited' for e in self.queue.pending()),1)
