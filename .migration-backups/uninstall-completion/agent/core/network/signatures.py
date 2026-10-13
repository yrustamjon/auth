"""BioGuard v1 request envelope. Keep wire contract aligned with auth backend."""
import base64
import hashlib
import re
import secrets
import time
from urllib.parse import urlsplit, unquote, quote, parse_qsl, urlencode
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def canonical_target(target):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or parts.fragment or not parts.path.startswith('/'):
        raise ValueError('A relative absolute-path request target is required')
    path = quote(unquote(parts.path, errors='strict'), safe='/~-._')
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True, encoding='utf-8', errors='strict'))
    return path + ('?' + query if query else '')


def envelope(method, target, body, device, certificate, timestamp, nonce):
    values = ('BIOGUARD/1', method.upper(), canonical_target(target), hashlib.sha256(body).hexdigest(),
              device, certificate, str(timestamp), nonce)
    if any(not isinstance(v, str) or '\n' in v or '\r' in v for v in values):
        raise ValueError('Invalid envelope field')
    return '\n'.join(values).encode()


def sign_headers(private_pem, method, target, body, device, certificate, *, timestamp=None, nonce=None):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    nonce = nonce or secrets.token_hex(32)
    key = serialization.load_pem_private_key(private_pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
        raise ValueError('RSA >=2048 required')
    signature = key.sign(envelope(method,target,body,device,certificate,timestamp,nonce),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=32), hashes.SHA256())
    return {'X-BioGuard-Version':'1','X-PC-ID':device,'X-Cert-ID':certificate,
            'X-Timestamp':timestamp,'X-Nonce':nonce,'X-Signature':base64.b64encode(signature).decode()}
