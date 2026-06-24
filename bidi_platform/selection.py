"""Read primary selection from X11 or Wayland."""

from __future__ import annotations

import shutil
import subprocess

from bidi_platform.session import is_wayland


def _run_reader(args: list[str]) -> str:
    try:
        raw = subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=2)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""
    return raw.decode("utf-8", errors="replace").strip()


def get_selected_text() -> str:
    """Read highlighted text from the primary selection."""
    if is_wayland():
        return _run_reader(["wl-paste", "--primary"])
    return _run_reader(["xclip", "-o", "-selection", "primary"])


def missing_dependencies() -> list[str]:
    """Return apt-style package names that appear to be missing."""
    if is_wayland():
        if not shutil.which("wl-paste"):
            return ["wl-clipboard"]
        return []

    if not shutil.which("xclip"):
        return ["xclip"]
    return []
