"""Reserved Linux secure storage; no insecure fallback is provided."""
from storage.base import SecureStorageError


class LinuxSecureStorage:
    def __init__(self):
        raise SecureStorageError("Linux secure storage is not implemented")
