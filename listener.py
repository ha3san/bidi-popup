#!/usr/bin/env python3
"""Global hotkey listener: Ctrl+Alt+Space opens selected text in an RTL popup."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from bidi_platform.selection import get_selected_text, missing_dependencies
from bidi_platform.session import is_wayland, is_windows, is_x11, session_type
from bidi_platform.trigger import TriggerServer, send_trigger
from popup import Popup

def _resource_root() -> Path:
    """App root for assets — supports PyInstaller freeze on Windows."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT = _resource_root()
ICON_PATH = ROOT / "assets" / "icon.svg"

# Set by BidiPopupApp so Windows notifications can use the tray.
_tray_ref: QSystemTrayIcon | None = None
# Keep Windows mutex handle alive for single-instance.
_win_mutex = None


def app_icon() -> QIcon:
    if ICON_PATH.is_file():
        icon = QIcon(str(ICON_PATH))
        if not icon.isNull():
            return icon
    for name in ("accessories-text-editor", "text-editor"):
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    return QIcon()


def notify(title: str, body: str) -> None:
    if is_windows():
        if _tray_ref is not None:
            _tray_ref.showMessage(
                title,
                body,
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
        return

    icon_arg = ["-i", str(ICON_PATH)] if ICON_PATH.is_file() else ["-i", "accessories-text-editor"]
    try:
        subprocess.run(
            ["notify-send", "-a", "bidi-popup", *icon_arg, title, body],
            check=False,
            timeout=3,
        )
    except (FileNotFoundError, OSError):
        pass


def _acquire_windows_single_instance() -> bool:
    """Return False if another instance already holds the mutex."""
    global _win_mutex
    import ctypes

    kernel32 = ctypes.windll.kernel32
    # Named mutex — survives for process lifetime via global ref.
    _win_mutex = kernel32.CreateMutexW(None, False, "Local\\BidiPopupSingleInstance")
    ERROR_ALREADY_EXISTS = 183
    return kernel32.GetLastError() != ERROR_ALREADY_EXISTS


class HotkeyBridge(QObject):
    activated = pyqtSignal()


class BidiPopupApp:
    def __init__(self) -> None:
        global _tray_ref
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Bidi Popup")
        self._app.setQuitOnLastWindowClosed(False)

        self._popup: Popup | None = None
        self._bridge = HotkeyBridge()
        self._bridge.activated.connect(self._on_hotkey)
        self._autostart_action = None
        self._win_clipboard_fallback = False
        self._hotkey_host: QWidget | None = None
        self._hotkey_filter = None

        self._setup_tray()
        _tray_ref = self._tray
        self._maybe_wayland_hint()

        if is_windows():
            self._setup_windows_hotkey()
            self._app.aboutToQuit.connect(self._teardown_windows_hotkey)
        else:
            # Linux only — keep background X11/Wayland listeners unchanged.
            thread = threading.Thread(target=self._run_listeners, name="hotkey-listener", daemon=True)
            thread.start()

    def _setup_tray(self) -> None:
        self._tray = QSystemTrayIcon(app_icon())
        if is_windows():
            from bidi_platform.hotkey_win import WINDOWS_HOTKEY_LABEL

            hotkey = WINDOWS_HOTKEY_LABEL
        elif is_x11():
            hotkey = "Ctrl+Alt+Space"
        else:
            hotkey = "shortcut (see README)"
        self._tray.setToolTip(f"Bidi Popup — {hotkey}")

        menu = QMenu()
        menu.addAction("Show last popup", self._show_popup)
        menu.addAction("Settings…", self._show_settings)
        if is_windows():
            from bidi_platform.autostart_win import is_autostart_enabled

            label = "Disable start with Windows" if is_autostart_enabled() else "Start with Windows"
            self._autostart_action = menu.addAction(label, self._toggle_windows_autostart)
        menu.addSeparator()
        menu.addAction("Quit", self._app.quit)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _toggle_windows_autostart(self) -> None:
        from bidi_platform.autostart_win import toggle_autostart

        enabled = toggle_autostart()
        if self._autostart_action is not None:
            self._autostart_action.setText(
                "Disable start with Windows" if enabled else "Start with Windows"
            )
        notify(
            "Bidi Popup",
            "با روشن شدن ویندوز اجرا می‌شود" if enabled else "اجرای خودکار خاموش شد",
        )

    def _maybe_wayland_hint(self) -> None:
        if not is_wayland():
            return
        notify(
            "Bidi Popup",
            "Wayland: یک‌بار ./install-shortcut.sh را اجرا کن تا Ctrl+Alt+Space تنظیم شود",
        )

    def _setup_windows_hotkey(self) -> None:
        from bidi_platform.hotkey_win import WinHotkeyFilter, register_hotkey

        # Hidden HWND that receives WM_HOTKEY (no low-level keyboard hook).
        # PyQt6 has no createWinId(); winId() after show() creates the native handle.
        self._hotkey_host = QWidget()
        self._hotkey_host.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self._hotkey_host.show()
        hwnd = int(self._hotkey_host.winId())
        if not hwnd:
            notify("Bidi Popup", "نتوانست پنجرهٔ میانبر را بسازد")
            print("bidi-popup: winId() returned 0", file=sys.stderr)
            return
        if not register_hotkey(hwnd):
            notify("Bidi Popup", "نتوانست میانبر Ctrl+Shift+Space را ثبت کند")
            print("bidi-popup: RegisterHotKey failed", file=sys.stderr)
            return
        self._hotkey_filter = WinHotkeyFilter(self._bridge)
        self._app.installNativeEventFilter(self._hotkey_filter)

    def _teardown_windows_hotkey(self) -> None:
        if self._hotkey_host is None:
            return
        try:
            from bidi_platform.hotkey_win import unregister_hotkey

            unregister_hotkey(int(self._hotkey_host.winId()))
        except Exception:
            pass

    def _run_listeners(self) -> None:
        # --- Linux path only (unchanged behavior) ---
        TriggerServer(self._bridge.activated.emit).start()

        if is_x11():
            try:
                from bidi_platform.hotkey_x11 import run_x11_hotkey

                run_x11_hotkey(self._bridge)
            except Exception as exc:
                print(f"bidi-popup: X11 hotkey unavailable ({exc})", file=sys.stderr)
                threading.Event().wait()
        else:
            threading.Event().wait()

    def _show_popup(self) -> None:
        if self._popup is not None:
            self._popup.show()
            self._popup.raise_()
            self._popup.activateWindow()

    def _show_settings(self) -> None:
        from settings_dialog import SettingsDialog

        dialog = SettingsDialog()
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if dialog.exec():
            if self._popup is not None:
                self._popup.reload_preferences()

    def _on_hotkey(self) -> None:
        try:
            text = get_selected_text()
            anchor = QPoint(QCursor.pos())

            if not text and is_windows():
                # Fallback: ask for a manual Ctrl+C, then re-read clipboard.
                if self._win_clipboard_fallback:
                    clip = (self._app.clipboard().text() or "").strip()
                    self._win_clipboard_fallback = False
                    if clip:
                        text = clip
                    else:
                        notify("Bidi Popup", "کلیپ‌بورد خالی بود — متن را Ctrl+C کن و دوباره میانبر را بزن")
                        return
                else:
                    self._win_clipboard_fallback = True
                    notify(
                        "Bidi Popup",
                        "خودکار کپی نشد. متن را با Ctrl+C کپی کن، بعد دوباره Ctrl+Shift+Space را بزن",
                    )
                    return

            if not text:
                notify("Bidi Popup", "متنی انتخاب نشده — اول متن را highlight کن")
                return

            self._win_clipboard_fallback = False

            if self._popup is not None and self._popup.isVisible():
                self._popup.set_text(text, anchor=anchor)
                return

            if self._popup is not None:
                self._popup.close()
                self._popup = None

            self._popup = Popup(text, anchor=anchor)
            self._popup.destroyed.connect(self._clear_popup)
            self._popup.show()
        except Exception as exc:
            notify("Bidi Popup", f"خطا در باز کردن پنجره: {exc}")
            print(f"bidi-popup error: {exc}", file=sys.stderr)

    def _clear_popup(self) -> None:
        self._popup = None

    def run(self) -> int:
        return self._app.exec()


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "trigger":
        return 0 if send_trigger() else 1

    if is_windows() and not _acquire_windows_single_instance():
        print("bidi-popup: already running", file=sys.stderr)
        return 1

    missing = missing_dependencies()
    if missing:
        pkgs = " ".join(missing)
        sess = session_type()
        print(
            f"bidi-popup: install required packages for {sess} session:\n"
            f"  sudo apt install {pkgs}",
            file=sys.stderr,
        )
        return 1

    return BidiPopupApp().run()


if __name__ == "__main__":
    sys.exit(main())
