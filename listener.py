#!/usr/bin/env python3
"""Global hotkey listener: Ctrl+Alt+Space opens selected text in an RTL popup."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from bidi_platform.selection import get_selected_text, missing_dependencies
from bidi_platform.session import is_wayland, is_x11, session_type
from bidi_platform.trigger import TriggerServer, send_trigger
from popup import Popup

ROOT = Path(__file__).resolve().parent
ICON_PATH = ROOT / "assets" / "icon.svg"


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
    icon_arg = ["-i", str(ICON_PATH)] if ICON_PATH.is_file() else ["-i", "accessories-text-editor"]
    try:
        subprocess.run(
            ["notify-send", "-a", "bidi-popup", *icon_arg, title, body],
            check=False,
            timeout=3,
        )
    except (FileNotFoundError, OSError):
        pass


class HotkeyBridge(QObject):
    activated = pyqtSignal()


class BidiPopupApp:
    def __init__(self) -> None:
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Bidi Popup")
        self._app.setQuitOnLastWindowClosed(False)

        self._popup: Popup | None = None
        self._bridge = HotkeyBridge()
        self._bridge.activated.connect(self._on_hotkey)

        self._setup_tray()
        self._maybe_wayland_hint()

        thread = threading.Thread(target=self._run_listeners, name="hotkey-listener", daemon=True)
        thread.start()

    def _setup_tray(self) -> None:
        self._tray = QSystemTrayIcon(app_icon())
        hotkey = "Ctrl+Alt+Space" if is_x11() else "shortcut (see README)"
        self._tray.setToolTip(f"Bidi Popup — {hotkey}")

        menu = QMenu()
        menu.addAction("Show last popup", self._show_popup)
        menu.addAction("Settings…", self._show_settings)
        menu.addSeparator()
        menu.addAction("Quit", self._app.quit)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _maybe_wayland_hint(self) -> None:
        if not is_wayland():
            return
        notify(
            "Bidi Popup",
            "Wayland: یک‌بار ./install-shortcut.sh را اجرا کن تا Ctrl+Alt+Space تنظیم شود",
        )

    def _run_listeners(self) -> None:
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

            if not text:
                notify("Bidi Popup", "متنی انتخاب نشده — اول متن را highlight کن")
                return

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
