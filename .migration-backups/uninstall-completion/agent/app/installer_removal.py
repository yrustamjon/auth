"""User-facing recovery after an interrupted online removal."""
import queue
import threading


def run():
    import tkinter as tk
    from core.config import API_BASE, DEVICE_UUID
    from core.network.client import BioGuardApiClient
    from services.removal import RemovalController
    from platform_adapters.windows.lifecycle import ProtectedReceipt, cleanup_user_credentials, is_elevated
    if is_elevated():
        raise OSError('Open recovery from the installed user desktop')
    store = ProtectedReceipt()
    receipt = store.load()
    if not receipt:
        return 0
    controller = RemovalController(BioGuardApiClient(API_BASE), DEVICE_UUID, store,
        lambda: cleanup_user_credentials(receipt['install_path']))
    root = tk.Tk()
    root.title('AD BioGuard — o‘chirishni yakunlash')
    root.geometry('550x220')
    status = tk.StringVar(value='O‘chirish yakunlanmagan. Internetga ulanib davom eting. Agar dastur fayllari qolgan bo‘lsa, avval uninstallerni qayta oching.')
    tk.Label(root, textvariable=status, wraplength=510).pack(padx=20, pady=25)
    results = queue.Queue()
    busy = False
    closed = False
    def close():
        nonlocal closed
        closed = True
        root.destroy()
    def submit():
        nonlocal busy
        busy = True
        button.configure(state='disabled')
        status.set('Serverdagi ruxsat tekshirilmoqda…')
        def worker():
            try:
                controller.cleanup_and_complete()
                results.put(True)
            except Exception:
                results.put(False)
        threading.Thread(target=worker, daemon=False).start()
    def poll():
        nonlocal busy
        if closed:
            return
        try:
            success = results.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        busy = False
        if success:
            status.set('Agent o‘chirildi. Qurilma joyi bo‘shatildi.')
            button.configure(text='Yakunlash', state='normal', command=close)
        else:
            status.set('Yakunlanmadi. Internet va qolgan dastur fayllarini tekshirib qayta urinib ko‘ring.')
            button.configure(state='normal')
        root.after(100, poll)
    button = tk.Button(root, text='Davom ettirish', command=submit)
    button.pack()
    tk.Button(root, text='Yopish', command=close).pack(pady=8)
    root.protocol('WM_DELETE_WINDOW', close)
    root.after(100, poll)
    root.mainloop()
    return 0
