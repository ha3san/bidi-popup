"""Global hotkey listener for Windows (pynput).

Uses Ctrl+Shift+Space — NOT Ctrl+Alt+Space — because Alt+Space opens the
Windows system menu and steals focus from the browser, which made every
selection method return empty.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from listener import HotkeyBridge

DEBOUNCE_SEC = 0.4
WINDOWS_HOTKEY_LABEL = "Ctrl+Shift+Space"


def run_windows_hotkey(bridge: "HotkeyBridge") -> None:
    from pynput import keyboard

    from bidi_platform.selection_win import note_foreground_window

    ctrl_keys = frozenset({keyboard.Key.ctrl_l, keyboard.Key.ctrl_r})
    shift_keys = frozenset({keyboard.Key.shift_l, keyboard.Key.shift_r})
    pressed: set[keyboard.Key | keyboard.KeyCode] = set()
    combo_was_active = False
    last_trigger = 0.0

    def ctrl_held() -> bool:
        return bool(pressed & ctrl_keys)

    def shift_held() -> bool:
        return bool(pressed & shift_keys)

    def combo_active() -> bool:
        return ctrl_held() and shift_held() and keyboard.Key.space in pressed

    def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
        nonlocal combo_was_active
        if key is None:
            return
        pressed.add(key)
        combo_was_active = combo_active()

    def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> None:
        nonlocal combo_was_active, last_trigger
        if key is None:
            return
        was_active = combo_was_active
        pressed.discard(key)
        active = combo_active()
        if was_active and not active:
            now = time.monotonic()
            if now - last_trigger >= DEBOUNCE_SEC:
                last_trigger = now
                # Capture the app that had focus *before* Qt handles the signal.
                note_foreground_window()
                bridge.activated.emit()
        combo_was_active = active

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
