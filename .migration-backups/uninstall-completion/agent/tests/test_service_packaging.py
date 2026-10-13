from pathlib import Path
import runpy
import types
import unittest


class PackagingTests(unittest.TestCase):
    def test_separate_service_bundle_has_no_gui_payload(self):
        root = Path(__file__).resolve().parents[1]
        spec = root / 'builders/windows/bioguard-service.spec'
        capture = {}
        def analysis(scripts, **kwargs):
            capture.update(scripts=scripts, **kwargs)
            return types.SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
        def executable(*args, **kwargs):
            capture['exe'] = kwargs
        runpy.run_path(str(spec), init_globals={
            'SPECPATH': str(spec.parent), 'Analysis': analysis,
            'PYZ': lambda *a, **k: None, 'EXE': executable,
            'COLLECT': lambda *a, **k: None})
        self.assertEqual(capture['scripts'], [str(root / 'platform_adapters/windows/service_entry.py')])
        self.assertEqual(capture['exe']['name'], 'BioGuardService')
        self.assertEqual(capture['datas'], [])
        self.assertNotIn('webview', capture['hiddenimports'])


if __name__ == '__main__':
    unittest.main()
