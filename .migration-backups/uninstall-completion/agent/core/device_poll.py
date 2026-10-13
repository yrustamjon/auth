"""
core/device_poll.py — Server polling: PC holati va foydalanuvchi blok tekshiruvi

Session davomida har 30 sek serverga so'rov yuboradi:
  GET /api/agent/device/status/

Javob:
  {"status": "active"}                    → davom etadi
  {"status": "blocked_device"}            → darhol relock
  {"status": "blocked_user"}              → darhol relock
  {"status": "disabled"}                  → darhol relock
  {"status": "revoked"}                   → sertifikat o'chirilgan, relock
"""

import threading
import time

_running   = False
_on_relock = None   # callable(reason: str)
_interval  = 30     # soniya


def _loop():
    global _running
    from api.client import api_get, is_online
    from core.config import DEVICE_UUID, USERNAME

    while _running:
        time.sleep(_interval)
        if not _running:
            break

        # Internet yo'q bo'lsa — skip
        if not is_online():
            continue

        try:
            data = api_get(
                f"/api/agent/device/status/"
                f"?pc_id={DEVICE_UUID}&username={USERNAME}"
            )
            status = data if isinstance(data, str) else data.get("status", "active")

            if status == "active":
                continue

            # Bloklangan — relock
            _running = False
            if _on_relock:
                try:
                    _on_relock(status)
                except Exception:
                    pass
            return

        except Exception as e:
            # Server xatosi — xavfsiz tomon uchun davom etamiz
            print(f"[device-poll] xato: {e}")


def start_device_poll(on_relock, interval: int = 30):
    """
    Server polling ni boshlaydi.
    on_relock(status) — bloklanganda chaqiriladi.
    interval — soniyalarda tekshiruv oralig'i (default 30).
    """
    global _running, _on_relock, _interval
    stop_device_poll()
    _on_relock = on_relock
    _interval  = max(10, interval)
    _running   = True
    threading.Thread(target=_loop, daemon=True).start()
    print(f"[device-poll] started, interval={_interval}s")


def stop_device_poll():
    global _running
    _running = False
