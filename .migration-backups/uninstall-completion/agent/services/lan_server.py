"""
core/lan_server.py — Har bir agentda ishlaydigan LAN server

UDP 7748 — broadcast: org dagi PC lar bir-birini topadi
TCP 7749 — HTTP: holat va buyruqlar

TUZATISHLAR:
  1. start_lan_server() da o'zini DARHOL peers ga qo'shadi
  2. Birinchi broadcast DARHOL yuboriladi (60s kutmaydi)
  3. _listen_loop o'zining IP sini ham qabul qiladi (o'zini ko'radi)
  4. get_local_ip() — ikki faylda takrorlanishi o'chirildi (bu yerda master)
"""

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

UDP_PORT           = 7748
HTTP_PORT          = 7749
BROADCAST_INTERVAL = 60   # sek

_httpd          = None
_broadcast_stop = threading.Event()

APPDATA     = os.environ.get("APPDATA", "")
PEERS_FILE  = os.path.join(APPDATA, "ADBioGuard", "peers.json")
_peers_lock = threading.Lock()


# ── Yordamchi ─────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Master get_local_ip — disable_manager.py ham shu yerdan import qiladi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_pc_name() -> str:
    return socket.gethostname()


def _build_my_info() -> dict:
    """O'z PC ma'lumotlarini dict ko'rinishida qaytaradi."""
    try:
        from core.cert import get_org_slug
        from core.config import USERNAME
        from services.disable_manager import get_lock_state
        return {
            "pc_name":  get_pc_name(),
            "ip":       get_local_ip(),
            "username": USERNAME,
            "org_slug": get_org_slug(),
            "state":    get_lock_state(),
            "last_seen": int(time.time()),
        }
    except Exception as e:
        print(f"[lan] _build_my_info xato: {e}")
        return {}


# ── UDP Broadcast ──────────────────────────────────────────────────────────

def _broadcast_loop():
    """
    FIX 1: Birinchi broadcast DARHOL yuboriladi, keyin har 60 sek.
    Oldin: while → sleep(60) → broadcast  (birinchi 60s kechikish)
    Endi:  while → broadcast → sleep(60)  (darhol ko'rinadi)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)

    while not _broadcast_stop.is_set():
        try:
            info = _build_my_info()
            if info:
                msg = json.dumps(info).encode()
                sock.sendto(msg, ("<broadcast>", UDP_PORT))
        except Exception as e:
            print(f"[lan-broadcast] xato: {e}")

        # 60 sek kutamiz (0.1s lik bo'laklarda — stop ga tez javob)
        for _ in range(BROADCAST_INTERVAL * 10):
            if _broadcast_stop.is_set():
                break
            time.sleep(0.1)

    sock.close()


def _listen_loop():
    """
    FIX 2: O'zining broadcast ni ham qabul qiladi.
    Oldin: o'z IP sini filtrlar edi → o'zini ko'rmaydi
    Endi:  filtr yo'q, barcha xabarlar qabul qilinadi (o'z xabari ham)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", UDP_PORT))
    except Exception as e:
        print(f"[lan-listen] bind xato: {e}")
        return
    sock.settimeout(2)

    while not _broadcast_stop.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode())
            ip   = info.get("ip") or addr[0]
            info["ip"] = ip

            # Faqat bir xil org_slug — o'zini ham qabul qiladi
            from core.cert import get_org_slug
            my_slug = get_org_slug()
            if my_slug and info.get("org_slug") == my_slug:
                _update_peer(info)
        except socket.timeout:
            continue
        except Exception:
            continue

    sock.close()


# ── Peers.json ────────────────────────────────────────────────────────────

def _update_peer(info: dict):
    """Topilgan PC ni peers.json ga qo'shadi/yangilaydi."""
    info["last_seen"] = int(time.time())

    with _peers_lock:
        peers = _load_peers_raw()
        found = False
        for i, p in enumerate(peers):
            if p.get("ip") == info.get("ip"):
                peers[i] = info
                found = True
                break
        if not found:
            peers.append(info)

        os.makedirs(os.path.dirname(PEERS_FILE), exist_ok=True)
        with open(PEERS_FILE, "w") as f:
            json.dump(peers, f)


def _load_peers_raw() -> list:
    try:
        with open(PEERS_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def get_peers() -> list:
    """Saqlangan peers ro'yxatini qaytaradi."""
    with _peers_lock:
        peers = _load_peers_raw()

    now = int(time.time())
    result = []
    for p in peers:
        last = p.get("last_seen", 0)
        if now - last > 300:
            p["state"] = "offline"
        result.append(p)
    return result


# ── HTTP Server ────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # console log chiqarmaydi

    def _json(self, code: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            from core.config import USERNAME, DEVICE_UUID
            from core.cert import get_org_slug
            from services.disable_manager import get_lock_state, is_disabled
            self._json(200, {
                "pc_name":  get_pc_name(),
                "ip":       get_local_ip(),
                "username": USERNAME,
                "org_slug": get_org_slug(),
                "state":    get_lock_state(),
                "disabled": is_disabled(),
            })
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/command":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except Exception:
            self._json(400, {"error": "bad json"})
            return

        # Token tekshiruvi
        token = payload.get("token", "")
        from core.offline import get_admin_token
        import hmac as _hmac
        expected = get_admin_token()
        if not expected or not _hmac.compare_digest(token, expected):
            self._json(403, {"error": "forbidden"})
            return

        cmd = payload.get("cmd", "")
        if cmd == "disable":
            from services.disable_manager import do_disable
            threading.Thread(target=do_disable, daemon=True).start()
            self._json(200, {"ok": True})
        elif cmd == "enable":
            from services.disable_manager import do_enable
            threading.Thread(target=do_enable, daemon=True).start()
            self._json(200, {"ok": True})
        else:
            self._json(400, {"error": f"unknown cmd: {cmd}"})


# ── Start / Stop ──────────────────────────────────────────────────────────

def start_lan_server():
    """
    FIX 3: Ishga tushganda o'zini DARHOL peers ga qo'shadi.
    Oldin: faqat broadcast yuboradi, o'zini ko'rmaydi
    Endi:  _build_my_info() → _update_peer() → darhol ko'rinadi
    """
    global _httpd
    _broadcast_stop.clear()

    # O'zini DARHOL ro'yxatga qo'shish
    my_info = _build_my_info()
    if my_info:
        _update_peer(my_info)
        print(f"[lan-server] o'zini qo'shdi: {my_info.get('ip')} ({my_info.get('pc_name')})")

    # UDP broadcast — birinchi darhol yuboriladi
    threading.Thread(target=_broadcast_loop, daemon=True).start()
    # UDP listen — o'z xabarini ham qabul qiladi
    threading.Thread(target=_listen_loop, daemon=True).start()
    # HTTP server
    try:
        _httpd = HTTPServer(("0.0.0.0", HTTP_PORT), _Handler)
        threading.Thread(target=_httpd.serve_forever, daemon=True).start()
        print(f"[lan-server] started | ip={get_local_ip()} | udp={UDP_PORT} | http={HTTP_PORT}")
    except Exception as e:
        print(f"[lan-server] HTTP start xato: {e}")


def stop_lan_server():
    global _httpd
    _broadcast_stop.set()
    if _httpd:
        try:
            _httpd.shutdown()
        except Exception:
            pass
        _httpd = None
