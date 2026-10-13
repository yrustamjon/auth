"""
AD BioGuard â€” Desktop Biometric Lock Agent
main.py â€” Asosiy kirish nuqtasi
"""

import os
import sys
import ctypes

import webview

# DPI awareness ENG BIRINCHI chaqirilishi kerak
from platform_adapters.windows.dpi import set_dpi_awareness
set_dpi_awareness()

from core.config import DEV_MODE, USERNAME
from platform_adapters.windows.keyboard import start_keyboard_block, stop_keyboard_block
from platform_adapters.windows.taskbar import hide_taskbar, show_taskbar
from platform_adapters.windows.monitors import get_all_monitors, start_fullscreen_monitor, stop_fullscreen_monitor

from platform_adapters.windows.camera import write_chromium_camera_pref

from platform_adapters.windows.overlay import create_overlays, destroy_overlays
import platform_adapters.windows.session_monitor as _sm
from app.paths import application_root
from app.bootstrap import create_controller

from services.lan_server import start_lan_server
from services.disable_manager import set_lock_state
from platform_adapters.windows.display_mode import switch_extend, switch_internal


def main():
    # Faqat bitta instance â€” mutex
    _mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "ADBioGuardMutex")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)

    switch_internal()
    hide_taskbar()
    start_keyboard_block()

    monitors = get_all_monitors()
    primary  = monitors[0] if monitors else (0, 0, 1920, 1080)
    px, py, pw, ph = primary
    print(f"[primary] x={px} y={py} w={pw} h={ph}")

    base_dir = str(application_root())

    if len(monitors) > 1:
        create_overlays(monitors[1:], base_dir)

    ui_path = os.path.join(base_dir, "ui", "index.html")
    url     = "file:///" + ui_path.replace("\\", "/")

    window = webview.create_window(
        "AD BioGuard",
        url=url,
        width=pw,
        height=ph,
        x=px,
        y=py,
        fullscreen=False,
        frameless=True,
        on_top=True,
        easy_drag=False,
        background_color="#040812",
        min_size=(800, 500),
    )

    _sm.MAIN_WINDOW = window


    def _on_closed():
        stop_keyboard_block()
        stop_fullscreen_monitor()
        show_taskbar()
        destroy_overlays()
        switch_extend()

    def _on_shown():
        start_fullscreen_monitor(px, py, pw, ph)
        set_lock_state("locked")

    window.events.closed += _on_closed
    window.events.shown  += _on_shown

    api = create_controller(window)
    platform_adapter = api._platform
    _sm.MAIN_API = api

    window.expose(api.get_config)
    window.expose(api.start_session)
    window.expose(api.capture_face)
    window.expose(api.start_face_qr_poll)
    window.expose(api.stop_face_poll)
    window.expose(api.start_finger_poll)
    window.expose(api.stop_finger_poll)
    window.expose(api.hide_lock)
    window.expose(api.dev_exit)
    # Doc 06 â€” offline login
    window.expose(api.offline_login)
    # Doc 04 â€” auto-lock
    window.expose(api.start_autolock_monitor)
    window.expose(api.extend_session)
    # Doc 02 â€” aktivatsiya
    window.expose(api.activate_org)
    window.expose(api.activate_personal)
    window.expose(api.start_internet_monitor)
    # Personal offline parol
    window.expose(api.set_personal_offline_password)
    window.expose(api.personal_offline_login)

    # Admin panel
    window.expose(api.set_admin_password)
    window.expose(api.admin_login)
    window.expose(api.get_lan_peers)
    window.expose(api.refresh_lan_peer)
    window.expose(api.lan_command)
    window.expose(api.lan_command_all)

    # LAN server ishga tushirish
    start_lan_server()

    # Chromium kamera ruxsatlari
    data_dir = os.path.join(base_dir, ".webview_data")
    os.makedirs(data_dir, exist_ok=True)
    write_chromium_camera_pref(data_dir)

    platform_adapter.start_service()

    # storage_path olib tashlandi â€” file:// URL bilan conflict qiladi
    webview.start(
        gui='edgechromium',
        debug=DEV_MODE,
        private_mode=False,
    )


if __name__ == "__main__":
    main()
