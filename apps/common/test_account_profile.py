from django.test import TestCase, Client
from .models import AdminUser, Organization
from apps.org.models import OrgToken


class AccountProfileTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='My company', slug='profile-company')
        self.user = AdminUser.objects.create_user('profile-owner', 'Old-password829!', organization=self.org)
        self.other = AdminUser.objects.create_user('other-owner', 'Other-password829!', organization=self.org)
        self.client.force_login(self.user)
        session = self.client.session
        session['panel'] = 'admin'
        session['current_org_id'] = self.org.id
        session.save()

    def test_profile_returns_only_current_account_without_credentials(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        self.assertEqual(response.json()['current_organization'], {'id': self.org.id, 'name': self.org.name})
        self.assertEqual(response.json()['organizations'], [{'id': self.org.id, 'name': self.org.name}])
        self.assertNotIn('password', response.json())

    def test_personal_and_system_accounts_can_open_profile(self):
        for kind, panel in [('personal', 'admin'), ('company', 'superadmin')]:
            self.org.kind = kind
            self.org.save()
            self.user.is_superadmin = panel == 'superadmin'
            self.user.save()
            session = self.client.session
            session['panel'] = panel
            session.save()
            response = self.client.get('/api/profile/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['account_type'], 'superadmin' if panel == 'superadmin' else 'personal')

    def test_company_activation_token_belongs_to_selected_authorized_organization(self):
        second = Organization.objects.create(name='Second company', slug='second-profile-company')
        self.user.organizations.add(second)
        response = self.client.get('/api/token/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OrgToken.objects.get(token=response.json()['token']).org_id, self.org.id)
        session = self.client.session
        session['current_org_id'] = second.id
        session.save()
        response = self.client.get('/api/token/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OrgToken.objects.get(token=response.json()['token']).org_id, second.id)
        self.user.organizations.remove(second)
        self.assertEqual(self.client.get('/api/token/').status_code, 403)

    def test_password_change_requires_current_password_and_validation(self):
        for data in [
            {'current_password': 'wrong', 'new_password': 'New-password937!', 'confirm_password': 'New-password937!'},
            {'current_password': 'Old-password829!', 'new_password': '123', 'confirm_password': '123'},
            {'current_password': 'Old-password829!', 'new_password': 'New-password937!', 'confirm_password': 'different'},
        ]:
            response = self.client.post('/api/profile/password/', data, content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Old-password829!'))

    def test_password_change_preserves_session_and_never_changes_another_account(self):
        response = self.client.post('/api/profile/password/', {
            'current_password': 'Old-password829!', 'new_password': 'New-password937!',
            'confirm_password': 'New-password937!', 'user_id': self.other.id,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.user.check_password('New-password937!'))
        self.assertTrue(self.other.check_password('Other-password829!'))
        self.assertEqual(self.client.get('/api/profile/').status_code, 200)

    def test_anonymous_inactive_and_missing_csrf_are_denied(self):
        self.client.logout()
        self.assertIn(self.client.get('/api/profile/').status_code, [401, 403])
        self.client.force_login(self.user)
        self.user.is_active = False
        self.user.save()
        self.assertIn(self.client.get('/api/profile/').status_code, [401, 403])
        self.user.is_active = True
        self.user.save()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post('/api/profile/password/', {}, content_type='application/json').status_code, 403)
