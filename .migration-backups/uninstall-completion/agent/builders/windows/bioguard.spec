# -*- mode: python ; coding: utf-8 -*-
# AD BioGuard — PyInstaller spec

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

a = Analysis(
    [str(PROJECT_ROOT / 'main.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=collect_dynamic_libs('webview'),
    datas=[
        (str(PROJECT_ROOT / 'ui/index.html'),   'ui'),
        (str(PROJECT_ROOT / 'ui/overlay.html'), 'ui'),
        (str(PROJECT_ROOT / 'ui/style.css'),    'ui'),
        (str(PROJECT_ROOT / 'ui/theme.css'),    'ui'),
        (str(PROJECT_ROOT / 'ui/app.js'),       'ui'),
        (str(PROJECT_ROOT / 'ui/qrcode.min.js'),'ui'),
        *collect_data_files('webview'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.winforms',
        'clr',
        'win32gui',
        'win32ts',
        'win32con',
        'win32api',
        'pywintypes',
        'keyboard',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BioGuard',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=False,
    icon=str(PROJECT_ROOT / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='BioGuard',
)
