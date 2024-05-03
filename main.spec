# -*- mode: python ; coding: utf-8 -*-
from pylibdmtx import pylibdmtx
from pathlib import Path


a = Analysis(
    ['C:\\Users\\HomutinnikovaII\\PycharmProjects\\DMPrintInterfaceRefactor\\project\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pylibdmtx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

a.binaries += TOC([
    (Path(dep._name).name, dep._name, 'BINARY')
    for dep in pylibdmtx.EXTERNAL_DEPENDENCIES
])

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
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
