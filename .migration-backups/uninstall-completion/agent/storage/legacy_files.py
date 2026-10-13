"""Existing JSON credential files; paths and formats intentionally preserved.

These legacy files are not represented as the new secure-storage implementation.
Changing encryption or migrating existing data is a separate change.
"""
import json
import os

LEGACY_DATA_DIR = os.path.join(os.environ.get("APPDATA", ""), "ADBioGuard")
OFFLINE_FILE = os.path.join(LEGACY_DATA_DIR, "offline.json")
PERSONAL_OFFLINE_FILE = os.path.join(LEGACY_DATA_DIR, "personal_offline.json")
ADMIN_FILE = os.path.join(LEGACY_DATA_DIR, "admin.json")


def exists(path: str) -> bool:
    return os.path.exists(path)


def read_json(path: str):
    with open(path) as stored:
        return json.load(stored)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as stored:
        json.dump(data, stored)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
