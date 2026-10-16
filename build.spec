# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 自動收集 customtkinter 與 deepfilternet 所需的靜態資源檔
datas = collect_data_files('customtkinter') + collect_data_files('df')

# 確保所有深層隱含的依賴模組都被正確引入
hiddenimports = [
    'df',
    'pedalboard',
    'customtkinter',
    'tkinterdnd2',
    'soundfile',
    'numpy',
    'torch'
] + collect_submodules('df')

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
    console=False,                  # 設為 False 避免啟動時跳出黑色終端機命令視窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
