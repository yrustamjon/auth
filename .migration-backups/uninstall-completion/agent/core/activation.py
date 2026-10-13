"""
core/activation.py — Agent aktivatsiya (doc 02-bo'lim)

Org oqimi:
  1. activation_code + device_uuid + windows_license + public_key → server
  2. Server: code qaysi orgga tegishli → PC ni o'sha orgga bog'laydi
  3. Server → unique PC sertifikat qaytaradi
  4. Sertifikat saqlanadi, activation code xotiradan o'chiriladi
"""

import json

from api.client import get_default_client
from core.config import DEVICE_UUID, WINDOWS_LICENSE
from core.cert import generate_keypair, save_cert, is_activated
from core.network.errors import BackendApiError, BackendResponseError
from core.network.signatures import sign_headers


class ActivationError(Exception):
    pass


def activate_org(activation_code: str, *, force: bool = False, keypair=None) -> dict:
    """
    Org PC ni aktivatsiya qiladi.
    Activation Code — IT manager bergan kod, server qaysi orgga tegishli ekanini o'zi aniqlaydi.
    """
    if not force and is_activated():
        return {"status": "already_activated"}

    if not activation_code or not activation_code.strip():
        raise ActivationError("Activation Code kiritilishi shart")

    public_pem, private_pem = keypair if keypair is not None else generate_keypair()
    from storage.legacy_windows_cert import validate_protection
    try:
        validate_protection(private_pem)
    except OSError as error:
        raise ActivationError('Protected credential storage unavailable') from error

    payload = {
        "activation_code":  activation_code.strip(),
        "device_uuid":      DEVICE_UUID,
        "windows_license":  WINDOWS_LICENSE,
        "public_key":       public_pem,
    }

    try:
        data = get_default_client().post("/api/agent/activate/", payload, timeout=15,
            request_signer=lambda method, target, body: sign_headers(private_pem.encode(), method, target, body, DEVICE_UUID, "bootstrap"))
    except BackendResponseError as error:
        raise ActivationError(_activation_error_message(error)) from error
    except BackendApiError as error:
        raise ActivationError(str(error)) from error

    cert_data = data.get("certificate")
    if not cert_data:
        raise ActivationError("Server sertifikat qaytarmadi")

    offline_hash = data.get("offline_admin_hash")
    offline_user = data.get("offline_admin_username")
    if offline_hash and offline_user:
        from core.offline import save_offline_creds
        save_offline_creds(offline_user, offline_hash)

    try:
        save_cert(cert_data, private_pem)
    except OSError as error:
        raise ActivationError('Enrollment returned but protected credential persistence failed; request administrator recovery') from error

    # activation_code xotiradan o'chiriladi
    # Python strings cannot be guaranteed securely erased. Avoid persistent copies.
    activation_code = "0" * len(activation_code)  # noqa
    del activation_code

    print(f"[activation] OK — cert_id={cert_data.get('cert_id', '')[:8]}...")
    return data


def activate_personal(email: str, password: str, *, force: bool = False) -> dict:
    """Orgsiz foydalanuvchi aktivatsiyasi."""
    if not force and is_activated():
        return {"status": "already_activated"}

    public_pem, private_pem = generate_keypair()
    from storage.legacy_windows_cert import validate_protection
    try:
        validate_protection(private_pem)
    except OSError as error:
        raise ActivationError('Protected credential storage unavailable') from error

    payload = {
        "email":           email,
        "password":        password,
        "device_uuid":     DEVICE_UUID,
        "windows_license": WINDOWS_LICENSE,
        "public_key":      public_pem,
    }

    try:
        data = get_default_client().post(
            "/api/agent/activate/personal/",
            payload,
            timeout=15,
            request_signer=lambda method, target, body: sign_headers(private_pem.encode(), method, target, body, DEVICE_UUID, "bootstrap"),
        )
    except BackendResponseError as error:
        raise ActivationError(_activation_error_message(error)) from error
    except BackendApiError as error:
        raise ActivationError(str(error)) from error

    cert_data = data.get("certificate")
    if not cert_data:
        raise ActivationError("Server sertifikat qaytarmadi")

    try:
        save_cert(cert_data, private_pem)
    except OSError as error:
        raise ActivationError('Enrollment returned but protected credential persistence failed; request administrator recovery') from error
    return data


def _activation_error_message(error: BackendResponseError) -> str:
    """Preserve legacy backend detail text without logging activation secrets."""
    body = error.response_body
    if body:
        try:
            detail = json.loads(body).get("detail")
            if isinstance(detail, str) and detail:
                return detail
        except json.JSONDecodeError:
            pass
        return f"HTTP {error.status_code}: {body[:200]}"
    return f"HTTP {error.status_code}" if error.status_code else str(error)
