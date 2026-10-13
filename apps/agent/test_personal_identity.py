import json
from django.test import TestCase
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from apps.common.models import AdminUser, Device, Organization, Users
from apps.agent.models import AgentSession
from apps.agent.tests import headers


class PersonalAgentIdentityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        public = key.public_key().public_bytes(serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        cls.company = Organization.objects.create(name='Company', slug='identity-company')
        cls.owner = AdminUser.objects.create_user(username='personal-owner', password='fixture', organization=cls.company)
        cls.personal = Organization.objects.create(name='Personal', slug='identity-personal',
            kind='personal', registration_owner=cls.owner)
        cls.owner.organizations.add(cls.personal)
        cls.user = Users.objects.create(organization=cls.personal, username=cls.owner.username)
        Users.objects.create(organization=cls.company, username='WindowsUser')
        cls.device = Device.objects.create(organization=cls.personal, pc_id='same-pc',
            cert='personal-cert', device_public_key=public, license='fixture', location='Fixture',
            enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED)
        cls.old = Device.objects.create(organization=cls.company, pc_id='same-pc',
            cert='company-cert', device_public_key=public, license='fixture', location='Fixture',
            enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED)

    def setUp(self):
        self.key = serialization.load_pem_private_key(self.private, password=None)

    def start(self, certificate='personal-cert', username='WindowsUser'):
        path = '/api/agent/session/start/'
        body = json.dumps({'pc_id':'same-pc', 'username':username}).encode()
        return self.client.post(path, body, content_type='application/json',
            **headers(self.key, 'POST', path, body, device='same-pc', certificate=certificate))

    def test_personal_uses_owner_not_windows_username_or_old_company_record(self):
        response = self.start()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['username'], self.owner.username)
        session = AgentSession.objects.get(session_id=response.json()['session_id'])
        self.assertEqual(session.user_id, self.user.pk)
        self.assertEqual(session.device_id, self.device.pk)

    def test_company_still_requires_its_own_windows_user(self):
        self.assertEqual(self.start('company-cert').status_code, 200)
        self.assertEqual(self.start('company-cert', self.owner.username).status_code, 403)

    def test_inactive_personal_owner_is_denied(self):
        self.owner.is_active = False
        self.owner.save(update_fields=['is_active'])
        self.assertEqual(self.start().status_code, 403)
        self.assertFalse(AgentSession.objects.exists())

    def test_followup_status_with_legacy_windows_username_uses_same_owner(self):
        path = '/api/agent/device/status/?pc_id=same-pc&username=WindowsUser'
        response = self.client.get(path, **headers(self.key, 'GET', path, b'',
            device='same-pc', certificate='personal-cert'))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['status'], 'active')

    def test_revoked_old_certificate_cannot_choose_other_workspace(self):
        from django.utils import timezone
        self.old.revoked_at = timezone.now()
        self.old.save(update_fields=['revoked_at'])
        self.assertEqual(self.start('company-cert').status_code, 403)
        self.assertFalse(AgentSession.objects.exists())

    def test_personal_cannot_select_another_biometric_user(self):
        other = Users.objects.create(organization=self.personal, username='another-person')
        response = self.start(username=other.username)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['username'], self.owner.username)

    def test_personal_rejects_other_users_existing_session(self):
        other = Users.objects.create(organization=self.personal, username='another-person')
        session = AgentSession.objects.create(device=self.device, user=other)
        path = f'/api/agent/device/status/?pc_id=same-pc&username=WindowsUser&session_id={session.session_id}'
        response = self.client.get(path, **headers(self.key, 'GET', path, b'',
            device='same-pc', certificate='personal-cert'))
        self.assertEqual(response.status_code, 403)
