# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Automatically detect optional files to bundle
binaries = []
if os.path.exists('ffmpeg.exe'):
    binaries.append(('ffmpeg.exe', '.'))
if os.path.exists('ffprobe.exe'):
    binaries.append(('ffprobe.exe', '.'))

datas = []
if os.path.exists('me.jpg'):
    datas.append(('me.jpg', '.'))
if os.path.exists('settings.json'):
    datas.append(('settings.json', '.'))

# Determine icon
icon_file = None
if os.path.exists('icon.ico'):
    icon_file = 'icon.ico'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['yt_dlp', 'PyQt5'],
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
    [],
    exclude_binaries=True,
    name='UltimateMediaDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Hides the console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UltimateMediaDownloader',
)
