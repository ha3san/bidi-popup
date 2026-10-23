"""Read highlighted text on Windows.

Strategy: UIA (incl. Chrome Document) → WM_COPY → SendInput Ctrl+C.
No pynput hook should be active when SendInput runs (see hotkey_win.py).

Debug: %LOCALAPPDATA%\\bidi-popup\\last-capture.log
"""

from __future__ import annotations

import os
import time
from pathlib import Path

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
WM_COPY = 0x0301
SMTO_ABORTIFHUNG = 0x0002
SW_RESTORE = 9

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_SPACE = 0x20
VK_C = 0x43
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5

KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

_MODIFIER_VKS = (
    VK_SHIFT,
    VK_CONTROL,
    VK_MENU,
    VK_SPACE,
    VK_LSHIFT,
    VK_RSHIFT,
    VK_LCONTROL,
    VK_RCONTROL,
    VK_LMENU,
    VK_RMENU,
)

_target_hwnd: int = 0


def note_foreground_window() -> None:
    global _target_hwnd
    try:
        _target_hwnd = int(ctypes_user32().GetForegroundWindow() or 0)
    except Exception:
        _target_hwnd = 0


def ctypes_user32():
    import ctypes

    return ctypes.windll.user32


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


def _window_debug(hwnd: int) -> str:
    if not hwnd:
        return "hwnd=0"
    import ctypes

    user32 = ctypes.windll.user32
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    title = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, title, 256)
    return f"hwnd={hwnd} class={buf.value!r} title={title.value[:80]!r}"


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


def _send_key_events(pairs: list[tuple[int, int]]) -> None:
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

    n = len(pairs)
    events = (INPUT * n)()
    for i, (vk, flags) in enumerate(pairs):
        events[i].type = INPUT_KEYBOARD
        events[i].ki = KEYBDINPUT(vk, 0, flags, 0, None)
    sent = user32.SendInput(n, ctypes.byref(events), ctypes.sizeof(INPUT))
    if sent != n:
        # Fallback for environments that reject SendInput batches.
        for vk, flags in pairs:
            user32.keybd_event(vk, 0, flags, 0)


def _force_release_modifiers() -> None:
    _send_key_events([(vk, KEYEVENTF_KEYUP) for vk in _MODIFIER_VKS])
    time.sleep(0.05)


def _wait_hotkey_keys_released(timeout: float = 1.5) -> None:
    _ctypes, _wintypes, user32, _kernel32 = _win()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(_key_down(user32, vk) for vk in _MODIFIER_VKS):
            time.sleep(0.05)
            break
        time.sleep(0.02)
    _force_release_modifiers()


def _restore_target_focus() -> int:
    import ctypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = _target_hwnd or int(user32.GetForegroundWindow() or 0)
    if not hwnd:
        return 0

    fg = int(user32.GetForegroundWindow() or 0)
    if fg == hwnd:
        return hwnd

    tid_current = kernel32.GetCurrentThreadId()
    tid_fg = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    tid_target = user32.GetWindowThreadProcessId(hwnd, None)

    if tid_fg:
        user32.AttachThreadInput(tid_current, tid_fg, True)
    if tid_target and tid_target != tid_fg:
        user32.AttachThreadInput(tid_current, tid_target, True)

    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)

    if tid_fg:
        user32.AttachThreadInput(tid_current, tid_fg, False)
    if tid_target and tid_target != tid_fg:
        user32.AttachThreadInput(tid_current, tid_target, False)

    time.sleep(0.1)
    return hwnd


def _uia_text_from_control(control) -> str:
    if control is None:
        return ""
    try:
        pattern = control.GetTextPattern()
    except Exception:
        pattern = None
    if pattern is None:
        return ""
    try:
        ranges = pattern.GetSelection()
        if ranges:
            text = "".join(r.GetText(-1) for r in ranges).strip()
            if text:
                return text
    except Exception:
        pass
    return ""


def _uia_selected_text(hwnd: int) -> str:
    try:
        import uiautomation as auto
    except ImportError:
        return ""

    try:
        auto.InitializeUIAutomationInCurrentThread()
    except Exception:
        pass

    candidates = []
    try:
        focused = auto.GetFocusedControl()
        if focused is not None:
            candidates.append(focused)
    except Exception:
        pass

    root = None
    try:
        if hwnd:
            root = auto.ControlFromHandle(hwnd)
            if root is not None:
                candidates.append(root)
                # Chromium document / pane often holds the selection.
                try:
                    doc = root.Control(ControlType=auto.ControlType.Document, searchDepth=12)
                    if doc is not None:
                        candidates.append(doc)
                except Exception:
                    pass
                try:
                    pane = root.Control(ClassName="Chrome_RenderWidgetHostHWND", searchDepth=8)
                    if pane is not None:
                        candidates.append(pane)
                except Exception:
                    pass
    except Exception:
        pass

    seen: set[int] = set()
    for control in candidates:
        current = control
        for _ in range(14):
            if current is None:
                break
            try:
                rid = id(current)
            except Exception:
                rid = 0
            if rid in seen:
                break
            seen.add(rid)
            text = _uia_text_from_control(current)
            if text:
                return text
            try:
                current = current.GetParentControl()
            except Exception:
                break
    return ""


def _focused_hwnds(preferred: int) -> list[int]:
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

    hwnds: list[int] = []
    if preferred:
        hwnds.append(preferred)
    fg = int(user32.GetForegroundWindow() or 0)
    if fg:
        hwnds.append(fg)
        tid = user32.GetWindowThreadProcessId(fg, None)
        info = GUITHREADINFO()
        info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(tid, ctypes.byref(info)) and info.hwndFocus:
            hwnds.insert(0, int(info.hwndFocus))

    seen: set[int] = set()
    ordered: list[int] = []
    for h in hwnds:
        if h and h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered


def _wm_copy(preferred: int) -> None:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    result = wintypes.DWORD()
    for hwnd in _focused_hwnds(preferred):
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
    _send_key_events(
        [
            (VK_CONTROL, 0),
            (VK_C, 0),
            (VK_C, KEYEVENTF_KEYUP),
            (VK_CONTROL, KEYEVENTF_KEYUP),
        ]
    )


def _process_events() -> None:
    try:
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.processEvents()
    except Exception:
        pass


def _wait_clipboard_changed(sentinel: str, timeout: float = 2.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _process_events()
        text = _get_clipboard()
        if text and text != sentinel:
            return text.strip()
        time.sleep(0.04)
    text = _get_clipboard().strip()
    if not text or text == sentinel:
        return ""
    return text


def get_selected_text_windows() -> str:
    previous = _get_clipboard()
    methods_tried: list[str] = []

    _wait_hotkey_keys_released()
    hwnd = _restore_target_focus()
    win_info = _window_debug(hwnd)

    uia_text = _uia_selected_text(hwnd)
    if uia_text:
        _log(f"ok method=uia len={len(uia_text)} {win_info}")
        return uia_text
    methods_tried.append("uia:empty")

    sentinel = f"__bidi_popup_{time.time_ns()}__"
    try:
        _set_clipboard(sentinel)
        _restore_target_focus()

        _wm_copy(hwnd)
        text = _wait_clipboard_changed(sentinel, timeout=1.2)
        if text:
            _log(f"ok method=wm_copy len={len(text)} {win_info}")
            return text
        methods_tried.append("wm_copy:empty")

        _set_clipboard(sentinel)
        _restore_target_focus()
        _force_release_modifiers()
        time.sleep(0.05)
        _send_ctrl_c()
        text = _wait_clipboard_changed(sentinel, timeout=2.0)
        if text:
            _log(f"ok method=sendinput len={len(text)} {win_info}")
            return text
        methods_tried.append("sendinput:empty")

        _log(f"fail reason=no_text methods={','.join(methods_tried)} {win_info}")
        return ""
    finally:
        try:
            _set_clipboard(previous)
        except OSError:
            pass
