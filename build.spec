# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 自動收集靜態資源與模型配置
datas = (
    collect_data_files('customtkinter') +
    collect_data_files('df') +
    collect_data_files('torchaudio')
)

# 確保所有深層隱含依賴完整引入
hiddenimports = [
    'df',
    'pedalboard',
    'customtkinter',
    'tkinterdnd2',
    'soundfile',
    'numpy',
    'torch',
    'torchaudio',
    'torchaudio.backend',
    'torchaudio.backend.soundfile_backend',
    'torchaudio.backend.sox_io_backend',
] + collect_submodules('df') + collect_submodules('torchaudio')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VoiceClarityStudio',
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
