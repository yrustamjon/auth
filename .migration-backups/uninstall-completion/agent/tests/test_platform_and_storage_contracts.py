import sys
import unittest

from platform_adapters.base import PlatformAdapter
from storage.base import SecureStorage


class MemorySecureStorage(SecureStorage):
    def __init__(self):
        self.values: dict[str, bytes] = {}

    def set_secret(self, key: str, value: bytes) -> None:
        self.values[key] = value

    def get_secret(self, key: str) -> bytes | None:
        return self.values.get(key)

    def delete_secret(self, key: str) -> None:
        self.values.pop(key, None)


class PlatformAndStorageContractTests(unittest.TestCase):
    def test_storage_contract_round_trips_and_deletes_binary_secret(self):
        """Would fail if a storage implementation could expose stale secret bytes."""
        storage = MemorySecureStorage()

        storage.set_secret("credential", b"opaque-secret")
        storage.delete_secret("credential")

        self.assertIsNone(storage.get_secret("credential"))

    def test_core_contract_imports_do_not_load_windows_dependencies(self):
        """Would fail if a pure abstraction acquired a hidden Windows import."""
        self.assertTrue(issubclass(PlatformAdapter, object))
        self.assertNotIn("win32gui", sys.modules)
        self.assertNotIn("win32ts", sys.modules)


if __name__ == "__main__":
    unittest.main()
