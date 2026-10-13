import json
import time
import uuid
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import Client, TestCase
from django.utils import timezone

from apps.common.models import AdminUser, Device, Organization, Users
from apps.agent.models import AgentSession
from apps.agent.signatures import envelope


class RemovalTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.org = Organization.objects.create(name='Removal company', slug='removal-company')
        self.admin = AdminUser.objects.create_user(username='removal-admin', password='test-pass', organization=self.org)
        self.client.force_login(self.admin)
        session = self.client.session
        session['current_org_id'] = self.org.pk
        session.save()
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.recovery = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.device = Device.objects.create(organization=self.org, pc_id='removal-pc', license='WINDOWS-ID',
            location='Office', cert='removal-cert', device_public_key=self.pem(self.key),
            enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED)
        self.operation = str(uuid.uuid4())
        self.desktop = Client()

    @staticmethod
    def pem(key):
        return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def issue(self, device=None):
        return self.client.post(f'/api/devices/{(device or self.device).pk}/removal-code/', data={}, content_type='application/json')

    def signed(self, action, payload=None, key=None, cert=None):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64
        path = action if action.startswith('/') else f'/api/agent/removal/{action}/'
        data = {'device_uuid': self.device.pc_id, **(payload or {})}
        body = json.dumps(data).encode()
        stamp, nonce = str(int(time.time())), uuid.uuid4().hex
        certificate = cert or self.device.cert
        signature = (key or self.key).sign(envelope('POST', path, body, self.device.pc_id, certificate, stamp, nonce),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256())
        return self.desktop.post(path, data=body, content_type='application/json',
            HTTP_X_BIOGUARD_VERSION='1', HTTP_X_PC_ID=self.device.pc_id, HTTP_X_CERT_ID=certificate,
            HTTP_X_TIMESTAMP=stamp, HTTP_X_NONCE=nonce, HTTP_X_SIGNATURE=base64.b64encode(signature).decode())

    def begin(self):
        response = self.issue()
        self.assertEqual(response.status_code, 201)
        self.code = response.json()['code']
        response = self.signed('begin', {'code': self.code, 'operation_id': self.operation,
            'recovery_public_key': self.pem(self.recovery)})
        self.assertEqual(response.status_code, 200, response.content)
        return response

    def recovery_request(self, action):
        return self.signed(action, {'operation_id': self.operation}, key=self.recovery, cert=f'removal:{self.operation}')

    def test_code_is_device_bound_short_lived_and_not_stored_plaintext(self):
        response = self.issue()
        self.assertEqual(response.status_code, 201)
        from apps.device.models import DeviceRemovalCode
        row = DeviceRemovalCode.objects.get(device=self.device)
        self.assertNotEqual(row.code_digest, response.json()['code'])
        self.assertLessEqual(row.expires_at, timezone.now() + timedelta(minutes=10))

    def test_cross_workspace_cannot_issue_code(self):
        other = Organization.objects.create(name='Other', slug='other-removal')
        device = Device.objects.create(organization=other, pc_id='other', license='ID', location='Other')
        self.assertEqual(self.issue(device).status_code, 404)

    def test_personal_workspace_only_owner_can_issue(self):
        self.org.kind = Organization.Kind.PERSONAL
        self.org.registration_owner = self.admin
        self.org.save()
        self.assertEqual(self.issue().status_code, 201)
        other = AdminUser.objects.create_user(username='other-admin', password='test-pass', organization=self.org)
        self.client.force_login(other)
        session = self.client.session
        session['current_org_id'] = self.org.pk
        session.save()
        self.assertEqual(self.issue().status_code, 403)

    def test_check_does_not_consume_or_revoke(self):
        issued = self.issue()
        self.assertEqual(issued.status_code, 201)
        response = self.signed('check', {'code': issued.json()['code'],
            'recovery_public_key': self.pem(self.recovery)}, key=self.recovery, cert='removal-bootstrap')
        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertIsNone(self.device.revoked_at)
        from apps.device.models import DeviceRemovalCode
        self.assertIsNone(DeviceRemovalCode.objects.get(device=self.device).used_at)

    def test_invalid_or_expired_code_does_not_revoke(self):
        issued = self.issue()
        self.assertEqual(issued.status_code, 201)
        from apps.device.models import DeviceRemovalCode
        DeviceRemovalCode.objects.filter(device=self.device).update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.signed('begin', {'code': issued.json()['code'], 'operation_id': self.operation,
            'recovery_public_key': self.pem(self.recovery)})
        self.assertEqual(response.status_code, 403)
        self.device.refresh_from_db()
        self.assertIsNone(self.device.revoked_at)

    def test_begin_revokes_device_and_retains_key_and_allocation(self):
        self.begin()
        self.device.refresh_from_db()
        self.assertFalse(self.device.is_active)
        self.assertIsNotNone(self.device.revoked_at)
        self.assertEqual(self.device.removal_state, 'removal_pending')
        self.assertTrue(self.device.agent_allocation_active)
        self.assertEqual(self.device.device_public_key, self.pem(self.key))
        self.assertEqual(self.device.license, 'WINDOWS-ID')

    def test_begin_invalidates_agent_sessions(self):
        # Use existing user factory conventions without requiring a biometric user.
        user = Users.objects.create(organization=self.org, username='removal-user')
        session = AgentSession.objects.create(device=self.device, user=user, expires_at=timezone.now() + timedelta(hours=1))
        self.begin()
        session.refresh_from_db()
        self.assertEqual(session.status, 'expired')
        self.assertLessEqual(session.expires_at, timezone.now())

    def test_recovery_key_survives_revocation_and_completion_is_idempotent(self):
        self.begin()
        self.assertEqual(self.recovery_request('status').status_code, 200)
        for _ in range(2):
            self.assertEqual(self.recovery_request('complete').status_code, 200)
        self.device.refresh_from_db()
        self.assertEqual(self.device.removal_state, 'removed')
        self.assertFalse(self.device.agent_allocation_active)
        self.assertIsNotNone(self.device.revoked_at)
        from apps.device.models import DeviceRemoval
        audit = DeviceRemoval.objects.get(pk=self.operation)
        self.assertEqual(audit.old_public_key, self.pem(self.key))
        self.assertEqual(audit.old_certificate, 'removal-cert')

    def test_normal_requests_cannot_use_revoked_key(self):
        self.begin()
        response = self.desktop.get('/api/agent/device/status/')
        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(self.signed('check', {'code': self.code}).status_code, 403)

    def test_recovery_rejects_wrong_key(self):
        self.begin()
        response = self.signed('status', {'operation_id': self.operation}, cert=f'removal:{self.operation}')
        self.assertEqual(response.status_code, 401)

    def test_code_cannot_begin_another_operation_after_claim(self):
        self.begin()
        response = self.signed('begin', {'code': self.code, 'operation_id': str(uuid.uuid4()),
            'recovery_public_key': self.pem(self.recovery)})
        self.assertIn(response.status_code, (403, 409))

    def test_delete_does_not_erase_enrolled_device(self):
        response = self.client.delete(f'/api/devices/{self.device.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertTrue(Device.objects.filter(pk=self.device.pk).exists())

    def test_edit_cannot_replace_enrolled_key_or_reactivate_removed_device(self):
        self.begin()
        self.assertEqual(self.recovery_request('complete').status_code, 200)
        response = self.client.patch(f'/api/devices/{self.device.pk}/', data={'is_active': True}, content_type='application/json')
        self.assertEqual(response.status_code, 409)

    def test_new_code_invalidates_previous_unused_code(self):
        first, second = self.issue(), self.issue()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(self.signed('check', {'code': first.json()['code']}).status_code, 403)
        self.assertEqual(self.signed('check', {'code': second.json()['code']}).status_code, 200)

    def test_recover_activation_response_requires_exact_live_key(self):
        response = self.signed('/api/agent/activate/status/', {'public_key': self.pem(self.key)}, cert='bootstrap')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['certificate']['cert_id'], self.device.cert)
        response = self.signed('/api/agent/activate/status/', {'public_key': self.pem(self.recovery)}, key=self.recovery, cert='bootstrap')
        self.assertEqual(response.status_code, 404)

    def test_revoked_activation_cannot_be_recovered(self):
        self.begin()
        response = self.signed('/api/agent/activate/status/', {'public_key': self.pem(self.key)}, cert='bootstrap')
        self.assertEqual(response.status_code, 404)

    def test_admin_code_plus_recovery_key_can_remove_missing_local_bundle(self):
        response = self.issue()
        self.assertEqual(response.status_code, 201)
        response = self.signed('begin', {'code': response.json()['code'], 'operation_id': self.operation,
            'recovery_public_key': self.pem(self.recovery)}, key=self.recovery, cert='removal-bootstrap')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.recovery_request('status').status_code, 200)

    def test_reinstallation_uses_new_key_and_keeps_old_audit(self):
        self.begin()
        self.assertEqual(self.recovery_request('complete').status_code, 200)
        from apps.org.models import OrgToken
        token = OrgToken.objects.create(org=self.org)
        fresh = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        response = self.signed('/api/agent/activate/', {'activation_code': token.token,
            'windows_license': self.device.license, 'public_key': self.pem(fresh)}, key=fresh, cert='bootstrap')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotEqual(response.json()['certificate']['cert_id'], 'removal-cert')
        self.device.refresh_from_db()
        self.assertEqual(self.device.removal_state, 'active')
        self.assertTrue(self.device.agent_allocation_active)
        from apps.device.models import DeviceRemoval
        self.assertEqual(DeviceRemoval.objects.get(pk=self.operation).old_certificate, 'removal-cert')
        self.assertEqual(self.signed('/api/agent/install/status/', {}, key=self.key, cert='removal-cert').status_code, 401)

    def test_old_generation_code_cannot_remove_reenrollment(self):
        issued = self.issue()
        Device.objects.filter(pk=self.device.pk).update(cert='new-generation')
        response = self.signed('check', {'code': issued.json()['code'],
            'recovery_public_key': self.pem(self.recovery)}, key=self.recovery, cert='removal-bootstrap')
        self.assertEqual(response.status_code, 403)

    def test_archived_key_reuse_is_rejected_before_token_consumption(self):
        self.begin()
        self.assertEqual(self.recovery_request('complete').status_code, 200)
        from apps.org.models import OrgToken
        token = OrgToken.objects.create(org=self.org)
        # PKCS1 and SubjectPublicKeyInfo encodings represent the same key.
        old = self.key.public_key().public_bytes(serialization.Encoding.PEM,
            serialization.PublicFormat.PKCS1).decode()
        response = self.signed('/api/agent/activate/', {'activation_code': token.token,
            'windows_license': self.device.license, 'public_key': old}, cert='bootstrap')
        self.assertEqual(response.status_code, 409, response.content)
        token.refresh_from_db()
        self.assertFalse(token.is_used)

    def test_cannot_issue_after_removal_started(self):
        self.begin()
        self.assertEqual(self.issue().status_code, 409)

    def test_claim_rechecks_generation_after_initial_proof(self):
        from unittest.mock import patch
        issued = self.issue()
        with patch('apps.device.removal.verify_code_request', side_effect=lambda *args:
                Device.objects.filter(pk=self.device.pk).update(cert='concurrent-enrollment')):
            response = self.signed('begin', {'code': issued.json()['code'],
                'operation_id': self.operation, 'recovery_public_key': self.pem(self.recovery)})
        self.assertEqual(response.status_code, 409)
        from apps.device.models import DeviceRemovalCode, DeviceRemoval
        self.assertIsNone(DeviceRemovalCode.objects.get(device=self.device).used_at)
        self.assertFalse(DeviceRemoval.objects.exists())

    def test_replayed_signed_check_is_rejected(self):
        from unittest.mock import patch
        issued = self.issue()
        with patch('uuid.uuid4', return_value=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')):
            self.assertEqual(self.signed('check', {'code': issued.json()['code']}).status_code, 200)
            self.assertEqual(self.signed('check', {'code': issued.json()['code']}).status_code, 409)

    def test_code_stops_working_when_issuer_loses_authority(self):
        issued = self.issue()
        self.admin.is_admin = False
        self.admin.save(update_fields=['is_admin'])
        self.assertEqual(self.signed('check', {'code': issued.json()['code']}).status_code, 403)
