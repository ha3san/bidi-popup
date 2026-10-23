"""Read highlighted text on Windows via Ctrl+C + clipboard (restore after).

Imported only when running on Windows — keep top-level free of windll so
accidental imports on Linux never break the Linux build.
"""

from __future__ import annotations

import time

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def _win():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    return ctypes, wintypes, user32, kernel32


def _open_clipboard(user32, retries: int = 10) -> bool:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.02)
    return False


def _read_clipboard_text(ctypes, user32, kernel32) -> str:
    if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return ""
    handle = user32.GetClipboardData(CF_UNICODETEXT)
    if not handle:
        return ""
    locked = kernel32.GlobalLock(handle)
    if not locked:
        return ""
    try:
        return ctypes.wstring_at(locked)
    finally:
        kernel32.GlobalUnlock(handle)


def _write_clipboard_text(ctypes, user32, kernel32, text: str) -> None:
    user32.EmptyClipboard()
    data = text.encode("utf-16-le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        return
    locked = kernel32.GlobalLock(handle)
    if not locked:
        return
    try:
        ctypes.memmove(locked, data, len(data))
    finally:
        kernel32.GlobalUnlock(handle)
    user32.SetClipboardData(CF_UNICODETEXT, handle)


def _get_clipboard() -> str:
    ctypes, _wintypes, user32, kernel32 = _win()
    if not _open_clipboard(user32):
        return ""
    try:
        return _read_clipboard_text(ctypes, user32, kernel32)
    finally:
        user32.CloseClipboard()


def _set_clipboard(text: str) -> None:
    ctypes, _wintypes, user32, kernel32 = _win()
    if not _open_clipboard(user32):
        return
    try:
        _write_clipboard_text(ctypes, user32, kernel32, text)
    finally:
        user32.CloseClipboard()


def _send_ctrl_c() -> None:
    from pynput.keyboard import Controller, Key

    keyboard = Controller()
    # Let the hotkey keys finish releasing before injecting Ctrl+C.
    time.sleep(0.08)
    with keyboard.pressed(Key.ctrl):
        keyboard.tap("c")
    time.sleep(0.12)


def get_selected_text_windows() -> str:
    """Copy current selection with Ctrl+C, then restore the previous clipboard."""
    previous = _get_clipboard()
    try:
        _send_ctrl_c()
        selected = _get_clipboard().strip()
        # If nothing changed, treat as empty selection (avoid showing old clipboard).
        if selected == previous.strip():
            return ""
        return selected
    finally:
        try:
            _set_clipboard(previous)
        except OSError:
            pass
