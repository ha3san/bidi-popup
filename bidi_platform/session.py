"""Detect Linux display session type (X11 vs Wayland)."""

from __future__ import annotations

import os


def session_type() -> str:
    """Return 'x11', 'wayland', or 'unknown'."""
    value = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if value in ("x11", "wayland"):
        return value
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "unknown"


def is_x11() -> bool:
    return session_type() in ("x11", "unknown")


def is_wayland() -> bool:
    return session_type() == "wayland"
