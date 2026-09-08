# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / "src" / "macsucks" / "main.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "src" / "macsucks" / "assets" / "test_ocr.png"), "macsucks/assets"),
        (str(root / "src" / "macsucks" / "assets" / "app.ico"), "macsucks/assets"),
        (str(root / "src" / "macsucks" / "assets" / "processing.gif"), "macsucks/assets"),
        (str(root / "src" / "macsucks" / "assets" / "mascot.gif"), "macsucks/assets"),
        (str(root / "src" / "macsucks" / "assets" / "success.gif"), "macsucks/assets"),
        (str(root / "src" / "macsucks" / "assets" / "error.gif"), "macsucks/assets"),
    ],
    hiddenimports=[
        "macsucks",
        "macsucks.app_controller",
        "macsucks.main",
        "macsucks.assets_util",
        "keyring.backends.Windows",
        "keyboard",
        "mss",
        "PIL",
        "llama_cloud",
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
    name="MacSucks",
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
    icon=str(root / "src" / "macsucks" / "assets" / "app.ico"),
)
