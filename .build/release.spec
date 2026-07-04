# .build/release.spec
# =====================================================
# PyInstaller release build spec for FG-ToolWatcher
# [MADE WITH THE HELP OF GEMINI 3.1 PRO MODEL]
# =====================================================

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent

block_cipher = None

# =====================================================
#   ANALYSIS
# =====================================================

a = Analysis(
    [str(ROOT / 'Launcher.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Assets GUI (icônes, i18n)
        (str(ROOT / 'GUI' / '__ASSETS' / 'icons'), 'GUI/__ASSETS/icons'),
        (str(ROOT / 'GUI' / '__ASSETS' / 'i18n'), 'GUI/__ASSETS/i18n'),

        # Resources CORE (brands.json, websites.json)
        (str(ROOT / 'CORE' / '__RESOURCES'), 'CORE/__RESOURCES'),

        # WEB viewer
        (str(ROOT / 'WEB' / 'viewer.html'), 'WEB'),
        (str(ROOT / 'WEB' / 'assets'), 'WEB/assets'),
    ],

    # === IMPORTS CACHÉS ===
    # Forcer l'inclusion de dépendances qui pourraient être ignorées
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
        'PyQt6.QtSvg',
        'PyQt6.QtPrintSupport',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # === EXCLUSIONS MASSIVES ===
    # Allège considérablement le poids final de l'application
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'notebook',
        'IPython',
        'thefuzz',
        'Levenshtein',
        'PySide6', # Exclusion de PySide6 au profit de PyQt6
        'PyQt5',
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
#   EXE (Exécutable lanceur)
# =====================================================

exe = EXE(
    pyz,
    a.scripts,
    name='FG-ToolWatcher',
    icon=str(ROOT / 'GUI' / '__ASSETS' / 'icons' / 'FG-TWicoBG.ico'),

    # --- Comportement ---
    console=False,   # Cache le terminal noir en arrière-plan
    onefile=False,   # Indispensable pour la vitesse : utilise le mode dossier

    # --- Windows metadata ---
    uac_admin=False,
    uac_uiaccess=False,
)

# =====================================================
#   COLLECT (Génération du dossier final)
# =====================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True, # Retire les symboles de debug pour réduire la taille
    upx=True,   # Compresse les binaires (Nécessite UPX installé sur ta machine)
    upx_exclude=[
        'python*.dll',
        'Qt6*.dll',
        'PyQt6/*.pyd',
    ],
    name='FG-ToolWatcher',
)