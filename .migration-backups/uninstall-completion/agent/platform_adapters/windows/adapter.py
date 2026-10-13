"""Windows integration through existing agent modules.

Imports of the current Windows implementation are deliberately lazy so merely
importing the common platform contract works on Linux and macOS.
"""

import socket
from typing import Any, Mapping

from platform_adapters.base import PlatformAdapter
from storage.base import SecureStorage


class WindowsPlatformAdapter(PlatformAdapter):
    """Adapter around the existing Windows session-monitor behavior."""

    def __init__(self, storage: SecureStorage | None = None):
        self._storage = storage

    @property
    def platform_name(self) -> str:
        return "windows"

    def lock_session(self) -> None:
        from platform_adapters.windows.session_monitor import relock_system

        relock_system()

    def unlock_session(self) -> None:
        from platform_adapters.windows.display_mode import switch_extend
        from platform_adapters.windows.keyboard import stop_keyboard_block
        from platform_adapters.windows.monitors import stop_fullscreen_monitor
        from platform_adapters.windows.taskbar import show_taskbar
        from platform_adapters.windows.overlay import destroy_overlays

        stop_keyboard_block()
        stop_fullscreen_monitor()
        show_taskbar()
        destroy_overlays()
        switch_extend()

    def get_device_metadata(self) -> Mapping[str, Any]:
        from core.config import DEVICE_UUID

        return {
            "device_id": DEVICE_UUID,
            "hostname": socket.gethostname(),
            "platform": self.platform_name,
        }

    def start_service(self) -> None:
        from platform_adapters.windows.session_monitor import start_session_monitor

        start_session_monitor()

    def secure_storage(self) -> SecureStorage:
        if self._storage is None:
            from storage.windows import WindowsSecureStorage

            self._storage = WindowsSecureStorage()
        return self._storage

    def start_autolock(self, timeout, on_warn, on_lock) -> None:
        from .autolock import start_autolock
        start_autolock(timeout, on_warn, on_lock)

    def stop_autolock(self) -> None:
        from .autolock import stop_autolock
        stop_autolock()

    def disable_session(self) -> None:
        from . import session_monitor
        self.unlock_session()
        if session_monitor.MAIN_WINDOW:
            session_monitor.MAIN_WINDOW.hide()

    def restart_agent(self) -> None:
        import subprocess
        import sys
        import time
        from app.paths import application_root
        command = [sys.executable] if getattr(sys, "frozen", False) else [
            sys.executable, str(application_root() / "main.py")]
        subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(1)
        sys.exit(0)
