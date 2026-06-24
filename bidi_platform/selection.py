"""Read selected text from X11 or Wayland clipboard APIs."""

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
    """Primary selection first, then clipboard."""
    if is_wayland():
        readers = (
            ["wl-paste", "--primary"],
            ["wl-paste"],
        )
    else:
        readers = (
            ["xclip", "-o", "-selection", "primary"],
            ["xclip", "-o", "-selection", "clipboard"],
        )

    seen: set[tuple[str, ...]] = set()
    for args in readers:
        key = tuple(args)
        if key in seen:
            continue
        seen.add(key)
        text = _run_reader(args)
        if text:
            return text
    return ""


def missing_dependencies() -> list[str]:
    """Return apt-style package names that appear to be missing."""
    if is_wayland():
        if not shutil.which("wl-paste"):
            return ["wl-clipboard"]
        return []

    if not shutil.which("xclip"):
        return ["xclip"]
    return []
