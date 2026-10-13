# Standalone one-file lifecycle helper; deliberately excludes biometric UI stacks.
from pathlib import Path
PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
a = Analysis([str(PROJECT_ROOT / 'app/lifecycle_entry.py')], pathex=[str(PROJECT_ROOT)],
    binaries=[], datas=[], hiddenimports=['win32api', 'win32con', 'win32file', 'win32pipe',
        'win32process', 'win32profile', 'win32security', 'pywintypes', 'tkinter'],
    hookspath=[], runtime_hooks=[], excludes=['webview', 'cv2', 'tensorflow', 'deepface'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='BioGuardLifecycle',
    debug=False, strip=False, upx=False, console=False, uac_admin=False)
