"""Theme helpers — follow GNOME on Ubuntu or use manual light/dark."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    name: str
    window_bg: str
    window_border: str
    text_bg: str
    text_fg: str
    title_fg: str
    muted_fg: str
    button_hover: str
    selection_bg: str
    scrollbar: str
    scrollbar_hover: str
    find_bar_bg: str
    toast_bg: str
    toast_fg: str
    shadow: str


DARK = Palette(
    name="dark",
    window_bg="#2b2b2b",
    window_border="#1a1a1a",
    text_bg="#2b2b2b",
    text_fg="#ececec",
    title_fg="#9a9a9a",
    muted_fg="#6e6e6e",
    button_hover="#3d3d3d",
    selection_bg="#4a6fa5",
    scrollbar="#3d3d3d",
    scrollbar_hover="#555555",
    find_bar_bg="#333333",
    toast_bg="#3d3d3d",
    toast_fg="#ececec",
    shadow="#000000",
)

LIGHT = Palette(
    name="light",
    window_bg="#f5f5f7",
    window_border="#d1d1d6",
    text_bg="#ffffff",
    text_fg="#1d1d1f",
    title_fg="#6e6e73",
    muted_fg="#86868b",
    button_hover="#e8e8ed",
    selection_bg="#b4d5fe",
    scrollbar="#e0e0e5",
    scrollbar_hover="#c8c8cd",
    find_bar_bg="#ebebef",
    toast_bg="#1d1d1f",
    toast_fg="#ffffff",
    shadow="#888888",
)


def gnome_prefers_dark() -> bool:
    try:
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip().lower()
        if "dark" in out:
            return True
        if "light" in out:
            return False
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    try:
        theme = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip().lower()
        return "dark" in theme
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return True


def resolve_palette(mode: str) -> Palette:
    if mode == "light":
        return LIGHT
    if mode == "dark":
        return DARK
    return DARK if gnome_prefers_dark() else LIGHT


def build_stylesheet(p: Palette) -> str:
    return f"""
    QWidget#MacFrame {{
        background-color: {p.window_bg};
        border: 1px solid {p.window_border};
        border-radius: 12px;
    }}
    QWidget#TitleBar {{
        background-color: transparent;
    }}
    QLabel#TitleLabel {{
        color: {p.title_fg};
        font-size: 13px;
        font-weight: 500;
    }}
    QTextEdit#ContentBox {{
        background-color: {p.text_bg};
        color: {p.text_fg};
        border: none;
        padding: 12px 14px;
        selection-background-color: {p.selection_bg};
    }}
    QPushButton#ToolButton {{
        background-color: transparent;
        border: none;
        color: {p.title_fg};
        font-size: 13px;
        padding: 4px 8px;
        border-radius: 6px;
        min-width: 28px;
        min-height: 24px;
    }}
    QPushButton#ToolButton:hover {{
        background-color: {p.button_hover};
        color: {p.text_fg};
    }}
    /* Traffic-light buttons carry their own inline styles — do not inherit ToolButton rules. */
    QLineEdit#FindInput {{
        background-color: {p.text_bg};
        color: {p.text_fg};
        border: 1px solid {p.window_border};
        border-radius: 6px;
        padding: 4px 8px;
    }}
    QWidget#FindBar {{
        background-color: {p.find_bar_bg};
        border-top: 1px solid {p.window_border};
    }}
    QLabel#ToastLabel {{
        background-color: {p.toast_bg};
        color: {p.toast_fg};
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 13px;
    }}
  QScrollBar:vertical {{
        background: {p.text_bg};
        width: 8px;
        margin: 4px 2px 4px 0;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.scrollbar};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p.scrollbar_hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {p.text_bg};
        height: 8px;
        margin: 0 4px 2px 4px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.scrollbar};
        border-radius: 4px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {p.scrollbar_hover};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    """
