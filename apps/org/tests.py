import json
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from apps.common.models import Device, Organization, Users
from apps.org.models import OrgToken


class EnrollmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.public = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def setUp(self):
        self.org = Organization.objects.create(name='Test org', slug='test-enroll')
        self.device = Device.objects.create(organization=self.org, pc_id='test-pc', license='UNKNOWN',
            location='Test', enrollment_status=Device.EnrollmentStatus.BROWSER_APPROVED, is_active=False)
        self.token = OrgToken.objects.create(org=self.org)
        self.payload = dict(activation_code=self.token.token, device_uuid='test-pc', windows_license='TEST-PRODUCT', public_key=self.public)

    def activate(self):
        return self.client.post('/api/agent/activate/', json.dumps(self.payload), content_type='application/json')

    def assert_unchanged(self):
        self.device.refresh_from_db(); self.token.refresh_from_db()
        self.assertIsNone(self.device.cert)
        self.assertIsNone(self.device.device_public_key)
        self.assertFalse(self.token.is_used)
        self.assertEqual(self.device.license, 'UNKNOWN')

    def test_browser_activation_then_check_and_session(self):
        response = self.activate()
        self.assertEqual(response.status_code, 200, response.content)
        self.device.refresh_from_db(); self.token.refresh_from_db()
        self.assertTrue(self.token.is_used)
        self.assertEqual(self.device.enrollment_status, Device.EnrollmentStatus.AGENT_ENROLLED)
        self.assertIsNotNone(self.device.enrolled_at)
        self.assertEqual(self.device.license, 'TEST-PRODUCT')
        self.assertEqual(self.device.device_public_key, self.public)
        self.assertEqual(self.client.post('/api/agent/check-pc/', json.dumps(dict(device_uuid='test-pc',windows_license='TEST-PRODUCT')), content_type='application/json').status_code, 200)
        Users.objects.create(organization=self.org, username='synthetic', fio='Test', lavozim='Test')
        response = self.client.post('/api/agent/session/start/', json.dumps(dict(pc_id='test-pc',username='synthetic')), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'pending')

    def test_invalid_expired_used_and_wrong_org_tokens(self):
        for condition in ('invalid','expired','used','wrong-org'):
            with self.subTest(condition=condition):
                self.token.is_used=False; self.token.expires_at=timezone.now()+timedelta(hours=1); self.token.save()
                self.payload['activation_code']=self.token.token
                if condition=='invalid': self.payload['activation_code']='invalid'
                if condition=='expired': self.token.expires_at=timezone.now()-timedelta(seconds=1); self.token.save()
                if condition=='used': self.token.is_used=True; self.token.save()
                if condition=='wrong-org':
                    other=Organization.objects.create(name='Other',slug='other')
                    self.payload['activation_code']=OrgToken.objects.create(org=other).token
                self.assertGreaterEqual(self.activate().status_code, 400)
                self.device.refresh_from_db(); self.assertIsNone(self.device.cert)

    def test_malformed_weak_and_non_string_keys(self):
        weak=rsa.generate_private_key(public_exponent=65537,key_size=1024).public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        for value in ('invalid', weak, {'key':'invalid'}, 'x'*16385):
            with self.subTest(key_type=type(value).__name__):
                self.payload['public_key']=value
                self.assertEqual(self.activate().status_code,400)
                self.assert_unchanged()

    def test_revoked_and_inactive_organization(self):
        self.device.revoked_at=timezone.now(); self.device.save()
        self.assertEqual(self.activate().status_code,403); self.assert_unchanged()
        self.device.revoked_at=None; self.device.save()
        self.org.is_active=False; self.org.save()
        self.assertEqual(self.activate().status_code,403); self.assert_unchanged()
