"""Read primary selection (Linux) or highlighted text (Windows)."""

from __future__ import annotations

import shutil
import subprocess

from bidi_platform.session import is_wayland, is_windows


def _run_reader(args: list[str]) -> str:
    try:
        raw = subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=2)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""
    return raw.decode("utf-8", errors="replace").strip()


def get_selected_text() -> str:
    """Read highlighted text from the primary selection (or Windows clipboard dance)."""
    if is_windows():
        from bidi_platform.selection_win import get_selected_text_windows

        return get_selected_text_windows()

    # --- Linux paths below: keep identical to previous behavior ---
    if is_wayland():
        return _run_reader(["wl-paste", "--primary"])
    return _run_reader(["xclip", "-o", "-selection", "primary"])


def missing_dependencies() -> list[str]:
    """Return apt-style package names that appear to be missing (Linux only)."""
    if is_windows():
        return []

    if is_wayland():
        if not shutil.which("wl-paste"):
            return ["wl-clipboard"]
        return []

    if not shutil.which("xclip"):
        return ["xclip"]
    return []
