import base64
import hashlib
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.db import close_old_connections
from django.utils import timezone
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from apps.common.models import Organization, Users, Device
from apps.org.models import OrgToken


def headers(key, method, target, body, device='signed-pc', certificate='signed-cert', timestamp=None, nonce=None):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    nonce = nonce or uuid.uuid4().hex
    envelope = '\n'.join(('BIOGUARD/1', method, target, hashlib.sha256(body).hexdigest(), device, certificate, timestamp, nonce)).encode()
    sig = key.sign(envelope, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32), hashes.SHA256())
    return {'HTTP_X_BIOGUARD_VERSION':'1', 'HTTP_X_PC_ID':device, 'HTTP_X_CERT_ID':certificate,
            'HTTP_X_TIMESTAMP':timestamp, 'HTTP_X_NONCE':nonce, 'HTTP_X_SIGNATURE':base64.b64encode(sig).decode()}


class SignedRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        cls.public=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    def setUp(self):
        self.key=serialization.load_pem_private_key(self.private,password=None)
        self.org=Organization.objects.create(name='Signed org',slug='signed-org')
        self.user=Users.objects.create(organization=self.org,username='signed-user',fio='Synthetic',lavozim='Test')
        self.device=Device.objects.create(organization=self.org,pc_id='signed-pc',cert='signed-cert',device_public_key=self.public,
            license='synthetic-license',location='Test',enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED,enrolled_at=timezone.now())
        self.body=json.dumps({'pc_id':'signed-pc','username':'signed-user'}).encode()
        self.path='/api/agent/session/start/'

    def post(self, body=None, signed=None):
        return self.client.post(self.path, body or self.body,content_type='application/json', **(signed or {}))

    def test_unsigned_desktop_paths_are_rejected(self):
        self.assertEqual(self.post().status_code,401)
        self.assertEqual(self.client.get('/api/agent/device/status/?pc_id=signed-pc').status_code,401)
        self.assertEqual(self.client.post('/api/agent/check-pc/',json.dumps({'device_uuid':'signed-pc','windows_license':'synthetic-license'}),content_type='application/json').status_code,401)

    def test_signed_session_replay_and_body_tampering(self):
        signed=headers(self.key,'POST',self.path,self.body)
        first=self.post(signed=signed);self.assertEqual(first.status_code,200,first.content)
        self.assertEqual(self.post(signed=signed).status_code,409)
        signed=headers(self.key,'POST',self.path,self.body)
        self.assertEqual(self.post(body=self.body+b' ',signed=signed).status_code,401)

    def test_wrong_path_query_method_expired_signature_and_certificate(self):
        for method,target,stamp,cert in [('GET',self.path,None,'signed-cert'),('POST','/different/',None,'signed-cert'),('POST',self.path+'?x=1',None,'signed-cert'),('POST',self.path,int(time.time())-301,'signed-cert'),('POST',self.path,None,'wrong-cert')]:
            with self.subTest(method=method,target=target,certificate=cert):
                self.assertEqual(self.post(signed=headers(self.key,method,target,self.body,timestamp=stamp,certificate=cert)).status_code,401)

    def test_revocation_inactive_org_and_user(self):
        self.device.revoked_at=timezone.now();self.device.save()
        self.assertEqual(self.post(signed=headers(self.key,'POST',self.path,self.body)).status_code,403)
        self.device.revoked_at=None;self.device.save()
        self.org.is_active=False;self.org.save()
        self.assertEqual(self.post(signed=headers(self.key,'POST',self.path,self.body)).status_code,403)
        self.org.is_active=True;self.org.save();self.user.status=False;self.user.save()
        self.assertEqual(self.post(signed=headers(self.key,'POST',self.path,self.body)).status_code,403)

    def test_cross_device_session_access_is_rejected(self):
        session=self.post(signed=headers(self.key,'POST',self.path,self.body)).json()['session_id']
        Device.objects.create(organization=self.org,pc_id='other-pc',cert='other-cert',device_public_key=self.public,license='test',location='Test',enrollment_status=Device.EnrollmentStatus.AGENT_ENROLLED)
        path=f'/api/agent/face/phone/status/{session}/'
        response=self.client.get(path,**headers(self.key,'GET',path,b'',device='other-pc',certificate='other-cert'))
        self.assertEqual(response.status_code,403)

    def test_fingerprint_raw_id_cannot_authorize(self):
        session=self.post(signed=headers(self.key,'POST',self.path,self.body)).json()['session_id']
        from apps.common.models import BiometricFingerprint
        fp=BiometricFingerprint.objects.create(user=self.user);fp.set_embedding(b'rawid|client|attestation');fp.save()
        response=self.client.post(f'/api/agent/fingerprint/phone/submit/{session}/',json.dumps({'rawId':'rawid'}),content_type='application/json')
        self.assertNotEqual(response.status_code,200)
        from apps.agent.models import AgentSession
        self.assertEqual(AgentSession.objects.get(session_id=session).status,'pending')

    def test_bootstrap_requires_proof_and_valid_key_can_enroll(self):
        token=OrgToken.objects.create(org=self.org)
        device=Device.objects.create(organization=self.org,pc_id='bootstrap-pc',license='UNKNOWN',location='Test',is_active=False,enrollment_status=Device.EnrollmentStatus.BROWSER_APPROVED)
        payload=json.dumps({'activation_code':token.token,'device_uuid':'bootstrap-pc','windows_license':'TEST','public_key':self.public}).encode()
        path='/api/agent/activate/'
        self.assertEqual(self.client.post(path,payload,content_type='application/json').status_code,401)
        signed=headers(self.key,'POST',path,payload,device='bootstrap-pc',certificate='bootstrap')
        response=self.client.post(path,payload,content_type='application/json',**signed)
        self.assertEqual(response.status_code,200,response.content)
        self.assertGreaterEqual(self.client.post(path,payload,content_type='application/json',**signed).status_code,400)

    def test_signed_face_request_uses_authenticated_device_without_redundant_pc_id(self):
        session=self.post(signed=headers(self.key,'POST',self.path,self.body)).json()['session_id']
        path='/api/face/agent/check/'
        body=json.dumps({'session_id':session,'username':'signed-user','image':'synthetic'}).encode()
        response=self.client.post(path,body,content_type='application/json',**headers(self.key,'POST',path,body))
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['status'],'failed')


class NonceRaceTests(TransactionTestCase):
    def test_parallel_duplicate_claim_has_exactly_one_winner(self):
        from apps.agent.security import consume_nonce
        def claim(_):
            close_old_connections()
            try: return consume_nonce('race-cert','a'*32,timezone.now()+timedelta(minutes=5))
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=4) as pool:
            result=list(pool.map(claim,range(8)))
        self.assertEqual(result.count(True),1)
        from apps.agent.models import RequestNonce
        self.assertEqual(RequestNonce.objects.count(),1)
