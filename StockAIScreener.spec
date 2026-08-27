# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Stock AI Screener
# Run on Windows: pyinstaller StockAIScreener.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Include data folder (cache, models, db will be created at runtime)
        ('data/cache', 'data/cache'),
        ('data/models', 'data/models'),
        # Include .env.example so user can configure on first run
        ('.env.example', '.'),
    ],
    hiddenimports=[
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtCharts',
        # pyqtgraph
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        # scikit-learn internals
        'sklearn.utils._cython_blas',
        'sklearn.neighbors._partition_nodes',
        'sklearn.tree._utils',
        'sklearn.ensemble._gb_losses',
        # joblib
        'joblib',
        # scipy
        'scipy.special._cython_special',
        'scipy.linalg.cython_blas',
        'scipy.linalg.cython_lapack',
        # project modules
        'app.broker',
        'app.broker.fyers_client',
        'app.broker.mock_client',
        'app.broker.angel_client',
        'app.market',
        'app.market.tick_processor',
        'app.market.symbol_manager',
        'app.market.state',
        'app.database',
        'app.indicators',
        'app.signals',
        'app.screening',
        'app.etq',
        'app.ml',
        'app.services',
        'app.utils',
        'dashboard',
        'dashboard.main_window',
        'dashboard.stock_table',
        'dashboard.signal_panel',
        'dashboard.trade_panel',
        'dashboard.ml_panel',
        'dashboard.charts',
        'dashboard.config_dialog',
        # other deps
        'fyers_apiv3',
        'websocket',
        'dotenv',
        'requests',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'matplotlib',
        'IPython',
        'notebook',
    ],
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
    name='StockAIScreener',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No black terminal window — GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add icon path here e.g. 'assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockAIScreener',
)
