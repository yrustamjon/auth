import tkinter as tk
import getpass
import ctypes
import threading
import time
import math
import json
import base64
import urllib.request

# ── optional imports ──────────────────────────────────────────────
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    from screeninfo import get_monitors as _gm
    def _get_monitors(): return _gm()
except ImportError:
    class _M:
        def __init__(self):
            u = ctypes.windll.user32
            self.width  = u.GetSystemMetrics(0)
            self.height = u.GetSystemMetrics(1)
            self.x = self.y = 0
    def _get_monitors(): return [_M()]

try:
    import qrcode
    from PIL import Image, ImageTk
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    import cv2
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════
API_BASE  = "http://localhost:8000"
DEV_MODE  = True    # True → "EXIT DEV" tugmasi ko'rinadi
DEMO_MODE = True    # True → server kerak emas
USERNAME  = getpass.getuser()

# ── colors ────────────────────────────────────────────────────────
BG        = "#0a0a14"
CARD      = "#0f1729"
CARD_DARK = "#060d1a"
BORDER    = "#1e2d4a"
BORDER2   = "#1e293b"
ACCENT    = "#3b82f6"
TEXT      = "#f1f5f9"
MUTED     = "#64748b"
DIM       = "#1e293b"
GREEN     = "#22c55e"
RED       = "#ef4444"
AMBER     = "#f59e0b"

# ── Windows API ───────────────────────────────────────────────────
user32 = ctypes.windll.user32

def hide_taskbar():
    h = user32.FindWindowW("Shell_TrayWnd", None)
    if h: user32.ShowWindow(h, 0)
    return h

def show_taskbar(h):
    if h: user32.ShowWindow(h, 5)

def block_keys():
    if not KEYBOARD_AVAILABLE: return
    for k in ["windows","alt","tab","esc","ctrl","shift",
              "f1","f2","f3","f4","f5","f11","f12"]:
        try: keyboard.block_key(k)
        except: pass

def unblock_keys():
    if not KEYBOARD_AVAILABLE: return
    try: keyboard.unhook_all()
    except: pass

def has_camera():
    if not CV_AVAILABLE: return False
    cap = cv2.VideoCapture(0)
    ok  = cap.isOpened()
    cap.release()
    return ok

# ══════════════════════════════════════════════════════════════════
# API  —  DEMO_MODE=True → mock, False → real server
# ══════════════════════════════════════════════════════════════════
_demo_poll_count = 0

def api_post(path, payload):
    if DEMO_MODE: return _mock_post(path)
    body = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{API_BASE}{path}", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def api_get(path):
    if DEMO_MODE: return _mock_get(path)
    with urllib.request.urlopen(f"{API_BASE}{path}", timeout=5) as r:
        raw = r.read()
        try:    return json.loads(raw)
        except: return raw.decode().strip()

def _mock_post(path):
    time.sleep(0.5)
    if "/session/start/"    in path: return {"session_id": "demo-0000"}
    if "/face/agent/check/" in path: return {"status": "verified"}
    return {}

def _mock_get(path):
    global _demo_poll_count
    time.sleep(0.3)
    if "/fingerprint/phone/status/" in path:
        _demo_poll_count += 1
        if _demo_poll_count >= 5:
            _demo_poll_count = 0
            return "completed"
        return "pending"
    return {}


# ══════════════════════════════════════════════════════════════════
# METHOD CARD helper
# ══════════════════════════════════════════════════════════════════
def make_method_card(parent, icon, title, desc, available, on_click, w=190, h=200):
    border_col = BORDER      if available else "#111825"
    bg_col     = CARD_DARK   if available else "#0a1020"
    icon_col   = TEXT        if available else "#2d3748"
    title_col  = TEXT        if available else "#2d3748"
    desc_col   = MUTED       if available else "#1e2937"
    hint_col   = ACCENT      if available else "#1e2937"
    hint_text  = "Click to use →" if available else "Not available"

    outer = tk.Frame(parent, bg=border_col, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg_col, width=w, height=h,
                     cursor="hand2" if available else "")
    inner.pack_propagate(False)
    inner.pack()

    accent_bar = tk.Frame(inner, bg=ACCENT if available else "#111825", height=3)
    accent_bar.pack(fill="x")

    tk.Label(inner, text=icon,  font=("Segoe UI", 28),
             fg=icon_col,  bg=bg_col).pack(pady=(18, 2))
    tk.Label(inner, text=title, font=("Segoe UI", 12, "bold"),
             fg=title_col, bg=bg_col).pack()
    tk.Label(inner, text=desc,  font=("Segoe UI", 9),
             fg=desc_col,  bg=bg_col,
             wraplength=w-24, justify="center").pack(pady=(5, 6))
    tk.Label(inner, text=hint_text, font=("Consolas", 9),
             fg=hint_col,  bg=bg_col).pack()

    if available:
        def _enter(e):
            inner.config(bg="#0d1f3a")
            accent_bar.config(bg="#60a5fa")
            for ch in inner.winfo_children():
                try: ch.config(bg="#0d1f3a")
                except: pass
        def _leave(e):
            inner.config(bg=CARD_DARK)
            accent_bar.config(bg=ACCENT)
            for ch in inner.winfo_children():
                try: ch.config(bg=CARD_DARK)
                except: pass
        for widget in [inner] + list(inner.winfo_children()):
            widget.bind("<Enter>",    _enter)
            widget.bind("<Leave>",    _leave)
            widget.bind("<Button-1>", lambda e: on_click())

    return outer


# ══════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════
class BioLockApp:

    def __init__(self):
        self.windows      = []
        self.taskbar_hwnd = hide_taskbar()
        block_keys()

        self.session_id   = None
        self.camera_ok    = has_camera()
        self._cam_running = False
        self._cap         = None
        self._last_frame  = None
        self.qr_photo     = None
        self._polling     = False
        self._content_frame = None

        self._build_all_windows()
        self.root.mainloop()

    # ── windows ───────────────────────────────────────────────────
    def _build_all_windows(self):
        for i, m in enumerate(_get_monitors()):
            self._create_window(m, primary=(i == 0))

    def _create_window(self, monitor, primary=False):
        win = tk.Tk() if not self.windows else tk.Toplevel()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        win.configure(bg=BG)
        win.lift(); win.focus_force()
        win.bind("<Key>",    lambda e: "break")
        win.bind("<Alt-F4>", lambda e: "break")
        win.bind("<Escape>", lambda e: "break")
        if primary:
            self.root = win
            self.W, self.H = monitor.width, monitor.height
            self._build_shell(win)
        else:
            self._build_blank(win, monitor)
        self.windows.append(win)

    def _build_blank(self, win, m):
        c = tk.Canvas(win, bg=BG, highlightthickness=0)
        c.pack(fill="both", expand=True)
        for x in range(0, m.width, 60):
            for y in range(0, m.height, 60):
                c.create_oval(x-1,y-1,x+1,y+1, fill="#141424", outline="")
        tk.Label(win, text="AD BioGuard", font=("Consolas",13),
                 fg=DIM, bg=BG).place(relx=0.5, rely=0.5, anchor="center")

    # ── shell ────────────────────────────────────────────────────
    def _build_shell(self, win):
        W, H = self.W, self.H
        self.bg_canvas = tk.Canvas(win, bg=BG, highlightthickness=0)
        self.bg_canvas.pack(fill="both", expand=True)

        for x in range(0, W, 60):
            for y in range(0, H, 60):
                self.bg_canvas.create_oval(x-1,y-1,x+1,y+1, fill="#141424", outline="")

        cx, cy = W//2, H//2
        for r, col in [(min(W,H)//3, "#0f172a"), (min(W,H)//3-20, "#090f1a")]:
            self.bg_canvas.create_oval(cx-r,cy-r,cx+r,cy+r, outline=col, width=1)

        CW, CH = 500, 520
        self.CW, self.CH = CW, CH
        self.cx0 = (W - CW) // 2
        self.cy0 = (H - CH) // 2
        cx0, cy0 = self.cx0, self.cy0

        for i in range(10, 0, -1):
            v = f"#{8+i:02x}{8+i:02x}{18+i:02x}"
            self.bg_canvas.create_rectangle(cx0-i,cy0-i,cx0+CW+i,cy0+CH+i, fill=v, outline="")
        self.bg_canvas.create_rectangle(cx0,cy0,cx0+CW,cy0+CH, fill=CARD, outline=BORDER, width=1)
        self.bg_canvas.create_rectangle(cx0,cy0,cx0+CW,cy0+3,  fill=ACCENT, outline="")

        self.bg_canvas.create_text(W//2, cy0+32, text="AD BioGuard",
                                    font=("Consolas",10), fill=ACCENT)
        self.bg_canvas.create_text(W//2, cy0+62, text="Identity Verification",
                                    font=("Segoe UI",19,"bold"), fill=TEXT)
        self.bg_canvas.create_text(W//2, cy0+90, text=f"User: {USERNAME}",
                                    font=("Consolas",11), fill=MUTED)
        self.bg_canvas.create_line(cx0+40,cy0+108, cx0+CW-40,cy0+108, fill=DIM)

        # content area
        content_y = cy0 + 118
        content_h = CH - 118 - 46
        self._content_frame = tk.Frame(win, bg=CARD, width=CW-40, height=content_h)
        self._content_frame.pack_propagate(False)
        self._content_win = self.bg_canvas.create_window(
            W//2, content_y + content_h//2,
            window=self._content_frame, width=CW-40, height=content_h)

        # status
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_lbl = tk.Label(win, textvariable=self.status_var,
                                    font=("Segoe UI",10), fg=MUTED, bg=CARD,
                                    pady=3, padx=12)
        self.bg_canvas.create_window(W//2, cy0+CH-34,
                                      window=self.status_lbl, width=CW-40)

        # bottom strip
        self.bg_canvas.create_rectangle(cx0,cy0+CH-22,cx0+CW,cy0+CH, fill=CARD_DARK, outline="")
        self.bg_canvas.create_text(W//2, cy0+CH-11,
                                    text="Secure biometric authentication  •  AD Security",
                                    font=("Consolas",8), fill=DIM)

        # pulse
        self.pulse_id = self.bg_canvas.create_oval(
            W//2-5, cy0+CH-20, W//2+5, cy0+CH-10, fill="#1e40af", outline="")
        self._pulse_tick()

        # DEV exit
        if DEV_MODE:
            tk.Button(win, text="⏻  EXIT DEV",
                      font=("Consolas",10,"bold"),
                      fg=MUTED, bg=CARD,
                      activeforeground=TEXT, activebackground=BORDER2,
                      bd=0, relief="flat", padx=14, pady=6, cursor="hand2",
                      command=self.close_all).place(x=W-130, y=H-38)

        threading.Thread(target=self._init_session, daemon=True).start()

    def _clear_content(self):
        for w in self._content_frame.winfo_children():
            w.destroy()

    # ── session ───────────────────────────────────────────────────
    def _init_session(self):
        try:
            data = api_post("/api/agent/session/start/", {"username": USERNAME})
            self.session_id = data.get("session_id", "demo-0000")
            self.root.after(0, self._show_method_select)
        except Exception as e:
            self._set_status(f"Server error: {e}. Retrying...", RED)
            time.sleep(8)
            threading.Thread(target=self._init_session, daemon=True).start()

    # ══════════════════════════════════════════════════════════════
    # SCREEN 1 — METHOD SELECTION
    # Foydalanuvchi IKKISIDAN BITTASINI tanlaydi
    # ══════════════════════════════════════════════════════════════
    def _show_method_select(self):
        self._cam_running = False
        self._polling     = False
        self._clear_content()
        f = self._content_frame
        self._set_status("Biometric verification required — choose one method", ACCENT)

        tk.Label(f, text="Choose verification method",
                 font=("Segoe UI",13,"bold"), fg=TEXT, bg=CARD).pack(pady=(18,14))

        row = tk.Frame(f, bg=CARD)
        row.pack()

        # ── Face card ──
        make_method_card(
            row,
            icon="📷",
            title="Face Scan",
            desc="Verify identity\nusing your webcam",
            available=self.camera_ok,
            on_click=self._start_face_flow,
            w=190, h=200
        ).pack(side="left", padx=12)

        # ── Fingerprint card ──
        make_method_card(
            row,
            icon="📱",
            title="Fingerprint",
            desc="Scan QR with phone\nfor fingerprint auth",
            available=True,
            on_click=self._start_finger_flow,
            w=190, h=200
        ).pack(side="left", padx=12)

        if not self.camera_ok:
            tk.Label(f, text="📷 Camera not detected on this device",
                     font=("Consolas", 9), fg="#374151", bg=CARD).pack(pady=(10,0))

    # ══════════════════════════════════════════════════════════════
    # FLOW A — FACE SCAN
    # ══════════════════════════════════════════════════════════════
    def _start_face_flow(self):
        self._clear_content()
        f = self._content_frame
        self._set_status("Position your face in the frame, then press Capture", ACCENT)

        self._cam_label = tk.Label(f, bg="#000000", width=58, height=10)
        self._cam_label.pack(pady=(12, 4))

        tk.Label(f, text="Look directly at the camera",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack()

        btn_row = tk.Frame(f, bg=CARD)
        btn_row.pack(pady=8)

        self._capture_btn = tk.Button(
            btn_row, text="📸  Capture & Verify",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT, bg=ACCENT,
            activeforeground=TEXT, activebackground="#2563eb",
            bd=0, relief="flat", padx=18, pady=7, cursor="hand2",
            command=self._on_capture_clicked)
        self._capture_btn.pack(side="left", padx=6)

        tk.Button(btn_row, text="← Back",
                  font=("Segoe UI", 10),
                  fg=MUTED, bg=CARD_DARK,
                  activeforeground=TEXT, activebackground=BORDER2,
                  bd=0, relief="flat", padx=12, pady=7, cursor="hand2",
                  command=self._show_method_select
                  ).pack(side="left", padx=6)

        self._last_frame  = None
        self._cam_running = True
        threading.Thread(target=self._camera_loop, daemon=True).start()

    def _camera_loop(self):
        cap = cv2.VideoCapture(0)
        self._cap = cap
        while self._cam_running and cap.isOpened():
            ok, frame = cap.read()
            if not ok: break
            frame = cv2.flip(frame, 1)
            self._last_frame = frame
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img   = Image.fromarray(rgb).resize((410, 180))
            photo = ImageTk.PhotoImage(img)
            def _upd(p=photo):
                try:
                    self._cam_label.config(image=p)
                    self._cam_label.image = p
                except: pass
            self.root.after(0, _upd)
            time.sleep(0.033)
        cap.release()

    def _on_capture_clicked(self):
        if self._last_frame is None:
            self._set_status("Camera not ready, please wait...", AMBER)
            return
        self._capture_btn.config(state="disabled", text="Verifying...")
        self._cam_running = False
        threading.Thread(target=self._send_face,
                          args=(self._last_frame,), daemon=True).start()

    def _send_face(self, frame):
        try:
            self._set_status("Verifying face...", AMBER)
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            b64    = base64.b64encode(buf.tobytes()).decode()
            data   = api_post("/api/face/agent/check/",
                               {"session_id": self.session_id,
                                "username": USERNAME, "image": b64})
            status = data.get("status", "")
            if status == "verified":
                self.root.after(0, self._on_verified)
            else:
                msg = data.get("detail", "Face not recognized")
                self.root.after(0, lambda m=msg: self._face_retry(m))
        except Exception as e:
            self.root.after(0, lambda ex=e: self._face_retry(str(ex)))

    def _face_retry(self, reason):
        self._set_status(f"Not recognized: {reason}  —  try again", RED)
        if hasattr(self, "_capture_btn") and self._capture_btn.winfo_exists():
            self._capture_btn.config(state="normal", text="📸  Capture & Verify")
        self._cam_running = True
        threading.Thread(target=self._camera_loop, daemon=True).start()

    # ══════════════════════════════════════════════════════════════
    # FLOW B — FINGERPRINT / QR
    # ══════════════════════════════════════════════════════════════
    def _start_finger_flow(self):
        self._clear_content()
        f = self._content_frame
        self._set_status("Scan the QR code with your phone", ACCENT)

        tk.Label(f, text="📱  Scan with your phone",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=CARD).pack(pady=(12, 8))

        # QR box
        qr_box = tk.Frame(f, bg=CARD_DARK, width=186, height=186,
                           highlightbackground=BORDER, highlightthickness=1)
        qr_box.pack_propagate(False)
        qr_box.pack()

        self._qr_placeholder = tk.Label(
            qr_box, text="Generating...",
            font=("Consolas", 9), fg=MUTED, bg=CARD_DARK)
        self._qr_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._qr_img  = tk.Label(qr_box, bg=CARD_DARK)
        self._qr_info = tk.Label(f,
            text="Open your phone camera and point at the QR code",
            font=("Segoe UI", 9), fg=MUTED, bg=CARD,
            wraplength=380, justify="center")
        self._qr_info.pack(pady=(8, 4))

        btn_row = tk.Frame(f, bg=CARD)
        btn_row.pack(pady=4)

        if DEV_MODE:
            tk.Button(btn_row, text="✓  Simulate (DEV)",
                      font=("Consolas", 9),
                      fg=MUTED, bg=CARD_DARK,
                      activeforeground=TEXT, activebackground=BORDER2,
                      bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                      command=self._on_verified).pack(side="left", padx=6)

        tk.Button(btn_row, text="← Back",
                  font=("Segoe UI", 9),
                  fg=MUTED, bg=CARD_DARK,
                  activeforeground=TEXT, activebackground=BORDER2,
                  bd=0, relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._show_method_select
                  ).pack(side="left", padx=6)

        threading.Thread(target=self._qr_and_poll, daemon=True).start()

    def _qr_and_poll(self):
        qr_url = f"{API_BASE}/mobile/fingerprint/{self.session_id}/"
        self.root.after(0, lambda u=qr_url: self._render_qr(u))
        self._polling = True
        while self._polling:
            try:
                raw    = api_get(f"/api/fingerprint/phone/status/{self.session_id}/")
                status = raw if isinstance(raw, str) else raw.get("status", "")
                if status == "completed":
                    self._polling = False
                    self.root.after(0, self._on_verified)
                    return
                elif status == "expired":
                    self._polling = False
                    self.root.after(0, lambda: self._set_status(
                        "QR expired — go back and retry", AMBER))
                    return
            except: pass
            time.sleep(2)

    def _render_qr(self, url):
        if not QR_AVAILABLE:
            if self._qr_info:
                self._qr_info.config(text=f"Install qrcode+Pillow\n{url}", fg=AMBER)
            return
        try:
            qr = qrcode.QRCode(version=4,
                               error_correction=qrcode.constants.ERROR_CORRECT_M,
                               box_size=4, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#f1f5f9", back_color="#060d1a")
            img = img.resize((182, 182), Image.NEAREST)
            self.qr_photo = ImageTk.PhotoImage(img)
            self._qr_placeholder.place_forget()
            self._qr_img.config(image=self.qr_photo)
            self._qr_img.image = self.qr_photo
            self._qr_img.place(relx=0.5, rely=0.5, anchor="center")
            if self._qr_info:
                self._qr_info.config(text="Waiting for phone scan...", fg=MUTED)
        except Exception as e:
            if self._qr_info:
                self._qr_info.config(text=f"QR error: {e}", fg=RED)

    # ══════════════════════════════════════════════════════════════
    # VERIFIED — either method leads here
    # ══════════════════════════════════════════════════════════════
    def _on_verified(self):
        self._cam_running = False
        self._polling     = False
        self._set_status("✓  Verified — unlocking workstation...", GREEN)
        self._clear_content()
        f = self._content_frame
        tk.Label(f, text="✓",
                 font=("Segoe UI", 52), fg=GREEN, bg=CARD).pack(pady=(38, 6))
        tk.Label(f, text="Identity Verified",
                 font=("Segoe UI", 16, "bold"), fg=TEXT, bg=CARD).pack()
        tk.Label(f, text="Unlocking workstation...",
                 font=("Segoe UI", 10), fg=MUTED, bg=CARD).pack(pady=6)
        self.root.after(1400, self.close_all)

    # ── pulse ─────────────────────────────────────────────────────
    def _pulse_tick(self, step=0):
        if not self.windows or not self.pulse_id: return
        t = step / 30
        b = int(30 + 25 * math.sin(t * math.pi * 2))
        try: self.bg_canvas.itemconfig(self.pulse_id, fill=f"#{b:02x}{b+20:02x}af")
        except: return
        self.root.after(80, lambda: self._pulse_tick((step+1) % 30))

    def _set_status(self, text, color=MUTED):
        if self.status_var: self.status_var.set(text)
        if self.status_lbl: self.status_lbl.config(fg=color)

    # ── close ─────────────────────────────────────────────────────
    def close_all(self):
        self._cam_running = False
        self._polling     = False
        if self._cap:
            try: self._cap.release()
            except: pass
        unblock_keys()
        show_taskbar(self.taskbar_hwnd)
        wins = list(self.windows)
        self.windows.clear()
        for w in wins:
            try: w.destroy()
            except: pass


if __name__ == "__main__":
    BioLockApp()