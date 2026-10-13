"""Data directory selection; preserve the existing Windows location."""
import os
import sys
import uuid


def application_data_dir() -> str:
    app_data = os.environ.get("APPDATA")
    if app_data:
        return os.path.join(app_data, "ADBioGuard")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/ADBioGuard")
    return os.path.expanduser("~/.local/share/ADBioGuard")


def persistent_device_uuid() -> str:
    path = os.path.join(application_data_dir(), "uuid.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as stored:
            return stored.read().strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    value = str(uuid.uuid4())
    with open(path, "w", encoding="utf-8") as stored:
        stored.write(value)
    return value
