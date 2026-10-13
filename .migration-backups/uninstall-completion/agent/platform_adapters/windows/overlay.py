"""
windows/overlay.py - Ikkilamchi monitorlar uchun native blackout overlay.
"""

import threading
import time
import uuid

import win32api
import win32con
import win32gui

_overlay_windows = []
_lock = threading.Lock()


def _overlay_wndproc(stop_event):
    def _proc(hwnd, msg, wparam, lparam):
        if msg == win32con.WM_CLOSE:
            try:
                win32gui.DestroyWindow(hwnd)
            except Exception:
                pass
            return 0

        if msg == win32con.WM_DESTROY:
            stop_event.set()
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    return _proc


def _enforce_topmost(hwnd: int, x: int, y: int, w: int, h: int, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                x,
                y,
                w,
                h,
                win32con.SWP_SHOWWINDOW,
            )
        except Exception:
            break
        time.sleep(0.2)


def _run_overlay(x: int, y: int, w: int, h: int, title: str,
                 stop_event: threading.Event, ready_event: threading.Event, holder: dict):
    class_name = f"ADBioGuardOverlay_{uuid.uuid4().hex}"
    hinstance = win32api.GetModuleHandle(None)

    wc = win32gui.WNDCLASS()
    wc.hInstance = hinstance
    wc.lpszClassName = class_name
    wc.lpfnWndProc = _overlay_wndproc(stop_event)
    wc.hbrBackground = win32gui.GetStockObject(win32con.BLACK_BRUSH)

    class_atom = win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindowEx(
        win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
        class_atom,
        title,
        win32con.WS_POPUP,
        x,
        y,
        w,
        h,
        0,
        0,
        hinstance,
        None,
    )

    holder["hwnd"] = hwnd
    holder["class_name"] = class_name

    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    win32gui.UpdateWindow(hwnd)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        x,
        y,
        w,
        h,
        win32con.SWP_SHOWWINDOW,
    )

    threading.Thread(
        target=_enforce_topmost,
        args=(hwnd, x, y, w, h, stop_event),
        daemon=True,
    ).start()

    ready_event.set()
    win32gui.PumpMessages()

    try:
        win32gui.UnregisterClass(class_name, hinstance)
    except Exception:
        pass


def create_overlays(secondary_monitors: list, base_dir: str) -> None:
    destroy_overlays()

    for index, (x, y, w, h) in enumerate(secondary_monitors, start=1):
        title = f"AD BioGuard Overlay {index}"
        stop_event = threading.Event()
        ready_event = threading.Event()
        holder = {"hwnd": None, "class_name": None}

        thread = threading.Thread(
            target=_run_overlay,
            args=(x, y, w, h, title, stop_event, ready_event, holder),
            daemon=True,
        )
        thread.start()
        ready_event.wait(timeout=2)

        with _lock:
            _overlay_windows.append({
                "title": title,
                "thread": thread,
                "stop_event": stop_event,
                "holder": holder,
            })

        print(f"[overlay] native blocker @ {x},{y} {w}x{h} | {title}")


def destroy_overlays() -> None:
    with _lock:
        overlays = list(_overlay_windows)
        _overlay_windows.clear()

    for overlay in overlays:
        overlay["stop_event"].set()
        hwnd = overlay["holder"].get("hwnd")
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass

    for overlay in overlays:
        thread = overlay["thread"]
        if thread.is_alive():
            thread.join(timeout=1)
