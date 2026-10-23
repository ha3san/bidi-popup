# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows builds (run on windows-latest CI).

from pathlib import Path

block_cipher = None
# SPECPATH is the directory that contains this .spec file (packaging/).
root = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(root / "listener.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "assets" / "icon.svg"), "assets"),
        (str(root / "assets" / "icon.ico"), "assets"),
    ],
    hiddenimports=[
        "bidi_platform.hotkey_win",
        "bidi_platform.selection_win",
        "bidi_platform.autostart_win",
        "settings_dialog",
        "popup",
        "theme",
        "layout_utils",
        "app_settings",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "uiautomation",
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
    [],
    exclude_binaries=True,
    name="BidiPopup",
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
    icon=str(root / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BidiPopup",
)
