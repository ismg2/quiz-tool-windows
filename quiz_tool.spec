# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Quiz Tool
Builds a single .exe with all dependencies bundled
"""

import os

block_cipher = None

# Get the directory where spec file is located
SPEC_DIR = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    ['app_standalone.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('quizzes', 'quizzes'),
    ],
    hiddenimports=[
        'flask',
        'jinja2',
        'werkzeug',
        'markupsafe',
        'itsdangerous',
        'click',
        'blinker',
        'cryptography',
        'waitress',
    ],
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
    name='QuizTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)
