"""Global hotkey listener for Windows (pynput). Same combo as Linux X11.

Triggers on combo *release* so Ctrl/Alt are less likely to still be held
when we inject Ctrl+C to read the selection.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from listener import HotkeyBridge

DEBOUNCE_SEC = 0.4


def run_windows_hotkey(bridge: "HotkeyBridge") -> None:
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
        # Falling edge of the full combo → fire once keys start coming up.
        if was_active and not active:
            now = time.monotonic()
            if now - last_trigger >= DEBOUNCE_SEC:
                last_trigger = now
                bridge.activated.emit()
        combo_was_active = active

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
