from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, Client, override_settings

class FrontendServingTests(TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name);(self.root/'assets').mkdir()
        (self.root/'index.html').write_text('<html><div id="root">new-frontend-test</div></html>')
        (self.root/'assets'/'app-123.js').write_text('window.frontend=true;')
        self.config=override_settings(SERVE_FRONTEND=True,FRONTEND_DIST_DIR=self.root)
        self.config.enable();self.addCleanup(self.config.disable)

    def body(self,response):
        return b''.join(response.streaming_content) if response.streaming else response.content

    def test_root_deep_links_and_qr_use_new_frontend_on_django_port(self):
        for path in ['/','/login/','/dashboard','/downloads','/personal/computer','/system/applications',
                     '/device/scan','/device-enroll/test-token','/device-enroll/approval/',
                     '/mobile/fingerprint/11111111-1111-1111-1111-111111111111/']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertIn(b'new-frontend-test',self.body(response),path)
        self.assertIn('csrftoken',self.client.cookies)

    def test_assets_are_served_but_api_and_admin_remain_django(self):
        response=self.client.get('/assets/app-123.js')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'window.frontend=true',self.body(response))
        self.assertIn('javascript',response['Content-Type'])
        self.assertTrue(self.client.get('/api/session/').json()['authenticated'] is False)
        self.assertEqual(self.client.get('/api/unknown-path/').status_code,404)
        self.assertEqual(self.client.get('/admin/').status_code,302)
        self.assertEqual(self.client.post('/downloads',{},content_type='application/json').status_code,404)

    def test_profile_deep_links_use_react_on_every_panel(self):
        for path in ['/profile', '/personal/profile', '/system/profile']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b'new-frontend-test', self.body(response), path)

    def test_missing_asset_or_path_escape_is_not_spa_html(self):
        self.assertEqual(self.client.get('/assets/missing.js').status_code,404)
        self.assertEqual(self.client.get('/assets/../index.html').status_code,404)
        self.assertEqual(self.client.get('/assets/%2e%2e/index.html').status_code,404)

    def test_legacy_templates_remain_available_with_setting(self):
        with override_settings(SERVE_FRONTEND=False):
            response=self.client.get('/')
            self.assertEqual(response.status_code,200)
            self.assertNotIn(b'new-frontend-test',self.body(response))
        self.assertTrue(Path('templates/home.html').exists())

    def test_missing_build_returns_explicit_unavailable_response(self):
        (self.root/'index.html').unlink()
        self.assertEqual(self.client.get('/').status_code,503)

    @override_settings(CSRF_TRUSTED_ORIGINS=['https://tunnel.example'])
    def test_tunnel_https_origin_can_post_with_csrf_cookie_from_new_frontend(self):
        browser=Client(enforce_csrf_checks=True)
        response=browser.get('/',HTTP_HOST='tunnel.example',HTTP_X_FORWARDED_PROTO='https')
        self.body(response)
        token=browser.cookies['csrftoken'].value
        response=browser.post('/api/register/',{},content_type='application/json',HTTP_HOST='tunnel.example',
            HTTP_X_FORWARDED_PROTO='https',HTTP_ORIGIN='https://tunnel.example',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,400,response.content)
