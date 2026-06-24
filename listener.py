#!/usr/bin/env python3
"""Global hotkey listener: Ctrl+Alt+Space opens selected text in an RTL popup."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

from PyQt6.QtCore import QObject, QPoint, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from pynput import keyboard

from popup import Popup

ROOT = Path(__file__).resolve().parent
DEBOUNCE_SEC = 0.4

CTRL_KEYS = frozenset({keyboard.Key.ctrl_l, keyboard.Key.ctrl_r})
ALT_KEYS = frozenset({keyboard.Key.alt_l, keyboard.Key.alt_r})


class HotkeyBridge(QObject):
    activated = pyqtSignal()


def notify(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "-a", "bidi-popup", "-i", "accessories-text-editor", title, body],
            check=False,
            timeout=3,
        )
    except (FileNotFoundError, OSError):
        pass


def get_selected_text() -> str:
    """Read X11 primary selection first, then clipboard."""
    for args in (
        ["xclip", "-o", "-selection", "primary"],
        ["xclip", "-o", "-selection", "clipboard"],
    ):
        try:
            raw = subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=2)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
        text = raw.decode("utf-8", errors="replace").strip()
        if text:
            return text
    return ""


class HotkeyListener:
    def __init__(self, bridge: HotkeyBridge) -> None:
        self._bridge = bridge
        self._pressed: set[keyboard.Key | keyboard.KeyCode] = set()
        self._combo_was_active = False
        self._last_trigger = 0.0

    def _ctrl_held(self) -> bool:
        return bool(self._pressed & CTRL_KEYS)

    def _alt_held(self) -> bool:
        return bool(self._pressed & ALT_KEYS)

    def _combo_active(self) -> bool:
        return (
            self._ctrl_held()
            and self._alt_held()
            and keyboard.Key.space in self._pressed
        )

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        self._pressed.add(key)
        active = self._combo_active()
        if active and not self._combo_was_active:
            now = time.monotonic()
            if now - self._last_trigger >= DEBOUNCE_SEC:
                self._last_trigger = now
                self._bridge.activated.emit()
        self._combo_was_active = active

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        if key is None:
            return
        self._pressed.discard(key)
        self._combo_was_active = self._combo_active()

    def run(self) -> None:
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()


class RtlViewerApp:
    def __init__(self) -> None:
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Bidi Popup")
        self._app.setQuitOnLastWindowClosed(False)

        self._popup: Popup | None = None
        self._bridge = HotkeyBridge()
        self._bridge.activated.connect(self._on_hotkey)

        self._setup_tray()

        thread = threading.Thread(target=self._run_listener, name="hotkey-listener", daemon=True)
        thread.start()

    def _setup_tray(self) -> None:
        icon = QIcon.fromTheme("accessories-text-editor")
        if icon.isNull():
            icon = QIcon.fromTheme("text-editor")

        self._tray = QSystemTrayIcon(icon)
        self._tray.setToolTip("Bidi Popup — Ctrl+Alt+Space")

        menu = QMenu()
        menu.addAction("Show last popup", self._show_popup)
        menu.addSeparator()
        menu.addAction("Quit", self._app.quit)
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _run_listener(self) -> None:
        HotkeyListener(self._bridge).run()

    def _show_popup(self) -> None:
        if self._popup is not None:
            self._popup.show()
            self._popup.raise_()
            self._popup.activateWindow()

    def _on_hotkey(self) -> None:
        try:
            text = get_selected_text()
            anchor = QPoint(QCursor.pos())

            if not text:
                notify("Bidi Popup", "متنی انتخاب نشده — اول متن را highlight کن یا Ctrl+C بزن")
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
    if subprocess.run(["which", "xclip"], capture_output=True).returncode != 0:
        print("bidi-popup: install xclip first (sudo apt install xclip)", file=sys.stderr)
        return 1
    return RtlViewerApp().run()


if __name__ == "__main__":
    sys.exit(main())
