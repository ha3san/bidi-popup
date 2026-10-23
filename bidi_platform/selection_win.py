"""Read highlighted text on Windows.

Browsers often ignore synthetic Ctrl+C (SendInput). Strategy order:
1) UI Automation TextPattern selection
2) WM_COPY to the focused / foreground window
3) SendInput Ctrl+C as last resort

Clipboard is restored afterwards. A short debug line is written under
%LOCALAPPDATA%\\bidi-popup\\last-capture.log for troubleshooting.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
WM_COPY = 0x0301
SMTO_ABORTIFHUNG = 0x0002

VK_CONTROL = 0x11
VK_MENU = 0x12
VK_SPACE = 0x20
VK_C = 0x43
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5

KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

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

    return ctypes, wintypes, ctypes.windll.user32, ctypes.windll.kernel32


def _log(msg: str) -> None:
    try:
        base = Path(os.environ.get("LOCALAPPDATA") or ".") / "bidi-popup"
        base.mkdir(parents=True, exist_ok=True)
        (base / "last-capture.log").write_text(msg, encoding="utf-8")
    except OSError:
        pass


def _open_clipboard(user32, retries: int = 30) -> bool:
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
    # Prefer Qt clipboard when running inside the GUI thread.
    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            text = app.clipboard().text()
            if text is not None:
                return text
    except Exception:
        pass

    ctypes, _wintypes, user32, kernel32 = _win()
    if not _open_clipboard(user32):
        return ""
    try:
        return _read_clipboard_text(ctypes, user32, kernel32)
    finally:
        user32.CloseClipboard()


def _set_clipboard(text: str) -> None:
    try:
        from PyQt6.QtGui import QClipboard
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.clipboard().setText(text, QClipboard.Mode.Clipboard)
            return
    except Exception:
        pass

    ctypes, _wintypes, user32, kernel32 = _win()
    if not _open_clipboard(user32):
        return
    try:
        _write_clipboard_text(ctypes, user32, kernel32, text)
    finally:
        user32.CloseClipboard()


def _key_down(user32, vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def _wait_hotkey_keys_released(timeout: float = 1.5) -> bool:
    _ctypes, _wintypes, user32, _kernel32 = _win()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(_key_down(user32, vk) for vk in _MODIFIER_VKS):
            time.sleep(0.06)
            return True
        time.sleep(0.02)
    return False


def _uia_selected_text() -> str:
    """Read selection via UI Automation (works in many browsers without Ctrl+C)."""
    try:
        import uiautomation as auto
    except ImportError:
        return ""

    try:
        control = auto.GetFocusedControl()
    except Exception:
        return ""
    if control is None:
        return ""

    current = control
    for _ in range(10):
        if current is None:
            break
        try:
            pattern = current.GetTextPattern()
        except Exception:
            pattern = None
        if pattern is not None:
            try:
                ranges = pattern.GetSelection()
                if ranges:
                    text = "".join(r.GetText(-1) for r in ranges).strip()
                    if text:
                        return text
            except Exception:
                pass
        try:
            current = current.GetParentControl()
        except Exception:
            break
    return ""


def _focused_hwnds():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    fg = user32.GetForegroundWindow()
    hwnds: list[int] = []
    if fg:
        hwnds.append(int(fg))
        tid = user32.GetWindowThreadProcessId(fg, None)
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(tid, ctypes.byref(info)) and info.hwndFocus:
            hwnds.insert(0, int(info.hwndFocus))
    # Unique, focus first
    seen: set[int] = set()
    ordered: list[int] = []
    for h in hwnds:
        if h and h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered


def _wm_copy() -> None:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    result = wintypes.DWORD()
    for hwnd in _focused_hwnds():
        user32.SendMessageTimeoutW(
            hwnd,
            WM_COPY,
            0,
            0,
            SMTO_ABORTIFHUNG,
            400,
            ctypes.byref(result),
        )


def _send_ctrl_c() -> None:
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


def _wait_clipboard_changed(sentinel: str, timeout: float = 1.8) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Let Qt process clipboard change notifications.
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                app.processEvents()
        except Exception:
            pass
        text = _get_clipboard()
        if text and text != sentinel:
            return text.strip()
        time.sleep(0.04)
    text = _get_clipboard().strip()
    if not text or text == sentinel:
        return ""
    return text


def get_selected_text_windows() -> str:
    """Return highlighted text using UIA, then WM_COPY, then Ctrl+C."""
    previous = _get_clipboard()
    methods_tried: list[str] = []

    # 1) UI Automation — no clipboard, best for browsers when available.
    uia_text = _uia_selected_text()
    if uia_text:
        _log(f"ok method=uia len={len(uia_text)}")
        return uia_text
    methods_tried.append("uia:empty")

    sentinel = f"__bidi_popup_{time.time_ns()}__"
    try:
        if not _wait_hotkey_keys_released():
            _log("fail reason=modifiers_timeout methods=" + ",".join(methods_tried))
            return ""

        _set_clipboard(sentinel)

        # 2) WM_COPY — native copy request, often works where SendInput fails.
        _wm_copy()
        text = _wait_clipboard_changed(sentinel, timeout=1.2)
        if text:
            _log(f"ok method=wm_copy len={len(text)}")
            return text
        methods_tried.append("wm_copy:empty")

        # 3) Synthetic Ctrl+C last.
        _set_clipboard(sentinel)
        _send_ctrl_c()
        text = _wait_clipboard_changed(sentinel, timeout=1.5)
        if text:
            _log(f"ok method=sendinput len={len(text)}")
            return text
        methods_tried.append("sendinput:empty")

        _log("fail reason=no_text methods=" + ",".join(methods_tried))
        return ""
    finally:
        try:
            _set_clipboard(previous)
        except OSError:
            pass
