import tkinter as tk
import getpass
import keyboard
import ctypes
from screeninfo import get_monitors

username = getpass.getuser()
windows = []

# ===== taskbar hide =====
user32 = ctypes.windll.user32
hwnd = user32.FindWindowW("Shell_TrayWnd", None)
user32.ShowWindow(hwnd, 0)

# ===== keyboard block =====
blocked_keys = [
    "windows",
    "alt",
    "tab",
    "esc",
    "ctrl",
    "shift",
    "f4"
]

for key in blocked_keys:
    keyboard.block_key(key)

def block_event(event):
    return "break"

def close_all():
    keyboard.unhook_all()

    # taskbar restore
    user32.ShowWindow(hwnd, 5)

    for w in windows:
        w.destroy()

def create_window(monitor):
    win = tk.Tk() if not windows else tk.Toplevel()

    win.overrideredirect(True)
    win.attributes("-topmost", True)

    win.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")

    win.configure(bg="white")

    win.lift()
    win.focus_force()

    # keyboard block tkinter
    win.bind("<Key>", block_event)
    win.bind("<Alt-F4>", block_event)

    frame = tk.Frame(win, bg="white")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    frame.bind("<Button-1>", block_event)

    title = tk.Label(
        frame,
        text="Identity Verification Required",
        font=("Segoe UI", 22, "bold"),
        bg="white"
    )
    title.pack(pady=20)

    user_label = tk.Label(
        frame,
        text=f"User: {username}",
        font=("Segoe UI", 16),
        bg="white"
    )
    user_label.pack(pady=10)

    status = tk.Label(
        frame,
        text="Please complete biometric verification",
        font=("Segoe UI", 14),
        fg="gray",
        bg="white"
    )
    status.pack(pady=15)

    btn_frame = tk.Frame(frame, bg="white")
    btn_frame.pack(pady=25)

    def scan():
        status.config(text="Scanning started...")

    scan_btn = tk.Button(
        btn_frame,
        text="Scan",
        width=15,
        height=2,
        command=scan
    )
    scan_btn.grid(row=0, column=0, padx=15)

    skip_btn = tk.Button(
        btn_frame,
        text="Skip",
        width=15,
        height=2,
        command=close_all
    )
    skip_btn.grid(row=0, column=1, padx=15)

    windows.append(win)

for monitor in get_monitors():
    create_window(monitor)

windows[0].mainloop()