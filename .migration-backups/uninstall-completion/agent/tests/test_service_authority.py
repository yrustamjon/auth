import unittest

from services.authorization import SessionAuthority, IdentityMismatchError


class SessionAuthorityTests(unittest.TestCase):
    def test_new_attempt_never_authorizes_desktop(self):
        authority = SessionAuthority("generation-1")
        attempt = authority.begin_attempt(1, "S-1-5-21-100")
        snapshot = authority.snapshot(1)
        self.assertEqual(snapshot.state, "MFA_PENDING")
        self.assertEqual(snapshot.attempt_id, attempt.attempt_id)
        self.assertEqual(attempt.generation, "generation-1")

    def test_same_session_cannot_change_user_without_invalidation(self):
        authority = SessionAuthority("generation-1")
        original = authority.begin_attempt(1, "S-1-5-21-100")
        with self.assertRaises(IdentityMismatchError):
            authority.begin_attempt(1, "S-1-5-21-200")
        self.assertEqual(authority.snapshot(1).attempt_id, original.attempt_id)

    def test_invalidation_clears_old_attempt_and_user_binding(self):
        authority = SessionAuthority("generation-1")
        original = authority.begin_attempt(1, "S-1-5-21-100")
        authority.invalidate_session(1)
        self.assertIsNone(authority.snapshot(1).attempt_id)
        replacement = authority.begin_attempt(1, "S-1-5-21-200")
        self.assertNotEqual(replacement.attempt_id, original.attempt_id)
        self.assertEqual(authority.snapshot(1).state, "MFA_PENDING")

    def test_restart_does_not_reuse_authority_or_attempt(self):
        old = SessionAuthority("generation-1")
        attempt = old.begin_attempt(1, "S-1-5-21-100")
        new = SessionAuthority("generation-2")
        self.assertIsNone(new.snapshot(1).attempt_id)
        replacement = new.begin_attempt(1, "S-1-5-21-100")
        self.assertNotEqual(replacement.attempt_id, attempt.attempt_id)
        self.assertEqual(replacement.generation, "generation-2")

    def test_unknown_session_is_pending(self):
        self.assertEqual(SessionAuthority("generation-1").snapshot(17).state, "MFA_PENDING")

    def test_noninteractive_session_is_rejected(self):
        authority = SessionAuthority("generation-1")
        for session in (0, -1, True, "1"):
            with self.subTest(session=session), self.assertRaises(ValueError):
                authority.begin_attempt(session, "S-1-5-21-100")

