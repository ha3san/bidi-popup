"""Windows Startup-folder autostart helpers (no effect on Linux)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SHORTCUT_NAME = "Bidi Popup.lnk"
BAT_NAME = "Bidi Popup.cmd"


def _startup_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise OSError("APPDATA is not set")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    root = Path(__file__).resolve().parent.parent
    python = sys.executable
    listener = root / "listener.py"
    return f'"{python}" "{listener}"'


def _bat_path() -> Path:
    return _startup_dir() / BAT_NAME


def _lnk_path() -> Path:
    return _startup_dir() / SHORTCUT_NAME


def is_autostart_enabled() -> bool:
    try:
        return _bat_path().is_file() or _lnk_path().is_file()
    except OSError:
        return False


def enable_autostart() -> None:
    startup = _startup_dir()
    startup.mkdir(parents=True, exist_ok=True)
    # .cmd avoids needing pywin32 to create a .lnk
    _bat_path().write_text(
        "@echo off\r\n"
        f"start \"\" {_launch_command()}\r\n",
        encoding="utf-8",
    )


def disable_autostart() -> None:
    for path in (_bat_path(), _lnk_path()):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def toggle_autostart() -> bool:
    """Enable or disable; return True if enabled afterwards."""
    if is_autostart_enabled():
        disable_autostart()
        return False
    enable_autostart()
    return True
