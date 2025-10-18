# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the flet_desktop package path
flet_desktop_path = Path(sys.modules['flet_desktop'].__file__).parent if 'flet_desktop' in sys.modules else None
if not flet_desktop_path:
    import importlib.util
    spec = importlib.util.find_spec('flet_desktop')
    if spec:
        flet_desktop_path = Path(spec.origin).parent

# Add Flet runtime files
flet_runtime = []
if flet_desktop_path and (flet_desktop_path / 'app' / 'flet').exists():
    flet_runtime_dir = flet_desktop_path / 'app' / 'flet'
    flet_runtime = [(str(flet_runtime_dir), 'flet_desktop/app/flet')]

a = Analysis(
    ['app_flet_restored.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'), 
        ('core', 'core'), 
        ('docs', 'docs'), 
        ('manifests', 'manifests'), 
        ('chunks', 'chunks')
    ] + flet_runtime,
    hiddenimports=['flet', 'flet_desktop', 'flet.fastapi'],
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
    [],
    exclude_binaries=True,
    name='MultiDriveCloudManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MultiDriveCloudManager',
)
