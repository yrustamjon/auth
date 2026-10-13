"""
core/disable_manager.py — Agent holat boshqaruvi

TUZATISH: get_local_ip() o'chirildi — lan_server.py dan import qilinadi
  Sabab: ikki faylda bir xil funksiya takrorlanishi yo'q qilindi
"""

import os
import threading
import time

from platform_adapters.factory import get_platform_adapter

_platform = None


def configure_platform(adapter):
    """Receive OS actions from application bootstrap."""
    global _platform
    _platform = adapter


def _get_platform():
    return _platform if _platform is not None else get_platform_adapter()

APPDATA       = os.environ.get("APPDATA", "")
BIOGUARD_DIR  = os.path.join(APPDATA, "ADBioGuard")
DISABLED_FLAG = os.path.join(BIOGUARD_DIR, "disabled.flag")

_lock_state      = "locked"
_state_lock      = threading.Lock()
_watcher_running = False


# ── Holat ──────────────────────────────────────────────────────────────────

def set_lock_state(state: str):
    global _lock_state
    with _state_lock:
        _lock_state = state


def get_lock_state() -> str:
    if is_disabled():
        return "disabled"
    with _state_lock:
        return _lock_state


def is_disabled() -> bool:
    return os.path.exists(DISABLED_FLAG)


def _set_disabled(value: bool):
    os.makedirs(BIOGUARD_DIR, exist_ok=True)
    if value:
        open(DISABLED_FLAG, "w").write("1")
    else:
        try:
            os.remove(DISABLED_FLAG)
        except Exception:
            pass


# ── Disable ────────────────────────────────────────────────────────────────

def do_disable():
    """LAN buyruq: lock ochiladi, disabled.flag qo'yiladi."""
    print("[disable-manager] DISABLE")
    _set_disabled(True)
    set_lock_state("disabled")

    try:
        _get_platform().disable_session()
    except Exception as e:
        print(f"[disable-manager] hide error: {e}")

    _trigger_broadcast()
    _start_internet_watcher()
    print("[disable-manager] agent disabled — PC ochiq")


# ── Enable ─────────────────────────────────────────────────────────────────

def do_enable():
    """LAN buyruq: flag o'chadi, agent qayta yonadi."""
    print("[disable-manager] ENABLE")
    _set_disabled(False)
    _restart_agent()


# ── Internet watcher ───────────────────────────────────────────────────────

def _start_internet_watcher():
    global _watcher_running
    if _watcher_running:
        return
    _watcher_running = True
    threading.Thread(target=_watcher_loop, daemon=True).start()
    print("[disable-manager] internet watcher started")


def _watcher_loop():
    global _watcher_running
    while _watcher_running:
        time.sleep(30)
        try:
            from api.client import is_online
            if is_online():
                if not is_disabled():
                    print("[disable-manager] internet keldi + flag yo'q → agent yonadi")
                    _watcher_running = False
                    _restart_agent()
                    return
                else:
                    print("[disable-manager] internet keldi, flag BOR → yotib qoladi")
        except Exception:
            pass
    _watcher_running = False


# ── Restart ────────────────────────────────────────────────────────────────

def _restart_agent():
    """Agent jarayonini qayta ishga tushiradi."""
    try:
        _get_platform().restart_agent()
    except Exception as e:
        print(f"[disable-manager] restart xato: {e}")


def _trigger_broadcast():
    """Broadcast ni darhol yangilaydi."""
    try:
        # FIX: get_local_ip lan_server.py dan import qilinadi (takrorlanish yo'q)
        from services.lan_server import get_local_ip
        from core.cert import get_org_slug
        from core.config import USERNAME
        import socket, json

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg  = json.dumps({
            "pc_name":  socket.gethostname(),
            "ip":       get_local_ip(),
            "username": USERNAME,
            "org_slug": get_org_slug(),
            "state":    "disabled",
        }).encode()
        sock.sendto(msg, ("<broadcast>", 7748))
        sock.close()
    except Exception:
        pass
