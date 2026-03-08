# -*- mode: python ; coding: utf-8 -*-
"""
PassiveGuard PyInstaller Spec File
==================================
Creates a single executable that bundles:
- FastAPI backend
- ML model (XGBoost)
- Demo HTML frontend
- All dependencies

Build command: pyinstaller passiveguard.spec
"""

import os
import sys
from pathlib import Path

# Paths - use absolute paths to avoid resolution issues
# SPECPATH is defined by PyInstaller and points to the spec file location
_spec_file = SPECPATH if 'SPECPATH' in dir() else __file__
SPEC_DIR = os.path.dirname(os.path.abspath(_spec_file))

# Walk up to find project root (directory containing 'backend' folder)
PROJECT_ROOT = SPEC_DIR
for _ in range(5):  # Max 5 levels up
    if os.path.isdir(os.path.join(PROJECT_ROOT, 'backend')):
        break
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
DEMO_DIR = os.path.join(PROJECT_ROOT, 'demo')
MODELS_DIR = os.path.join(BACKEND_DIR, 'models')
STANDALONE_DIR = SPEC_DIR

# Debug: Print paths during build
print(f"[SPEC] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[SPEC] BACKEND_DIR: {BACKEND_DIR}")
print(f"[SPEC] MODELS_DIR: {MODELS_DIR}")

# Determine platform-specific settings
if sys.platform == 'darwin':
    # macOS
    icon_file = None  # Use .icns file if available
    console = False
elif sys.platform == 'win32':
    # Windows
    icon_file = None  # Use .ico file if available
    console = False
else:
    # Linux
    icon_file = None
    console = True

# Analysis - collect all dependencies
a = Analysis(
    ['passiveguard_app.py'],
    pathex=[STANDALONE_DIR, BACKEND_DIR],
    binaries=[],
    datas=[
        # ML Models
        (os.path.join(MODELS_DIR, 'bot_detector.joblib'), 'models'),
        (os.path.join(MODELS_DIR, 'feature_importance.json'), 'models'),
        # Demo HTML
        (os.path.join(DEMO_DIR, 'index.html'), 'static'),
    ],
    hiddenimports=[
        # FastAPI & Starlette
        'fastapi',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.responses',
        'starlette.staticfiles',
        'starlette.templating',
        
        # Uvicorn
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        
        # ML Libraries
        'sklearn',
        'sklearn.ensemble',
        'sklearn.tree',
        'sklearn.utils',
        'sklearn.utils._typedefs',
        'sklearn.utils._heap',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
        'sklearn.neighbors._partition_nodes',
        'xgboost',
        'xgboost.core',
        'xgboost.sklearn',
        'joblib',
        'numpy',
        'scipy',
        'scipy.special',
        'scipy.special._ufuncs',
        
        # Async
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'httptools',
        'watchfiles',
        'websockets',
        
        # Other
        'email.mime.text',
        'email.mime.multipart',
        'encodings',
        'json',
        'hashlib',
        'webbrowser',
        'threading',
        'socket',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate binaries/data
def remove_duplicates(items):
    seen = set()
    result = []
    for item in items:
        key = item[0] if isinstance(item, tuple) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

a.binaries = remove_duplicates(a.binaries)
a.datas = remove_duplicates(a.datas)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PassiveGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# For macOS, also create .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='PassiveGuard.app',
        icon=icon_file,
        bundle_identifier='com.passiveguard.app',
        info_plist={
            'CFBundleName': 'PassiveGuard',
            'CFBundleDisplayName': 'PassiveGuard',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSBackgroundOnly': False,
        },
    )
