from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from builders.archive_package import archive_package, read_version


class ReleaseArchiveTests(unittest.TestCase):
    def test_independent_versions_timestamp_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for system, version in [('windows', '1.2.3'), ('linux', '0.4.0')]:
                folder = root / 'releases' / system
                folder.mkdir(parents=True)
                (folder / 'VERSION').write_text(version)
            source = root / 'installer.exe'
            source.write_bytes(b'package contents')
            now = datetime(2026, 10, 8, 13, 30, tzinfo=timezone.utc)
            target = archive_package('windows', source, root=root, now=now, commit='abc123')
            self.assertEqual(target.relative_to(root).as_posix(),
                'releases/windows/1.2.3/2026-10-08_18-30-00-000000_UZT')
            manifest = json.loads((target / 'manifest.json').read_text())
            self.assertEqual(manifest['files'][0]['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(manifest['version'], '1.2.3')
            self.assertEqual(manifest['commit'], 'abc123')
            self.assertEqual((target / 'SHA256SUMS.txt').read_text(),
                hashlib.sha256(source.read_bytes()).hexdigest() + '  installer.exe\n')
            self.assertEqual(read_version('linux', root), '0.4.0')
            with self.assertRaises(FileExistsError):
                archive_package('windows', source, root=root, now=now, commit='abc123')
            self.assertEqual((target / source.name).read_bytes(), source.read_bytes())

    def test_invalid_version_cannot_escape_os_folder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / 'releases/windows'
            folder.mkdir(parents=True)
            (folder / 'VERSION').write_text('../../outside')
            with self.assertRaises(ValueError):
                read_version('windows', root)
            with self.assertRaises(ValueError):
                read_version('../linux', root)


if __name__ == '__main__':
    unittest.main()
