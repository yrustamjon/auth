import json
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, override_settings

class ProductDownloadsTests(TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        for os in ['windows','linux','macos']:
            (self.root/os).mkdir();(self.root/os/'VERSION').write_text('1.0.3' if os=='windows' else '0.0.0')
        release=self.root/'windows'/'1.0.3'/'2026-10-08_20-31-03_UZT';release.mkdir(parents=True)
        (release/'BioGuard_Setup_v1.0.3.exe').write_bytes(b'agent-installer')
        (release/'manifest.json').write_text(json.dumps({'os':'windows','version':'1.0.3','prerelease':True,
            'created_at':'2026-10-08T20:31:03+05:00','files':[{'name':'BioGuard_Setup_v1.0.3.exe','size':15,'sha256':'a'*64}]}))
        self.settings=override_settings(AGENT_RELEASE_DIR=self.root);self.settings.enable();self.addCleanup(self.settings.disable)

    def test_public_catalog_uses_real_installer_and_unavailable_os(self):
        response=self.client.get('/api/downloads/')
        self.assertEqual(response.status_code,200)
        rows=response.json()['releases'];windows=next(r for r in rows if r['platform']=='windows')
        self.assertTrue(windows['available']);self.assertTrue(windows['prerelease'])
        self.assertEqual(windows['filename'],'BioGuard_Setup_v1.0.3.exe')
        self.assertFalse(next(r for r in rows if r['platform']=='macos')['available'])
        package=self.client.get(windows['download_url'])
        self.assertEqual(package.status_code,200)
        self.assertEqual(b''.join(package.streaming_content),b'agent-installer')
        self.assertIn('attachment',package['Content-Disposition'])

    def test_missing_or_path_traversal_package_is_never_available(self):
        manifest=next(self.root.rglob('manifest.json'))
        data=json.loads(manifest.read_text());data['files'][0]['name']='../../outside.exe';manifest.write_text(json.dumps(data))
        self.assertFalse(self.client.get('/api/downloads/').json()['releases'][0]['available'])
        self.assertEqual(self.client.get('/api/downloads/windows/').status_code,404)
        self.assertEqual(self.client.get('/api/downloads/unknown/').status_code,404)
