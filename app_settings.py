"""Persistent user preferences for Bidi Popup."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QSettings

SETTINGS_ORG = "bidi-popup"
SETTINGS_APP = "bidi-popup"

FONT_CANDIDATES = (
    "Vazirmatn",
    "Noto Sans Arabic",
    "Iranian Sans",
    "Tahoma",
    "DejaVu Sans",
)


@dataclass
class AppSettings:
    auto_size: bool = True
    font_size: int = 12
    font_family: str = ""  # empty = pick first installed candidate
    rtl_default: bool = True
    theme: str = "dark"
    remember_geometry: bool = True
    fixed_width: int = 580
    fixed_height: int = 380
    auto_max_width: int = 920
    auto_max_height: int = 720
    open_near_cursor: bool = True

    @classmethod
    def load(cls, store: QSettings | None = None) -> AppSettings:
        s = store or QSettings(SETTINGS_ORG, SETTINGS_APP)
        theme = s.value("theme", "dark", type=str)
        if theme == "auto":
            theme = "dark"
        return cls(
            auto_size=s.value("auto_size", True, type=bool),
            font_size=s.value("font_size", 12, type=int),
            font_family=s.value("font_family", "", type=str) or "",
            rtl_default=s.value("rtl", True, type=bool),
            theme=theme,
            remember_geometry=s.value("remember_geometry", True, type=bool),
            fixed_width=s.value("width", 580, type=int),
            fixed_height=s.value("height", 380, type=int),
            auto_max_width=s.value("auto_max_width", 920, type=int),
            auto_max_height=s.value("auto_max_height", 720, type=int),
            open_near_cursor=s.value("open_near_cursor", True, type=bool),
        )

    def save(self, store: QSettings | None = None) -> None:
        s = store or QSettings(SETTINGS_ORG, SETTINGS_APP)
        s.setValue("auto_size", self.auto_size)
        s.setValue("font_size", self.font_size)
        s.setValue("font_family", self.font_family)
        s.setValue("rtl", self.rtl_default)
        s.setValue("theme", self.theme)
        s.setValue("remember_geometry", self.remember_geometry)
        s.setValue("width", self.fixed_width)
        s.setValue("height", self.fixed_height)
        s.setValue("auto_max_width", self.auto_max_width)
        s.setValue("auto_max_height", self.auto_max_height)
        s.setValue("open_near_cursor", self.open_near_cursor)
        s.sync()
