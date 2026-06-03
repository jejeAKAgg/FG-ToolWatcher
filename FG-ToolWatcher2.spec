# FG-ToolWatcher.spec
# =====================================================
# PyInstaller build spec for FG-ToolWatcher
#
# Usage:
#   pyinstaller FG-ToolWatcher.spec
#
# Output:
#   dist/FG-ToolWatcher/FG-ToolWatcher.exe
# =====================================================

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

block_cipher = None


# =====================================================
#   ANALYSIS
# =====================================================

a = Analysis(
    [str(ROOT / 'Launcher.py')],

    pathex=[str(ROOT)],

    binaries=[],

    datas=[

        # Assets GUI (icônes, i18n, widgets)
        (str(ROOT / 'GUI' / '__ASSETS' / 'icons'), 'GUI/__ASSETS/icons'),
        (str(ROOT / 'GUI' / '__ASSETS' / 'i18n'), 'GUI/__ASSETS/i18n'),

        # Resources CORE (brands.json, websites.json)
        (str(ROOT / 'CORE' / '__RESOURCES'), 'CORE/__RESOURCES'),

        # WEB viewer
        (str(ROOT / 'WEB' / 'viewer.html'), 'WEB'),
        (str(ROOT / 'WEB' / 'assets'), 'WEB/assets'),
    ],

    hiddenimports=[
        'cloudscraper',
        'cloudscraper.interpreters',
        'bs4',
        'lxml',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'pandas',
        'requests',
        'PySide6.QtSvg',
        'PySide6.QtPrintSupport',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'notebook',
        'IPython',
        'thefuzz',
        'Levenshtein',
        'PyQt5',
        'PyQt6',
        'wx',
        'gi',
        'test',
        'unittest',
        'pydoc',
        'doctest',
        'pdb',
        'profile',
        'cProfile',
        'difflib',
        'ftplib',
        'imaplib',
        'poplib',
        'telnetlib',
        'xmlrpc',
    ],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


# =====================================================
#   PYZ
# =====================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)


# =====================================================
#   EXE  (onedir — pas d'extraction au démarrage)
# =====================================================

exe = EXE(
    pyz,
    a.scripts,

    name='FG-ToolWatcher',
    icon=str(ROOT / 'GUI' / '__ASSETS' / 'icons' / 'FG-TWicoBG.ico'),

    # --- Behaviour ---
    console=False,
    onefile=False,

    # --- Optimization ---
    strip=True,
    upx=True,
    upx_exclude=[
        'python*.dll',
        'Qt6*.dll',
        'PySide6/*.pyd',
    ],

    # --- Windows metadata ---
    version_file=None,
    uac_admin=False,
    uac_uiaccess=False,

    # --- Debug ---
    debug=False,
    bootloader_ignore_signals=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    runtime_tmpdir=None,
)


# =====================================================
#   COLLECT  (requis pour onedir)
# =====================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[
        'python*.dll',
        'Qt6*.dll',
        'PySide6/*.pyd',
    ],
    name='FG-ToolWatcher',
)
