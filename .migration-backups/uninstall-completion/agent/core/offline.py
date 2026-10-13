"""
core/offline.py — Internet uzilganda offline kirish (doc 06-bo'lim)

TUZATISH: Funksiya ichidagi keraksiz importlar olib tashlandi
  secrets, base64, hashlib — fayl boshida bir marta import qilinadi
"""

import hashlib
import hmac
import base64
import secrets          # FIX: bir marta import

from core.config import API_BASE, DEVICE_UUID

from storage.legacy_files import (
    OFFLINE_FILE, PERSONAL_OFFLINE_FILE, ADMIN_FILE, exists, read_json, write_json,
)

PBKDF2_ITERATIONS = 100_000
PBKDF2_DKLEN      = 32


# ── Admin parol ───────────────────────────────────────────────────────────

def has_admin_password() -> bool:
    return exists(ADMIN_FILE)


def set_admin_password(password: str):
    """Aktivatsiyada o'rnatiladi — MAJBURIY."""
    if not password or len(password) < 6:
        raise ValueError("Admin parol kamida 6 ta belgi bo'lishi kerak")
    # FIX: funksiya ichida import yo'q — fayl boshida allaqachon bor
    salt    = secrets.token_bytes(32)
    dk      = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS, dklen=PBKDF2_DKLEN)
    pw_hash = base64.b64encode(dk).decode()
    pw_salt = base64.b64encode(salt).decode()
    write_json(ADMIN_FILE, {
            "hash":       pw_hash,
            "salt":       pw_salt,
            "algo":       "pbkdf2_sha256",
            "iterations": PBKDF2_ITERATIONS,
        })
    print("[admin] parol o'rnatildi")


def verify_admin_password(password: str) -> bool:
    if not has_admin_password():
        return False
    try:
        data = read_json(ADMIN_FILE)
        stored_hash = data.get("hash", "")
        stored_salt = data.get("salt", "")
        if not stored_salt:
            ph = hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(ph, stored_hash)
        salt     = base64.b64decode(stored_salt)
        dk       = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS, dklen=PBKDF2_DKLEN)
        expected = base64.b64encode(dk).decode()
        return hmac.compare_digest(expected, stored_hash)
    except Exception:
        return False


def get_admin_token() -> str:
    try:
        from core.cert import get_org_slug
        org_slug = get_org_slug()
        if not org_slug or not has_admin_password():
            return ""
        data = read_json(ADMIN_FILE)
        raw = f"{org_slug}:{data.get('hash', '')}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return ""


# ── Hash yordamchi funksiyalar ─────────────────────────────────────────────

def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(32)
    dk      = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=PBKDF2_DKLEN)
    h_b64   = base64.b64encode(dk).decode()
    s_b64   = base64.b64encode(salt).decode()
    return h_b64, s_b64


def _verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    try:
        salt     = base64.b64decode(stored_salt)
        dk       = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=PBKDF2_DKLEN)
        expected = base64.b64encode(dk).decode()
        return hmac.compare_digest(expected, stored_hash)
    except Exception:
        return False


# ── Org admin offline kirish ───────────────────────────────────────────────

def has_offline_creds() -> bool:
    return exists(OFFLINE_FILE)


def verify_offline(username: str, password: str) -> bool:
    if not has_offline_creds():
        return False
    try:
        data = read_json(OFFLINE_FILE)
        if data.get("username", "").lower() != username.lower():
            return False
        return _verify_password(password, data["hash"], data["salt"])
    except Exception:
        return False


def save_offline_creds(username: str, password: str):
    h, s = _hash_password(password)
    write_json(OFFLINE_FILE, {
            "username":   username,
            "hash":       h,
            "salt":       s,
            "algo":       "pbkdf2_sha256",
            "iterations": PBKDF2_ITERATIONS,
        })


# ── Personal offline ───────────────────────────────────────────────────────

def has_personal_offline() -> bool:
    return exists(PERSONAL_OFFLINE_FILE)


def set_personal_offline_password(password: str):
    if not password or len(password) < 6:
        raise ValueError("Parol kamida 6 ta belgi bo'lishi kerak")
    h, s = _hash_password(password)
    write_json(PERSONAL_OFFLINE_FILE, {
            "hash":       h,
            "salt":       s,
            "algo":       "pbkdf2_sha256",
            "iterations": PBKDF2_ITERATIONS,
        })


def verify_personal_offline(password: str) -> bool:
    if not has_personal_offline():
        return False
    try:
        data = read_json(PERSONAL_OFFLINE_FILE)
        return _verify_password(password, data["hash"], data["salt"])
    except Exception:
        return False
