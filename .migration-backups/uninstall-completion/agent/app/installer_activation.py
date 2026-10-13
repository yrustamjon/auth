"""Interactive provisioning launched by Setup before the normal agent starts.

Secrets stay in this process: neither command arguments nor temporary files
carry the organization token. Uses the same user context and certificate store
as the subsequent agent launch.
"""
import queue
import threading


def provision(token, activate=None):
    if activate is None:
        from core.activation import activate_org
        activate = activate_org
    token = token.strip()
    if not token:
        raise ValueError('Org tokenni kiriting.')
    return activate(token)


def run():
    import tkinter as tk
    from tkinter import messagebox
    from core.cert import is_activated

    if is_activated():
        return
    root = tk.Tk()
    root.title('AD BioGuard — o‘rnatish: org token')
    root.geometry('510x260')
    root.resizable(False, False)
    results = queue.Queue()
    busy = False
    tk.Label(root, text='Org tokenni kiriting yoki Ctrl+V bilan joylashtiring.',
             wraplength=470).pack(pady=(20, 10))
    entry = tk.Entry(root, show='*', width=52)
    entry.pack(padx=20)
    entry.focus_set()
    status = tk.StringVar(value='PC ma’lumotlari va keylar avtomatik yaratiladi.')
    tk.Label(root, textvariable=status, wraplength=470).pack(pady=15)

    def close():
        if busy and not messagebox.askyesno(
                'Bekor qilish', 'So‘rov yuborilgan. Server uni yakunlagan bo‘lishi mumkin. '
                'Aktivatsiya oynasini yopasizmi?', parent=root):
            return
        entry.delete(0, tk.END)
        root.destroy()

    def submit():
        nonlocal busy
        token = entry.get().strip()
        if not token:
            status.set('Org tokenni kiriting.')
            return
        busy = True
        entry.delete(0, tk.END)
        entry.configure(state='disabled')
        button.configure(state='disabled')
        status.set('Keylar yaratilmoqda va serverda aktivatsiya qilinmoqda…')

        def worker():
            try:
                provision(token)
                results.put(None)
            except Exception as error:
                from core.activation import ActivationError
                # Unexpected failures must not display payloads or secrets.
                results.put(str(error).replace(token, '[token]') if isinstance(error, ActivationError)
                            else 'Aktivatsiya bajarilmadi. Qayta urinib ko‘ring.')
        # Finish an already submitted request even if the window is closed:
        # otherwise the server could consume a token before we persist its key.
        threading.Thread(target=worker, daemon=False).start()

    def poll():
        nonlocal busy
        try:
            error = results.get_nowait()
        except queue.Empty:
            root.after(100, poll)
            return
        busy = False
        if error is None:
            root.destroy()
            return
        status.set(error)
        entry.configure(state='normal')
        button.configure(state='normal')
        entry.focus_set()
        root.after(100, poll)

    button = tk.Button(root, text='Aktivatsiya qilish', command=submit)
    button.pack()
    tk.Button(root, text='Bekor qilish', command=close).pack(pady=8)
    root.protocol('WM_DELETE_WINDOW', close)
    root.after(100, poll)
    root.mainloop()
