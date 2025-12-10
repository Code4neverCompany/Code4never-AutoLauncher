# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Autolauncher
Builds a standalone Windows executable with all dependencies and assets bundled.
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all qfluentwidgets data files
qfluentwidgets_datas = collect_data_files('qfluentwidgets')

# Build explicit list of data files as TOC tuples (source, dest)
import glob
added_files = []

# Add version_info.json to root of application
added_files.append(('version_info.json', '.'))

# Add all assets - use explicit file paths
for asset_file in glob.glob('assets/**/*', recursive=True):
    if os.path.isfile(asset_file):
        # Source path, destination directory
        added_files.append((asset_file, os.path.dirname(asset_file)))

# Add all translation files
for translation_file in glob.glob('translations/**/*', recursive=True):
    if os.path.isfile(translation_file):
        # Source path, destination directory
        added_files.append((translation_file, os.path.dirname(translation_file)))

# NOTE: data/*.json files are NO LONGER bundled - user data now stored in AppData
# The app will create tasks.json and settings.json in %APPDATA%\c4n-AutoLauncher\ on first run

# Combine all data files  
all_datas = added_files + qfluentwidgets_datas

# Hidden imports for PyQt5 and qfluentwidgets
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'requests',
    'qfluentwidgets',
    'qfluentwidgets.components',
    'qfluentwidgets.common',
    'qfluentwidgets.window',
    'APScheduler',
    'apscheduler',
    'apscheduler.schedulers',
    'apscheduler.schedulers.background',
    'apscheduler.triggers',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.date',
    'apscheduler.triggers.interval',
    'pywinauto',
    'pywinauto.application',
    'pywinauto.backend',
    'pywinauto.backends.uia',
    'comtypes',
    'comtypes.client',
    'comtypes.gen',
    'six',
    'uuid',
]

a = Analysis(
    ['autolauncher.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PyQt5', 'PySide2', 'tkinter'],
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
    name='Autolauncher',
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
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Autolauncher',
)
