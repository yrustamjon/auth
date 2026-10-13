# Standalone SCM service. Build separately from the interactive agent.
from pathlib import Path
PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
a = Analysis(
    [str(PROJECT_ROOT / 'platform_adapters/windows/service_entry.py')],
    pathex=[str(PROJECT_ROOT)], binaries=[], datas=[],
    hiddenimports=['servicemanager', 'win32service', 'win32serviceutil',
                   'win32security', 'win32pipe', 'win32file', 'win32event',
                   'win32api', 'win32con', 'win32ts', 'pywintypes',
                   'win32com.shell.shell', 'win32com.shell.shellcon'],
    excludes=['webview', 'cv2', 'keyboard'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='BioGuardService',
          console=True, debug=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='BioGuardService', strip=False, upx=False)
