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

# Define data files to include
added_files = [
    ('assets/*', 'assets'),  # Include all assets
    ('data/*.json', 'data'), # Include existing JSON data files
    ('version_info.json', '.'), # Include version info in root
]

# Hidden imports for PyQt5 and qfluentwidgets
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtSvg',
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
]

a = Analysis(
    ['autolauncher.py'],
    pathex=[],
    binaries=[],
    datas=added_files + qfluentwidgets_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PyQt6', 'PySide2', 'tkinter'],
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
