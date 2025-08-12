# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['WatcherGUI.py', 'Watcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ASSETS/*', 'ASSETS/'),
        ('CONFIGS/*', 'CONFIGS/'),
        ('UTILS/*', 'UTILS/'),
        ('WEBSITES/*', 'WEBSITES/'),
        ('Watcher.py', '.'),
        ('requirements.txt', '.'),
        ('downloaded_files', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FG-ToolWatcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ASSETS/FG-TWico.ico',
)
