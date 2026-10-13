import json
import unittest

from services.authorization import SessionAuthority
from services.local_protocol import (decode_request, dispatch_request, PeerIdentity,
                                     RequestHistory, ProtocolError)


class LocalProtocolTests(unittest.TestCase):
    def setUp(self):
        self.authority = SessionAuthority("generation-1")
        self.peer = PeerIdentity(1, "S-1-5-21-100")
        self.history = RequestHistory()

    def request(self, command="begin_attempt", **changes):
        data = {"version": 1, "request_id": "request-1", "command": command,
                "session_id": 1, "user_sid": "S-1-5-21-100", "generation": "generation-1"}
        data.update(changes)
        return decode_request(json.dumps(data).encode())

    def dispatch(self, request):
        return dispatch_request(request, self.peer, self.authority, self.history)

    def test_begin_only_returns_pending_state(self):
        response = self.dispatch(self.request())
        self.assertTrue(response["ok"])
        self.assertEqual(response["state"], "MFA_PENDING")
        self.assertEqual(response["attempt_id"], self.authority.snapshot(1).attempt_id)

    def test_wrong_sid_or_session_cannot_mutate_authority(self):
        for changes in ({"user_sid": "S-1-5-21-200"}, {"session_id": 2}):
            with self.subTest(changes=changes):
                response = self.dispatch(self.request(**changes))
                self.assertEqual(response["error"], "IDENTITY_MISMATCH")
                self.assertIsNone(self.authority.snapshot(1).attempt_id)

    def test_previous_generation_cannot_start_attempt(self):
        self.assertEqual(self.dispatch(self.request(generation="generation-old"))["error"], "STALE_GENERATION")
        self.assertIsNone(self.authority.snapshot(1).attempt_id)

    def test_replayed_request_does_not_replace_attempt(self):
        request = self.request()
        first = self.dispatch(request)
        self.assertEqual(self.dispatch(request)["error"], "REPLAYED_REQUEST")
        self.assertEqual(self.authority.snapshot(1).attempt_id, first["attempt_id"])

    def test_cancel_requires_current_attempt(self):
        first = self.dispatch(self.request())
        wrong = self.request("cancel_attempt", request_id="cancel-1", attempt_id="wrong")
        self.assertEqual(self.dispatch(wrong)["error"], "STALE_ATTEMPT")
        valid = self.request("cancel_attempt", request_id="cancel-2", attempt_id=first["attempt_id"])
        self.assertTrue(self.dispatch(valid)["ok"])
        self.assertIsNone(self.authority.snapshot(1).attempt_id)

    def test_connection_limit_never_evicts_replay_history(self):
        first = self.request("status", request_id="request-0")
        self.assertTrue(self.dispatch(first)["ok"])
        for index in range(1, 256):
            self.assertTrue(self.dispatch(self.request("status", request_id=f"request-{index}"))["ok"])
        self.assertEqual(self.dispatch(self.request(request_id="request-256"))["error"], "CONNECTION_LIMIT")
        self.assertEqual(self.dispatch(first)["error"], "REPLAYED_REQUEST")

    def test_commands_cannot_authorize_stop_or_execute(self):
        for command in ("unlock", "stop", "execute", "verified"):
            with self.subTest(command=command), self.assertRaises(ProtocolError):
                self.request(command)

    def test_malformed_extra_duplicate_oversized_fields_rejected(self):
        valid = {"version": 1, "request_id": "request-1", "command": "status",
                 "session_id": 1, "user_sid": "S-1-5-21-100", "generation": "generation-1"}
        frames = [b'{', b'[]', b'\xff', b'x' * 65537,
                  json.dumps({**valid, "verified": True}).encode(),
                  json.dumps({**valid, "version": True}).encode(),
                  json.dumps({**valid, "session_id": True}).encode(),
                  json.dumps(valid).replace('"version": 1', '"version": 1, "version": 1').encode()]
        for frame in frames:
            with self.subTest(frame=frame[:80]), self.assertRaises(ProtocolError):
                decode_request(frame)

