"""Linux platform helpers for Bidi Popup."""

from bidi_platform.selection import get_selected_text, missing_dependencies
from bidi_platform.session import is_wayland, is_x11, session_type
from bidi_platform.trigger import send_trigger

__all__ = [
    "get_selected_text",
    "missing_dependencies",
    "is_wayland",
    "is_x11",
    "session_type",
    "send_trigger",
]
