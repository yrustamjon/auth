from django.test import TestCase, Client
from apps.common.models import AdminUser, Organization

class FrontendSessionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Example', slug='frontend-test')
        self.user = AdminUser.objects.create_user('frontend-test', 'test-password', organization=self.org)

    def test_anonymous_session_and_csrf(self):
        response = self.client.get('/api/session/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])
        self.assertIn('csrftoken', response.cookies)

    def test_authenticated_panel_and_organizations(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['panel'] = 'admin'
        session['current_org_id'] = self.org.id
        session.save()
        data = self.client.get('/api/session/').json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['panel'], 'admin')
        self.assertEqual(data['organization_id'], self.org.id)
        self.assertEqual(data['organizations'], [{'id':self.org.id,'name':'Example'}])
        self.client.post('/api/admin/logout')
        self.assertFalse(self.client.get('/api/session/').json()['authenticated'])

    def test_wrong_password_is_json_error(self):
        response = self.client.post('/api/admin/login', {'username':self.user.username,'password':'wrong'}, content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail',response.json())
