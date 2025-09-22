# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['WatcherGUI.py', 'Watcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('APP/*', 'APP/'),
        ('APP/ASSETS/*', 'APP/ASSETS/'),
        ('APP/CONFIGS/*', 'APP/CONFIGS/'),
        ('APP/LAYOUTS/*, 'APP/LAYOUTS/'),
        ('APP/PAGES/*', 'APP/PAGES/'),
        ('APP/SERVICES/*', 'APP/SERVICES/'),
        ('APP/UTILS/*', 'APP/UTILS/'),
        ('APP/WEBSITES/*', 'APP/WEBSITES/'),
        ('APP/WIDGETS/*', 'APP/WIDGETS/'),
        ('Watcher.py', '.'),
        ('WatcherGUI.py', '.')
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
