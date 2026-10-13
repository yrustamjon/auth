from pathlib import Path
PROJECT_ROOT=Path(SPECPATH).resolve().parents[1]
a=Analysis([str(PROJECT_ROOT/'platform_adapters/windows/watchdog_entry.py')],pathex=[str(PROJECT_ROOT)],binaries=[],datas=[],
    hiddenimports=['win32api','win32con','win32security','win32process','win32event','pywintypes'],
    excludes=['webview','cv2','tensorflow','deepface'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='BioGuardWatchdog',console=False,uac_admin=False,upx=False)
