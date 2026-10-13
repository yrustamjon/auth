from unittest import TestCase
from apps.log.similarity import log_similarity


class LogSimilarityTests(TestCase):
    def test_saved_score(self):
        self.assertEqual(log_similarity('Yuz tasdiqlandi (similarity=0.9234)'), 0.9234)

    def test_zero(self):
        self.assertEqual(log_similarity('Yuz tanilmadi (similarity=0.0000)'), 0.0)

    def test_missing_or_invalid_score(self):
        for cause in (None, '', 'Yuz tasdiqlandi', 'similarity=nan', 'similarity=1.5'):
            self.assertIsNone(log_similarity(cause))
