# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

datas = [('LICENSE', '.'), ('assets', 'assets')]
datas += copy_metadata('pymobiledevice3')
name = 'TetherPin'
identity_dir = os.environ.get('TETHERPIN_IDENTITY_DIR')
if identity_dir:
    identity = Path(identity_dir).resolve(strict=True)
    for filename in ('certificate.p7b', 'identity.pk8'):
        credential = identity / filename
        if not credential.is_file() or not 0 < credential.stat().st_size <= 16 * 1024:
            raise ValueError(f'Missing or invalid identity file: {filename}')
        datas.append((str(credential), 'bundled_identity'))
    name = 'TetherPin-Offline'


a = Analysis(
    ['tools\\portable_gui.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas', 'numpy', 'jedi', 'parso'],
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
    name=name,
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
)
