"""Settings dialog for Bidi Popup."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase, QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app_settings import FONT_CANDIDATES, AppSettings
from theme import build_settings_stylesheet, resolve_palette


def _screen_pixel_limits() -> tuple[int, int]:
    screen = QGuiApplication.primaryScreen()
    if screen is not None:
        geo = screen.availableGeometry()
        return geo.width(), geo.height()
    return 7680, 4320


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsDialog")
        self.setWindowTitle("تنظیمات Bidi Popup")
        self.setMinimumWidth(480)
        self.resize(520, 620)
        self._settings = AppSettings.load()
        self._screen_w, self._screen_h = _screen_pixel_limits()
        self._build_ui()
        self._load_values()
        self._apply_theme(self._settings.theme)
        self._theme.currentIndexChanged.connect(self._on_theme_preview)

    def _size_spin(self, minimum: int, maximum: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSuffix(" px")
        spin.setSingleStep(20)
        spin.setAccelerated(True)
        return spin

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 16)
        outer.setSpacing(12)

        title = QLabel("تنظیمات")
        title.setObjectName("SettingsTitle")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName("SettingsScroll")

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 4, 0)
        body_layout.setSpacing(8)

        size_group = QGroupBox("اندازه پنجره")
        size_form = QFormLayout(size_group)
        size_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        size_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        size_form.setHorizontalSpacing(16)
        size_form.setVerticalSpacing(12)

        self._auto_size = QCheckBox("اندازه خودکار بر اساس متن")
        self._auto_size.setToolTip("عرض و ارتفاع با توجه به طول خطوط و حجم متن تنظیم می‌شود")
        size_form.addRow(self._auto_size)

        self._fixed_w = self._size_spin(320, self._screen_w)
        self._fixed_h = self._size_spin(200, self._screen_h)
        size_form.addRow("عرض ثابت", self._fixed_w)
        size_form.addRow("ارتفاع ثابت", self._fixed_h)

        self._max_w = self._size_spin(400, self._screen_w)
        self._max_h = self._size_spin(260, self._screen_h)
        max_hint = QLabel(f"حداکثر: اندازه صفحه نمایش ({self._screen_w}×{self._screen_h})")
        max_hint.setObjectName("HintLabel")
        size_form.addRow("حداکثر عرض (خودکار)", self._max_w)
        size_form.addRow("حداکثر ارتفاع (خودکار)", self._max_h)
        size_form.addRow(max_hint)

        self._remember = QCheckBox("به‌خاطر سپردن اندازه دستی پنجره")
        size_form.addRow(self._remember)

        self._near_cursor = QCheckBox("باز شدن کنار نشانگر موس")
        size_form.addRow(self._near_cursor)

        font_group = QGroupBox("قلم و نمایش")
        font_form = QFormLayout(font_group)
        font_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        font_form.setHorizontalSpacing(16)
        font_form.setVerticalSpacing(12)

        self._font_size = QSpinBox()
        self._font_size.setRange(9, 28)
        self._font_size.setSuffix(" pt")
        font_form.addRow("اندازه فونت", self._font_size)

        self._font_family = QComboBox()
        self._font_family.addItem("خودکار (پیشنهادی)", "")
        installed = set(QFontDatabase.families())
        for name in FONT_CANDIDATES:
            if name in installed:
                self._font_family.addItem(name, name)
        for name in sorted(installed):
            if name.lower().startswith(("noto", "dejavu", "liberation", "ubuntu", "vazir")):
                if self._font_family.findData(name) < 0:
                    self._font_family.addItem(name, name)
        font_form.addRow("قلم", self._font_family)

        self._theme = QComboBox()
        self._theme.addItem("تاریک", "dark")
        self._theme.addItem("روشن", "light")
        font_form.addRow("تم", self._theme)

        self._rtl = QCheckBox("راست‌چین پیش‌فرض (RTL)")
        font_form.addRow(self._rtl)

        body_layout.addWidget(size_group)
        body_layout.addWidget(font_group)
        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll, stretch=1)

        hint = QLabel(
            "تغییرات از دفعه بعد که میانبر را بزنید اعمال می‌شود.\n"
            "اگر پنجره باز است، یک‌بار ببندید و دوباره Ctrl+Alt+Space بزنید."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("انصراف")
        buttons.accepted.connect(self._save_and_close)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self._auto_size.toggled.connect(self._toggle_auto_fields)

    def _toggle_auto_fields(self, enabled: bool) -> None:
        for widget in (self._max_w, self._max_h):
            widget.setEnabled(enabled)
        for widget in (self._fixed_w, self._fixed_h):
            widget.setEnabled(not enabled)

    def _load_values(self) -> None:
        s = self._settings
        self._auto_size.setChecked(s.auto_size)
        self._fixed_w.setValue(min(s.fixed_width, self._screen_w))
        self._fixed_h.setValue(min(s.fixed_height, self._screen_h))
        self._max_w.setValue(min(s.auto_max_width, self._screen_w))
        self._max_h.setValue(min(s.auto_max_height, self._screen_h))
        self._remember.setChecked(s.remember_geometry)
        self._near_cursor.setChecked(s.open_near_cursor)
        self._font_size.setValue(s.font_size)
        idx = self._font_family.findData(s.font_family)
        self._font_family.setCurrentIndex(max(0, idx))
        tidx = self._theme.findData(s.theme)
        self._theme.setCurrentIndex(max(0, tidx))
        self._rtl.setChecked(s.rtl_default)
        self._toggle_auto_fields(s.auto_size)

    def _on_theme_preview(self) -> None:
        mode = self._theme.currentData() or "dark"
        self._apply_theme(mode)

    def _save_and_close(self) -> None:
        self._settings = AppSettings(
            auto_size=self._auto_size.isChecked(),
            font_size=self._font_size.value(),
            font_family=self._font_family.currentData() or "",
            rtl_default=self._rtl.isChecked(),
            theme=self._theme.currentData() or "dark",
            remember_geometry=self._remember.isChecked(),
            fixed_width=self._fixed_w.value(),
            fixed_height=self._fixed_h.value(),
            auto_max_width=self._max_w.value(),
            auto_max_height=self._max_h.value(),
            open_near_cursor=self._near_cursor.isChecked(),
        )
        self._settings.save()
        self.accept()

    def _apply_theme(self, mode: str) -> None:
        palette = resolve_palette(mode)
        self.setStyleSheet(build_settings_stylesheet(palette))

    @property
    def settings(self) -> AppSettings:
        return self._settings
