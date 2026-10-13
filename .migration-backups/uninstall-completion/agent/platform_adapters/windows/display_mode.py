import subprocess
import threading
import time

_lock = threading.Lock()
_last_mode = "extend"


def _run_display_switch(arg: str):
    subprocess.Popen(["DisplaySwitch.exe", arg], creationflags=subprocess.CREATE_NO_WINDOW)


def switch_internal():
    global _last_mode
    with _lock:
        _last_mode = "internal"
        _run_display_switch("/internal")


def switch_extend():
    global _last_mode
    with _lock:
        if _last_mode != "extend":
            _last_mode = "extend"
        _run_display_switch("/extend")


def switch_extend_delayed(delay: float = 1.0):
    def _worker():
        time.sleep(delay)
        try:
            switch_extend()
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()
