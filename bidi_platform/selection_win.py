"""Read highlighted text on Windows via Ctrl+C + clipboard (restore after).

Imported only when running on Windows — keep top-level free of windll so
accidental imports on Linux never break the Linux build.
"""

from __future__ import annotations

import time

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

# Virtual-key codes
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_SPACE = 0x20
VK_C = 0x43
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5

KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

# Hotkey modifiers that must be up before we inject Ctrl+C
_MODIFIER_VKS = (
    VK_CONTROL,
    VK_MENU,
    VK_SPACE,
    VK_LCONTROL,
    VK_RCONTROL,
    VK_LMENU,
    VK_RMENU,
)


def _win():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    return ctypes, wintypes, user32, kernel32


def _open_clipboard(user32, retries: int = 20) -> bool:
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


def _clear_clipboard() -> None:
    _ctypes, _wintypes, user32, _kernel32 = _win()
    if not _open_clipboard(user32):
        return
    try:
        user32.EmptyClipboard()
    finally:
        user32.CloseClipboard()


def _key_down(user32, vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def _wait_hotkey_keys_released(timeout: float = 1.5) -> bool:
    """Wait until Ctrl/Alt/Space from the hotkey are no longer held."""
    _ctypes, _wintypes, user32, _kernel32 = _win()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(_key_down(user32, vk) for vk in _MODIFIER_VKS):
            # Brief settle so the target app sees a clean key state.
            time.sleep(0.05)
            return True
        time.sleep(0.02)
    return False


def _send_ctrl_c() -> None:
    """Inject Ctrl+C with SendInput (more reliable than pynput while Alt was held)."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        _anonymous_ = ("i",)
        _fields_ = [("type", wintypes.DWORD), ("i", _I)]

    def _event(vk: int, flags: int = 0) -> INPUT:
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki = KEYBDINPUT(vk, 0, flags, 0, None)
        return inp

    events = (INPUT * 4)(
        _event(VK_CONTROL, 0),
        _event(VK_C, 0),
        _event(VK_C, KEYEVENTF_KEYUP),
        _event(VK_CONTROL, KEYEVENTF_KEYUP),
    )
    user32.SendInput(4, ctypes.byref(events), ctypes.sizeof(INPUT))


def _wait_clipboard_changed(sentinel: str, timeout: float = 0.8) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = _get_clipboard()
        if text and text != sentinel:
            return text.strip()
        time.sleep(0.03)
    # Final read — empty or still sentinel means copy failed / no selection.
    text = _get_clipboard().strip()
    if not text or text == sentinel:
        return ""
    return text


def get_selected_text_windows() -> str:
    """Copy current selection with Ctrl+C, then restore the previous clipboard."""
    previous = _get_clipboard()
    sentinel = f"__bidi_popup_{time.time_ns()}__"
    try:
        # Unique marker so we can tell a real copy from a failed Ctrl+C.
        _set_clipboard(sentinel)
        if not _wait_hotkey_keys_released():
            return ""
        _send_ctrl_c()
        return _wait_clipboard_changed(sentinel)
    finally:
        try:
            _set_clipboard(previous)
        except OSError:
            pass
