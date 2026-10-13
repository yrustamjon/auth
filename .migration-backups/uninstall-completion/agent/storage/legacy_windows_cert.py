"""Legacy Windows certificate persistence; original paths/bytes preserved."""
import os
import json
import tempfile
import threading
import hmac

CERT_DIR  = os.path.join(os.environ.get("APPDATA", ""), "ADBioGuard")
CERT_FILE = os.path.join(CERT_DIR, "cert.json")
KEY_FILE  = os.path.join(CERT_DIR, "private.pem")
KEY_FILE_ENC = os.path.join(CERT_DIR, "private.pem.dpapi")


def _ensure_dir():
    os.makedirs(CERT_DIR, exist_ok=True)

def _dpapi_encrypt(data: bytes) -> bytes | None:
    """User-bound Windows DPAPI; not TPM-backed or non-exportable."""
    try:
        import ctypes, ctypes.wintypes
        crypt = ctypes.windll.crypt32
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.wintypes.DWORD),
                        ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
        buf = (ctypes.c_ubyte * len(data))(*data)
        inp = DATA_BLOB(len(data), buf)
        out = DATA_BLOB()
        # CRYPTPROTECT_LOCAL_MACHINE=0 → faqat shu user ochib o'qiy oladi
        if crypt.CryptProtectData(ctypes.byref(inp), None, None, None, None, 0,
                                  ctypes.byref(out)):
            encrypted = bytes(out.pbData[:out.cbData])
            ctypes.windll.kernel32.LocalFree(out.pbData)
            return encrypted
    except Exception:
        pass
    return None

def _dpapi_decrypt(data: bytes) -> bytes | None:
    """Windows DPAPI orqali shifr ochadi."""
    try:
        import ctypes, ctypes.wintypes
        crypt = ctypes.windll.crypt32
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.wintypes.DWORD),
                        ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
        buf = (ctypes.c_ubyte * len(data))(*data)
        inp = DATA_BLOB(len(data), buf)
        out = DATA_BLOB()
        if crypt.CryptUnprotectData(ctypes.byref(inp), None, None, None, None, 0,
                                    ctypes.byref(out)):
            decrypted = bytes(out.pbData[:out.cbData])
            ctypes.windll.kernel32.LocalFree(out.pbData)
            return decrypted
    except Exception:
        pass
    return None

_lock = threading.RLock()


def _bundle_path():
    return KEY_FILE_ENC + '.bundle'


def save_cert(cert_data: dict, private_pem: str):
    """Atomically replace one verified DPAPI bundle; never write a plaintext key.

    Installer and desktop must run as the same user. LocalService cannot read
    this user-bound blob. DPAPI does not provide TPM/non-exportability guarantees.
    """
    with _lock:
        payload = json.dumps({'version': 1, 'certificate': cert_data,
                              'private_pem': private_pem}, sort_keys=True).encode()
        encrypted = _dpapi_encrypt(payload)
        if not encrypted or _dpapi_decrypt(encrypted) != payload:
            raise OSError('Protected credential storage unavailable or verification failed')
        _ensure_dir()
        descriptor, temporary = tempfile.mkstemp(prefix='.credential-', dir=CERT_DIR)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(encrypted)
                stream.flush()
                os.fsync(stream.fileno())
            with open(temporary, 'rb') as stream:
                if _dpapi_decrypt(stream.read()) != payload:
                    raise OSError('Protected credential verification failed')
            os.replace(temporary, _bundle_path())
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
        # Original files are retained until the entire protected bundle is durable.
        for path in (KEY_FILE, KEY_FILE_ENC, CERT_FILE):
            if os.path.exists(path):
                os.remove(path)


def _read_bundle():
    with _lock:
        if os.path.exists(_bundle_path()):
            with open(_bundle_path(), 'rb') as stream:
                decrypted = _dpapi_decrypt(stream.read())
            if not decrypted:
                return None
            data = json.loads(decrypted)
            if data.get('version') != 1 or not isinstance(data.get('certificate'), dict) or not isinstance(data.get('private_pem'), str):
                return None
            if os.path.exists(KEY_FILE):
                # Interrupted cleanup must not silently retain a plaintext secret.
                with open(KEY_FILE, 'rb') as stream:
                    if not hmac.compare_digest(stream.read(), data['private_pem'].encode()):
                        return None
                os.remove(KEY_FILE)
            return data
        if not os.path.exists(CERT_FILE):
            return None
        with open(CERT_FILE) as stream:
            certificate = json.load(stream)
        if os.path.exists(KEY_FILE_ENC):
            with open(KEY_FILE_ENC, 'rb') as stream:
                key = _dpapi_decrypt(stream.read())
            if not key:
                return None  # Never fall back when protected storage fails.
        elif os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as stream:
                key = stream.read()
        else:
            return None
        save_cert(certificate, key.decode())
        return _read_bundle()


def _load_private_key_bytes() -> bytes | None:
    try:
        bundle = _read_bundle()
        return bundle['private_pem'].encode() if bundle else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def load_cert() -> dict | None:
    try:
        bundle = _read_bundle()
        return bundle['certificate'] if bundle else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def delete_cert():
    with _lock:
        for path in (_bundle_path(), CERT_FILE, KEY_FILE, KEY_FILE_ENC):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


def validate_protection(private_pem):
    """Check protection before sending a token-consuming enrollment request."""
    data=private_pem.encode()
    encrypted=_dpapi_encrypt(data)
    if not encrypted or _dpapi_decrypt(encrypted) != data:
        raise OSError('Protected credential storage unavailable')
