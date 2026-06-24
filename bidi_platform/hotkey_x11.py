"""Global hotkey listener for X11 sessions (pynput)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from listener import HotkeyBridge

DEBOUNCE_SEC = 0.4


def run_x11_hotkey(bridge: "HotkeyBridge") -> None:
    from pynput import keyboard

    ctrl_keys = frozenset({keyboard.Key.ctrl_l, keyboard.Key.ctrl_r})
    alt_keys = frozenset({keyboard.Key.alt_l, keyboard.Key.alt_r})
    pressed: set[keyboard.Key | keyboard.KeyCode] = set()
    combo_was_active = False
    last_trigger = 0.0

    def ctrl_held() -> bool:
        return bool(pressed & ctrl_keys)

    def alt_held() -> bool:
        return bool(pressed & alt_keys)

    def combo_active() -> bool:
        return ctrl_held() and alt_held() and keyboard.Key.space in pressed

    def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
        nonlocal combo_was_active, last_trigger
        if key is None:
            return
        pressed.add(key)
        active = combo_active()
        if active and not combo_was_active:
            now = time.monotonic()
            if now - last_trigger >= DEBOUNCE_SEC:
                last_trigger = now
                bridge.activated.emit()
        combo_was_active = active

    def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> None:
        nonlocal combo_was_active
        if key is None:
            return
        pressed.discard(key)
        combo_was_active = combo_active()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
