"""Windows registry identity; existing identifiers remain unchanged."""
import os
import subprocess
import uuid as _uuid
from storage.paths import application_data_dir

def get_device_uuid() -> str:
    """Windows MachineGUID — PC ning noyob identifikatori."""
    try:
        out = subprocess.check_output(
            ["reg", "query",
             r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography",
             "/v", "MachineGuid"],
            stderr=subprocess.DEVNULL
        ).decode(errors="ignore")
        for line in out.splitlines():
            if "MachineGuid" in line:
                return line.strip().split()[-1]
    except Exception:
        pass
    # Fallback — application data directory, not the project working directory.
    path = os.path.join(application_data_dir(), "uuid.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as stored_uuid:
            return stored_uuid.read().strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    uid = str(_uuid.uuid4())
    with open(path, "w", encoding="utf-8") as stored_uuid:
        stored_uuid.write(uid)
    return uid

def get_windows_license() -> str:
    """Windows Product ID — litsenziya identifikatori."""
    try:
        out = subprocess.check_output(
            ["reg", "query",
             r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion",
             "/v", "ProductId"],
            stderr=subprocess.DEVNULL
        ).decode(errors="ignore")
        for line in out.splitlines():
            if "ProductId" in line:
                return line.strip().split()[-1]
    except Exception:
        pass
    return "UNKNOWN"
