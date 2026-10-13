"""User-bound protected device credentials; no plaintext fallback or TPM claims."""

import hmac
import hashlib
import time
import sys
import types
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


from storage.legacy_windows_cert import (
    CERT_DIR, CERT_FILE, KEY_FILE, KEY_FILE_ENC, save_cert, load_cert,
    delete_cert, _load_private_key_bytes, _ensure_dir, _dpapi_encrypt, _dpapi_decrypt,
)
from storage import legacy_windows_cert as _certificate_storage


_PERSISTENCE_NAMES = frozenset({
    "CERT_DIR", "CERT_FILE", "KEY_FILE", "KEY_FILE_ENC", "save_cert", "load_cert",
    "delete_cert", "_load_private_key_bytes", "_ensure_dir", "_dpapi_encrypt", "_dpapi_decrypt",
})


class _CertificateCompatibilityModule(types.ModuleType):
    """Keep legacy mutable attributes connected to the extracted storage module."""

    def __getattribute__(self, name):
        if name in _PERSISTENCE_NAMES:
            return getattr(_certificate_storage, name)
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name in _PERSISTENCE_NAMES:
            setattr(_certificate_storage, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CertificateCompatibilityModule


# ── TPM / DPAPI ───────────────────────────────────────────────────────────────


def generate_keypair() -> tuple[str, str]:
    """RSA keypair yaratadi. (public_pem, private_pem) qaytaradi."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return public_pem, private_pem


def is_activated() -> bool:
    """Agent aktivatsiyadan o'tganmi?"""
    return _certificate_storage.load_cert() is not None


def get_org_slug() -> str:
    """Sertifikatdan org_slug oladi."""
    cert = _certificate_storage.load_cert()
    if not cert:
        return ""
    return cert.get("org_slug", "")


def sign_request(pc_id, method, target, body):
    """Sign the complete v1 envelope, failing closed without protected credentials."""
    from core.network.signatures import sign_headers
    cert = _certificate_storage.load_cert()
    key = _certificate_storage._load_private_key_bytes()
    if not cert or not key or cert.get('pc_id') != pc_id:
        raise ValueError('Protected device credentials required')
    return sign_headers(key, method, target, body, pc_id, cert['cert_id'])
