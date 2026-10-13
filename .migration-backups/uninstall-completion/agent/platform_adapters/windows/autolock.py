"""
core/autolock.py — Auto-lock (doc 04-bo'lim)

TUZATISHLAR:
  1. time.sleep(30) LOOP OXIRIGA ko'chirildi (loop boshida emas)
     Sabab: oldin sleep → tekshiruv → sleep edi
     Natija: foydalanuvchi faol bo'lsa ham, 30s uxlab, keyin idle=0
     hisoblab, remaining=timeout (masalan 300) → warned=False reset
     Bo'ladi, lekin KEYINGI 30s uxlaydi, ana o'sha orada foydalanuvchi
     hech narsa qilmasa idle=30s bo'lib qoladi → remaining=270 → OK
     LEKIN: agar timeout=60s bo'lsa, foydalanuvchi 1s harakatda
     bo'lsa: sleep(30) → idle=1s → remaining=59 → OK
     sleep(30) → idle=31s → remaining=29 → WARN → sleep(30) → idle=61
     → remaining=-1 → LOCK ← BU XATO: foydalanuvchi 31s dan keyin
     faol bo'lsa ham, sleep(30) da qulflanib qoladi

  2. warned reset faqat idle < CHECK_INTERVAL bo'lsa (30s emas, 5s)
     Chunki sleep(30) bilan idle<30 sharti juda keng

  3. CHECK_INTERVAL = 5s (30s emas) — aniqroq tekshiruv
"""

import threading
import time
import ctypes

_running        = False
_timeout        = 300   # soniya
_on_warn        = None  # callable(seconds_left)
_on_lock        = None  # callable()
CHECK_INTERVAL  = 5     # har 5 sek tekshiradi (30s emas)
WARN_THRESHOLD  = 30    # timeout - 30s qolsa ogohlantirish


def _get_idle_seconds() -> float:
    """Windows GetLastInputInfo orqali harakatsizlik vaqti."""
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except Exception:
        return 0.0


def _loop():
    """
    FIX: sleep OXIRIDA — dastlab tekshiruv, keyin kutish.
    FIX: CHECK_INTERVAL = 5s — aniq idle vaqt o'lchovi.
    FIX: warned reset — faqat idle < CHECK_INTERVAL (haqiqiy faollik).
    """
    global _running
    warned = False

    while _running:
        idle      = _get_idle_seconds()
        remaining = _timeout - idle

        # Foydalanuvchi haqiqatan faol — warned ni reset qil
        # idle < CHECK_INTERVAL: oxirgi 5 sek ichida harakat bo'lgan
        if idle < CHECK_INTERVAL:
            warned = False

        # Qulflash vaqti keldi
        if remaining <= 0:
            _running = False
            if _on_lock:
                try:
                    _on_lock()
                except Exception:
                    pass
            return

        # Ogohlantirish: timeout - 30s qoldi, hali ogohlantirilmagan
        if remaining <= WARN_THRESHOLD and not warned:
            warned = True
            if _on_warn:
                try:
                    _on_warn(max(0, int(remaining)))
                except Exception:
                    pass

        # FIX: sleep OXIRDA — birinchi tekshiruv darhol bo'ladi
        for _ in range(CHECK_INTERVAL * 10):
            if not _running:
                return
            time.sleep(0.1)


def start_autolock(timeout_seconds: int, on_warn, on_lock):
    global _running, _timeout, _on_warn, _on_lock
    stop_autolock()
    _timeout = max(60, timeout_seconds)
    _on_warn = on_warn
    _on_lock = on_lock
    _running = True
    threading.Thread(target=_loop, daemon=True).start()
    print(f"[autolock] started, timeout={_timeout}s, check_interval={CHECK_INTERVAL}s")


def stop_autolock():
    global _running
    _running = False
