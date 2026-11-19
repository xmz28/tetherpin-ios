# -*- mode: python ; coding: utf-8 -*-
import os
import tomllib
from importlib.metadata import distributions
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable,
    VarFileInfo, VarStruct, VSVersionInfo,
)

version = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version']
version_tuple = tuple(int(part) for part in version.split('.')) + (0,)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=version_tuple, prodvers=version_tuple,
                     mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
    kids=[
        StringFileInfo([StringTable('040904B0', [
            StringStruct('CompanyName', 'xmz28'),
            StringStruct('FileDescription', 'TetherPin iPhone USB Location'),
            StringStruct('FileVersion', version),
            StringStruct('ProductName', 'TetherPin'),
            StringStruct('ProductVersion', version),
            StringStruct('OriginalFilename', 'TetherPin.exe'),
        ])]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])]),
    ],
)

datas = [('LICENSE', '.'), ('assets', 'assets'), ('THIRD_PARTY_NOTICES.md', '.')]
datas += copy_metadata('pymobiledevice3')
for distribution in distributions():
    for entry in distribution.files or ():
        if '.dist-info' in str(entry) and any(
            token in str(entry).lower() for token in ('license', 'copying', 'notice')
        ):
            source = Path(distribution.locate_file(entry))
            if source.is_file():
                destination = Path('third_party_licenses') / Path(entry).parent
                datas.append((str(source), str(destination)))

name = 'TetherPin'
identity_dir = os.environ.get('TETHERPIN_IDENTITY_DIR') or (
    Path(os.environ['LOCALAPPDATA']) / 'iap2-location-bridge-windows' / 'identity'
)
identity = Path(identity_dir).resolve(strict=True)
for filename in ('certificate.p7b', 'identity.pk8'):
    credential = identity / filename
    if not credential.is_file() or not 0 < credential.stat().st_size <= 16 * 1024:
        raise ValueError(f'Missing or invalid identity file: {filename}')
    datas.append((str(credential), 'bundled_identity'))



a = Analysis(
    ['tools\\portable_gui.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=['build_hooks'],
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
    version=version_info,
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
