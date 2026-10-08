import base64, hashlib, json, os, struct
import cbor2
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from apps.common.models import Organization, AdminUser, Users, Device, BiometricFingerprint
from apps.biometrik.models import FingerprintSession
from apps.agent.models import AgentSession


def b64(value): return base64.urlsafe_b64encode(value).decode().rstrip('=')


@override_settings(PUBLIC_SITE_URL='https://bioguard.example')
class WebAuthnTests(TestCase):
    def setUp(self):
        self.org=Organization.objects.create(name='Biometric test',slug='bio-test')
        self.admin=AdminUser.objects.create_user('bio-admin','synthetic-password',organization=self.org)
        self.user=Users.objects.create(organization=self.org,username='bio-user',fio='Test',lavozim='Test')
        self.client.force_login(self.admin)
        self.key=ec.generate_private_key(ec.SECP256R1());numbers=self.key.public_key().public_numbers()
        self.cose=cbor2.dumps({1:2,3:-7,-1:1,-2:numbers.x.to_bytes(32,'big'),-3:numbers.y.to_bytes(32,'big')})
        self.credential=os.urandom(16)

    def enroll(self, *, origin='https://bioguard.example', uv=True):
        response=self.client.post('/api/fingerprint/phone/start/',json.dumps({'user_id':self.user.pk}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        session=FingerprintSession.objects.get(session_id=response.json()['session_id'])
        challenge=bytes(session.challenge)
        client_data=json.dumps({'type':'webauthn.create','challenge':b64(challenge),'origin':origin}).encode()
        flags=0x45 if uv else 0x41
        data=hashlib.sha256(b'bioguard.example').digest()+bytes([flags])+struct.pack('>I',0)+b'\0'*16+struct.pack('>H',len(self.credential))+self.credential+self.cose
        att=cbor2.dumps({'fmt':'none','authData':data,'attStmt':{}})
        payload={'session_id':str(session.session_id),'rawId':b64(self.credential),'clientDataJSON':b64(client_data),'attestationObject':b64(att)}
        return self.client.post('/api/fingerprint/phone/submit/',json.dumps(payload),content_type='application/json')

    def session(self):
        device=Device.objects.create(organization=self.org,pc_id='webauthn-pc',license='Test',location='Test',enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED)
        return AgentSession.objects.create(user=self.user,device=device)

    def assertion(self,session,challenge,*,origin='https://bioguard.example',uv=True,count=1):
        client_data=json.dumps({'type':'webauthn.get','challenge':challenge,'origin':origin}).encode()
        auth=hashlib.sha256(b'bioguard.example').digest()+bytes([0x05 if uv else 0x01])+struct.pack('>I',count)
        sig=self.key.sign(auth+hashlib.sha256(client_data).digest(),ec.ECDSA(hashes.SHA256()))
        return {'rawId':b64(self.credential),'clientDataJSON':b64(client_data),'authenticatorData':b64(auth),'signature':b64(sig)}

    def test_valid_registration_and_assertion_then_replay_rejected(self):
        response=self.enroll();self.assertEqual(response.status_code,200,response.content)
        session=self.session();path=f'/api/agent/fingerprint/phone/submit/{session.session_id}/'
        options=self.client.get(path).json()
        payload=self.assertion(session,options['challenge'])
        response=self.client.post(path,json.dumps(payload),content_type='application/json')
        self.assertEqual(response.status_code,200,response.content);self.assertEqual(response.json()['status'],'completed')
        self.assertGreaterEqual(self.client.post(path,json.dumps(payload),content_type='application/json').status_code,400)
        self.assertEqual(BiometricFingerprint.objects.get(user=self.user).sign_count,1)

    def test_wrong_origin_and_absent_user_verification_cannot_enroll(self):
        self.assertEqual(self.enroll(origin='https://evil.example').status_code,400)
        self.assertEqual(self.enroll(uv=False).status_code,400)
        self.assertEqual(BiometricFingerprint.objects.count(),0)

    def test_tampered_signature_wrong_challenge_origin_and_no_uv(self):
        self.assertEqual(self.enroll().status_code,200)
        session=self.session();path=f'/api/agent/fingerprint/phone/submit/{session.session_id}/'
        for condition in ('signature','challenge','origin','uv'):
            with self.subTest(condition=condition):
                options=self.client.get(path).json()
                payload=self.assertion(session, 'invalid' if condition=='challenge' else options['challenge'],origin='https://evil.example' if condition=='origin' else 'https://bioguard.example',uv=condition!='uv')
                if condition=='signature':payload['signature']=b64(b'invalid')
                self.assertEqual(self.client.post(path,json.dumps(payload),content_type='application/json').status_code,400)
                session.refresh_from_db();self.assertEqual(session.status,'pending')

    def test_foreign_org_cannot_start_enrollment(self):
        other=Organization.objects.create(name='Other',slug='bio-other')
        user=Users.objects.create(organization=other,username='other',fio='Test',lavozim='Test')
        response=self.client.post('/api/fingerprint/phone/start/',json.dumps({'user_id':user.pk}),content_type='application/json')
        self.assertEqual(response.status_code,403)
