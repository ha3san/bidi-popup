"""Detect display / OS session type (Linux X11/Wayland, or Windows)."""

from __future__ import annotations

import os
import sys


def is_windows() -> bool:
    return sys.platform == "win32"


def session_type() -> str:
    """Return 'windows', 'x11', 'wayland', or 'unknown'."""
    # Windows first so Linux helpers below stay behaviorally identical on Linux.
    if is_windows():
        return "windows"

    value = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if value in ("x11", "wayland"):
        return value
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def is_x11() -> bool:
    # Unchanged rule for Linux; "windows" is neither x11 nor unknown.
    return session_type() in ("x11", "unknown")


def is_wayland() -> bool:
    return session_type() == "wayland"
