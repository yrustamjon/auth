"""Reserved macOS Keychain integration."""
from storage.base import SecureStorageError


class MacOSSecureStorage:
    def __init__(self):
        raise SecureStorageError("macOS secure storage is not implemented")
