from pathlib import Path
PROJECT_ROOT=Path(SPECPATH).resolve().parents[1]
a=Analysis([str(PROJECT_ROOT/'platform_adapters/windows/supervisor_service.py')],pathex=[str(PROJECT_ROOT)],binaries=[],datas=[],
    hiddenimports=['servicemanager','win32service','win32serviceutil','win32security','win32process','win32profile','win32ts',
        'win32api','win32con','win32event','pywintypes','win32com.shell.shell','win32com.shell.shellcon'],
    excludes=['webview','cv2','tensorflow','deepface'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='BioGuardSupervisor',console=False,uac_admin=False,upx=False)
