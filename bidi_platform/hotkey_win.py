"""Windows global hotkey via RegisterHotKey (no low-level keyboard hook).

pynput's WH_KEYBOARD_LL hook was intercepting our injected Ctrl+C, so Chrome
never received the copy even with correct focus (Chrome_WidgetWin_1).
RegisterHotKey avoids that conflict entirely.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import TYPE_CHECKING

from PyQt6.QtCore import QAbstractNativeEventFilter

if TYPE_CHECKING:
    from listener import HotkeyBridge

WINDOWS_HOTKEY_LABEL = "Ctrl+Shift+Space"

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
VK_SPACE = 0x20
HOTKEY_ID = 0xB1D1  # arbitrary app id


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


def register_hotkey(hwnd: int) -> bool:
    user32 = ctypes.windll.user32
    # Clear any previous registration on this id.
    user32.UnregisterHotKey(hwnd, HOTKEY_ID)
    return bool(
        user32.RegisterHotKey(
            hwnd,
            HOTKEY_ID,
            MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT,
            VK_SPACE,
        )
    )


def unregister_hotkey(hwnd: int) -> None:
    ctypes.windll.user32.UnregisterHotKey(hwnd, HOTKEY_ID)


class WinHotkeyFilter(QAbstractNativeEventFilter):
    """Receives WM_HOTKEY on the Qt event loop."""

    def __init__(self, bridge: "HotkeyBridge") -> None:
        super().__init__()
        self._bridge = bridge

    def nativeEventFilter(self, eventType, message):  # noqa: N802
        et = eventType if isinstance(eventType, (bytes, bytearray)) else bytes(eventType)
        if et not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0
        try:
            msg = MSG.from_address(int(message))
        except (TypeError, ValueError, OverflowError):
            return False, 0
        if msg.message != WM_HOTKEY or int(msg.wParam) != HOTKEY_ID:
            return False, 0

        from bidi_platform.selection_win import note_foreground_window

        note_foreground_window()
        self._bridge.activated.emit()
        return True, 0
