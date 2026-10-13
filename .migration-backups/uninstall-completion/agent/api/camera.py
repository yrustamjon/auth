"""
api/camera.py — Kamera mavjudligini tekshirish va Chromium ruxsatlarini yozish
"""

import json
import os


def check_camera() -> bool:
    """Kamera (index 0) ochilishini tekshiradi."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ok = cap.isOpened()
        cap.release()
        return ok
    except Exception:
        return False


def write_chromium_camera_pref(data_dir: str) -> None:
    """Compatibility wrapper for Windows Chromium permission setup."""
    from platform_adapters.windows.camera import write_chromium_camera_pref as write_pref
    write_pref(data_dir)
