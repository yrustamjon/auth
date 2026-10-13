"""Windows DPAPI-backed secure storage.

DPAPI protects data for the Windows user context. It is not represented as TPM
or non-exportable hardware-key storage.
"""

import hashlib
import os
from pathlib import Path
import sys
import tempfile

from .base import SecureStorage, SecureStorageError


class WindowsSecureStorage(SecureStorage):
    """Persist opaque bytes as DPAPI-protected blobs on Windows only."""

    def __init__(self, storage_dir: str | os.PathLike[str] | None = None):
        if sys.platform != "win32":
            raise SecureStorageError("Windows DPAPI storage is unavailable on this platform")
        root = storage_dir or os.path.join(os.environ.get("APPDATA", ""), "ADBioGuard", "secrets")
        self._storage_dir = Path(root)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def set_secret(self, key: str, value: bytes) -> None:
        self._validate(key, value)
        encrypted = self._encrypt(value)
        target = self._path_for(key)
        descriptor, temporary_path = tempfile.mkstemp(
            dir=self._storage_dir,
            prefix=".secret-",
        )
        try:
            with os.fdopen(descriptor, "wb") as temporary_file:
                temporary_file.write(encrypted)
            os.replace(temporary_path, target)
        except OSError as error:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            raise SecureStorageError("Could not persist DPAPI-protected secret") from error

    def get_secret(self, key: str) -> bytes | None:
        self._validate(key)
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            encrypted = path.read_bytes()
        except OSError as error:
            raise SecureStorageError("Could not read DPAPI-protected secret") from error
        return self._decrypt(encrypted)

    def delete_secret(self, key: str) -> None:
        self._validate(key)
        try:
            self._path_for(key).unlink(missing_ok=True)
        except OSError as error:
            raise SecureStorageError("Could not delete DPAPI-protected secret") from error

    def _path_for(self, key: str) -> Path:
        return self._storage_dir / hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate(key: str, value: bytes | None = None) -> None:
        if not key:
            raise ValueError("Secure storage key must not be empty")
        if value is not None and not isinstance(value, bytes):
            raise TypeError("Secure storage values must be bytes")

    @staticmethod
    def _encrypt(value: bytes) -> bytes:
        from core.cert import _dpapi_encrypt

        encrypted = _dpapi_encrypt(value)
        if encrypted is None:
            raise SecureStorageError("Windows DPAPI encryption failed")
        return encrypted

    @staticmethod
    def _decrypt(value: bytes) -> bytes:
        from core.cert import _dpapi_decrypt

        decrypted = _dpapi_decrypt(value)
        if decrypted is None:
            raise SecureStorageError("Windows DPAPI decryption failed")
        return decrypted
