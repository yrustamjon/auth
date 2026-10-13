from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from builders.archive_package import archive_package
from builders.publish_release import publish, release_plan


class ReleasePublishingTests(unittest.TestCase):
    def package(self, root):
        version = root / 'releases/windows'
        version.mkdir(parents=True)
        (version / 'VERSION').write_text('1.0.0')
        binary = root / 'setup.exe'
        binary.write_bytes(b'installer')
        return archive_package('windows', binary, root=root,
            now=datetime(2026, 10, 8, 13, 30, tzinfo=timezone.utc), commit='a' * 40)

    def test_os_timestamp_and_manifest_bound_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = self.package(Path(temporary))
            plan, files = release_plan(folder)
            self.assertEqual(plan['tag_name'], 'windows-v1.0.0-20261008-183000-000000')
            self.assertTrue(plan['draft'])
            self.assertTrue(plan['prerelease'])
            self.assertEqual(plan['target_commitish'], 'a' * 40)
            self.assertEqual([file.name for file in files], ['setup.exe', 'manifest.json', 'SHA256SUMS.txt'])
            (folder / 'setup.exe').write_bytes(b'modified')
            with patch('builders.publish_release._api') as api:
                with self.assertRaises(ValueError):
                    publish(folder, 'owner/repo', 'test-token')
                api.assert_not_called()

    def test_upload_failure_keeps_release_unpublished(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = self.package(Path(temporary))
            with patch('builders.publish_release._api', return_value={'id': 1, 'upload_url': 'url'}) as api, \
                 patch('builders.publish_release._upload', side_effect=OSError('upload failed')):
                with self.assertRaises(OSError):
                    publish(folder, 'owner/repo', 'test-token')
            self.assertEqual(api.call_count, 1)
            self.assertTrue(api.call_args.args[3]['draft'])

    def test_all_assets_uploaded_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = self.package(Path(temporary))
            order = []
            def api(method, *args):
                order.append(method)
                return {'id': 1, 'upload_url': 'url', 'html_url': 'https://github.com/owner/repo/releases/tag/test'}
            with patch('builders.publish_release._api', side_effect=api), \
                 patch('builders.publish_release._upload', side_effect=lambda *args: order.append('upload')):
                publish(folder, 'owner/repo', 'test-token')
            self.assertEqual(order, ['POST', 'upload', 'upload', 'upload', 'PATCH'])


if __name__ == '__main__':
    unittest.main()

class CatalogTests(unittest.TestCase):
    package = ReleasePublishingTests.package
    def test_catalog_updated_only_after_confirmed_publication_and_preserves_history(self):
        from builders.publish_release import update_catalog
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);folder=self.package(root)
            catalog=root/'releases/README.md'
            catalog.write_text('| Windows | [1.0.0](windows/VERSION) | Pending | Not published |\n\n| OS | Version | Date | Folder | Hash |\n| --- | --- | --- | --- | --- |\n| Windows | 0.9.0 | earlier | old-folder | old-hash |\n')
            plan,_=release_plan(folder)
            url='https://github.com/owner/repo/releases/tag/'+plan['tag_name']
            update_catalog(folder,'owner/repo',url)
            result=catalog.read_text()
            self.assertIn('old-folder',result)
            self.assertIn('/releases/download/'+plan['tag_name']+'/setup.exe',result)
            self.assertIn('windows/1.0.0/',result)
            update_catalog(folder,'owner/repo',url)
            self.assertEqual(catalog.read_text(),result)
