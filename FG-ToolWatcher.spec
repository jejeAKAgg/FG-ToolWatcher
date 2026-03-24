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
        
        # Secrets data
        (str(ROOT / '__SECRETS'), '/__SECRETS'),
        
        # Assets GUI (icônes, i18n, widgets)
        (str(ROOT / 'GUI' / '__ASSETS' / 'icons'), 'GUI/__ASSETS/icons'),
        (str(ROOT / 'GUI' / '__ASSETS' / 'i18n'), 'GUI/__ASSETS/i18n'),

        # Resources CORE (brands.json, websites.json)
        (str(ROOT / 'CORE' / '__RESOURCES'), 'CORE/__RESOURCES'),
    ],

    # Imports
    hiddenimports=[
        'cloudscraper',
        'cloudscraper.interpreters',
        'thefuzz',
        'thefuzz.fuzz',
        'thefuzz.process',
        'Levenshtein',
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
#   EXE
# =====================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='FG-ToolWatcher',
    icon=str(ROOT / 'GUI' / '__ASSETS' / 'icons' / 'FG-TWicoBG.ico'),

    # --- Behaviour ---
    console=False,       # no console
    onefile=True,        # only one .exe

    # --- Optimization ---
    strip=False,
    upx=True,            # compress the binary (UPX needed)
    upx_exclude=[],

    # --- WINDOWS metadata ---
    version_file=None,   # optionnel : fichier version_info.txt
    uac_admin=False,     # no admin rights
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
