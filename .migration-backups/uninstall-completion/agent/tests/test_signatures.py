import unittest
import base64
from unittest.mock import patch
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding,rsa
from core.network.client import BioGuardApiClient


class SignatureTests(unittest.TestCase):
    def test_request_signer_receives_exact_body_and_target(self):
        seen=[]
        def signer(method,path,body):
            seen.append((method,path,body));return {'X-Signature':'test'}
        requests=[]
        client=BioGuardApiClient('http://127.0.0.1:8000',request_signer=signer,transport=lambda req,timeout:requests.append(req) or b'{}')
        client.post('/api/test/?a=1',{'a':'test'})
        self.assertEqual(seen,[('POST','/api/test/?a=1',requests[0].data)])
        self.assertEqual(requests[0].get_header('X-signature'),'test')

    def test_real_rsa_signature_covers_method_target_and_body(self):
        from core.network.signatures import sign_headers,envelope
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        pem=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        headers=sign_headers(pem,'POST','/api/a/?x=a%20b',b'{}','device','cert',timestamp=123,nonce='a'*32)
        signature=base64.b64decode(headers['X-Signature'])
        key.public_key().verify(signature,envelope('POST','/api/a/?x=a+b',b'{}','device','cert','123','a'*32),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32),hashes.SHA256())
        from cryptography.exceptions import InvalidSignature
        with self.assertRaises(InvalidSignature):
            key.public_key().verify(signature,envelope('POST','/api/a/?x=a+b',b'{ }','device','cert','123','a'*32),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32),hashes.SHA256())

    def test_default_signing_failure_does_not_send_unsigned_request(self):
        from core.network.errors import BackendAuthenticationError
        requests=[]
        client=BioGuardApiClient('https://example.com',request_signer=lambda *args: (_ for _ in ()).throw(OSError('no key')),transport=lambda *args:requests.append(args))
        with self.assertRaises(BackendAuthenticationError): client.post('/api/agent/session/start/',{})
        self.assertEqual(requests,[])
