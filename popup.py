"""macOS-style RTL popup for mixed Persian/English text."""

from __future__ import annotations

import re
import sys

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSettings,
    Qt,
    QTimer,
)
from PyQt6.QtGui import (
    QCursor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QKeySequence,
    QShortcut,
    QTextCursor,
    QTextDocument,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from theme import Palette, build_stylesheet, resolve_palette

FONT_CANDIDATES = (
    "Vazirmatn",
    "Noto Sans Arabic",
    "Iranian Sans",
    "Tahoma",
    "DejaVu Sans",
)

SETTINGS_ORG = "bidi-popup"
SETTINGS_APP = "bidi-popup"
RESIZE_MARGIN = 8
SHADOW_MARGIN = 16
MIN_WIDTH = 360
MIN_HEIGHT = 220

LEFT, RIGHT, TOP, BOTTOM = 1, 2, 4, 8


def pick_font(size: int) -> QFont:
    families = set(QFontDatabase.families())
    for name in FONT_CANDIDATES:
        if name in families:
            return QFont(name, size)
    return QFont("Sans Serif", size)


def looks_like_markdown(text: str) -> bool:
    if "```" in text:
        return True
    if re.search(r"^#{1,6}\s", text, re.MULTILINE):
        return True
    if re.search(r"^\s*[-*]\s", text, re.MULTILINE):
        return True
    if "**" in text or "__" in text:
        return True
    return False


class TrafficLight(QPushButton):
    """macOS-style window control with always-visible symbol."""

    def __init__(
        self,
        color: str,
        hover: str,
        icon: str,
        icon_color: str = "#4a4a4a",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._color = color
        self._hover = hover
        self._icon = icon
        self._icon_color = icon_color
        self._hover_icon_color = "#1a1a1a"
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._paint(color, icon_color)

    def _paint(self, bg: str, fg: str) -> None:
        self.setText(self._icon)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                border-radius: 7px;
                color: {fg};
                font-size: 11px;
                font-weight: bold;
                padding: 0;
                margin: 0;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
            }}
            """
        )

    def enterEvent(self, event) -> None:
        self._paint(self._hover, self._hover_icon_color)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._paint(self._color, self._icon_color)
        super().leaveEvent(event)


class MacTitleBar(QWidget):
    def __init__(self, popup: "Popup") -> None:
        super().__init__(popup)
        self.setObjectName("TitleBar")
        self._popup = popup
        self._dragging = False
        self._drag_pos = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 4)
        layout.setSpacing(8)

        lights = QHBoxLayout()
        lights.setSpacing(8)
        self._btn_close = TrafficLight("#ff5f57", "#ff3b30", "×", "#6b0000")
        self._btn_min = TrafficLight("#febc2e", "#f5a623", "−", "#6b4a00")
        self._btn_max = TrafficLight("#28c840", "#1faa34", "+", "#005000")
        self._btn_close.clicked.connect(popup.close)
        self._btn_min.clicked.connect(popup.showMinimized)
        self._btn_max.clicked.connect(popup.toggle_maximize)
        lights.addWidget(self._btn_close)
        lights.addWidget(self._btn_min)
        lights.addWidget(self._btn_max)
        layout.addLayout(lights)

        self._title = QLabel("Bidi Popup")
        self._title.setObjectName("TitleLabel")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title, stretch=1)

        tools = QHBoxLayout()
        tools.setSpacing(2)

        self._rtl_btn = QPushButton("RTL")
        self._rtl_btn.setObjectName("ToolButton")
        self._rtl_btn.setToolTip("Toggle text direction")
        self._rtl_btn.clicked.connect(popup.toggle_direction)
        tools.addWidget(self._rtl_btn)

        self._smaller_btn = QPushButton("A−")
        self._smaller_btn.setObjectName("ToolButton")
        self._smaller_btn.setToolTip("Smaller font")
        self._smaller_btn.clicked.connect(lambda: popup.adjust_font(-1))
        tools.addWidget(self._smaller_btn)

        self._larger_btn = QPushButton("A+")
        self._larger_btn.setObjectName("ToolButton")
        self._larger_btn.setToolTip("Larger font")
        self._larger_btn.clicked.connect(lambda: popup.adjust_font(1))
        tools.addWidget(self._larger_btn)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("ToolButton")
        self._copy_btn.clicked.connect(popup.copy_text)
        tools.addWidget(self._copy_btn)

        self._theme_btn = QPushButton("◐")
        self._theme_btn.setObjectName("ToolButton")
        self._theme_btn.setToolTip("Toggle light / dark theme")
        self._theme_btn.clicked.connect(popup.cycle_theme)
        tools.addWidget(self._theme_btn)

        layout.addLayout(tools)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._dragging and not self._popup._maximized:
            diff = event.globalPosition().toPoint() - self._drag_pos
            self._popup.move(self._popup.pos() + diff)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._popup.toggle_maximize()
        super().mouseDoubleClickEvent(event)


class ResizeRail(QWidget):
    """Transparent strip on the frame edge — always receives resize mouse events."""

    def __init__(self, popup: "Popup", edges: int) -> None:
        super().__init__(popup)
        self._popup = popup
        self._edges = edges
        self.setCursor(popup._cursor_for_edges(edges))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._popup._start_resize(self._edges, event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._popup._resizing:
            self._popup._apply_resize(event.globalPosition().toPoint())
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._popup._end_resize()
            event.accept()


class Popup(QWidget):
    def __init__(
        self,
        text: str = "",
        anchor: QPoint | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self._anchor = anchor
        self._rtl = self._settings.value("rtl", True, type=bool)
        theme = self._settings.value("theme", "dark", type=str)
        if theme == "auto":
            theme = "dark"
        self._theme_mode = theme
        self._font_size = self._settings.value("font_size", 12, type=int)
        self._maximized = False
        self._normal_geometry = QRect()
        self._resizing = False
        self._resize_edges = 0
        self._resize_origin = QPoint()
        self._geom_origin = QRect()

        self.setWindowTitle("Bidi Popup")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        self._frame = QFrame()
        self._frame.setObjectName("MacFrame")
        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        shadow = QGraphicsDropShadowEffect(self._frame)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        shadow.setColor(Qt.GlobalColor.black)
        self._frame.setGraphicsEffect(shadow)

        self._title_bar = MacTitleBar(self)
        frame_layout.addWidget(self._title_bar)

        self._box = QTextEdit()
        self._box.setObjectName("ContentBox")
        self._box.setReadOnly(True)
        self._box.installEventFilter(self)
        frame_layout.addWidget(self._box, stretch=1)

        self._find_bar = QWidget()
        self._find_bar.setObjectName("FindBar")
        find_layout = QHBoxLayout(self._find_bar)
        find_layout.setContentsMargins(10, 6, 10, 8)
        self._find_input = QLineEdit()
        self._find_input.setObjectName("FindInput")
        self._find_input.setPlaceholderText("Search…  (Enter = next, Shift+Enter = prev)")
        self._find_input.textChanged.connect(self._find_next)
        self._find_input.returnPressed.connect(self._find_next)
        find_layout.addWidget(self._find_input)
        self._find_bar.hide()
        frame_layout.addWidget(self._find_bar)

        outer.addWidget(self._frame)

        self._toast = QLabel(self._frame)
        self._toast.setObjectName("ToastLabel")
        self._toast.hide()
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._rails: list[ResizeRail] = []
        for edges in (LEFT, RIGHT, TOP, BOTTOM, LEFT | TOP, RIGHT | TOP, LEFT | BOTTOM, RIGHT | BOTTOM):
            self._rails.append(ResizeRail(self, edges))

        self._apply_theme()
        self._apply_font()
        self._apply_direction()
        self._set_content(text)

        self._register_shortcuts()
        self._restore_geometry(anchor)

    def _register_shortcuts(self) -> None:
        for seq, slot in (
            (QKeySequence("Escape"), self.close),
            (QKeySequence("Ctrl+C"), self.copy_text),
            (QKeySequence("Ctrl+F"), self.toggle_find),
            (QKeySequence("Ctrl+="), lambda: self.adjust_font(1)),
            (QKeySequence("Ctrl+-"), lambda: self.adjust_font(-1)),
        ):
            shortcut = QShortcut(seq, self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(slot)

    def _palette(self) -> Palette:
        return resolve_palette(self._theme_mode)

    def _apply_theme(self) -> None:
        palette = self._palette()
        self._frame.setStyleSheet(build_stylesheet(palette))
        effect = self._frame.graphicsEffect()
        if isinstance(effect, QGraphicsDropShadowEffect):
            from PyQt6.QtGui import QColor

            effect.setColor(QColor(palette.shadow))

    def cycle_theme(self) -> None:
        order = {"auto": "light", "light": "dark", "dark": "auto"}
        self._theme_mode = order.get(self._theme_mode, "auto")
        self._settings.setValue("theme", self._theme_mode)
        self._apply_theme()

    def _apply_font(self) -> None:
        self._font_size = max(9, min(28, self._font_size))
        self._box.setFont(pick_font(self._font_size))
        self._settings.setValue("font_size", self._font_size)

    def adjust_font(self, delta: int) -> None:
        self._font_size += delta
        self._apply_font()

    def _apply_direction(self) -> None:
        # Widget stays LTR so the editor fills the pane; only text blocks align right.
        self._box.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        if self._rtl:
            align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
            text_dir = Qt.LayoutDirection.RightToLeft
            self._title_bar._rtl_btn.setText("RTL")
        else:
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute
            text_dir = Qt.LayoutDirection.LeftToRight
            self._title_bar._rtl_btn.setText("LTR")

        option = QTextOption()
        option.setAlignment(align)
        option.setTextDirection(text_dir)
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        doc = self._box.document()
        doc.setDefaultTextOption(option)

        # Re-align existing blocks (setPlainText / setMarkdown resets per-block state).
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        block = doc.firstBlock()
        while block.isValid():
            cursor.setPosition(block.position())
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            fmt = cursor.blockFormat()
            fmt.setAlignment(align)
            cursor.setBlockFormat(fmt)
            block = block.next()
        cursor.endEditBlock()

    def toggle_direction(self) -> None:
        self._rtl = not self._rtl
        self._settings.setValue("rtl", self._rtl)
        self._apply_direction()

    def _set_content(self, text: str) -> None:
        if looks_like_markdown(text):
            self._box.setMarkdown(text)
        else:
            self._box.setPlainText(text)
        self._apply_direction()

    def set_text(self, text: str, anchor: QPoint | None = None) -> None:
        self._set_content(text)
        if anchor is not None:
            self._place_near(anchor)
        cursor = self._box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self._box.setTextCursor(cursor)
        self.show()
        self.raise_()
        self.activateWindow()

    def copy_text(self) -> None:
        QApplication.clipboard().setText(self._box.toPlainText())
        self._show_toast("Copied ✓")

    def _show_toast(self, message: str) -> None:
        self._toast.setText(message)
        self._toast.adjustSize()
        x = (self._frame.width() - self._toast.width()) // 2
        y = self._frame.height() - self._toast.height() - 20
        self._toast.move(max(12, x), max(12, y))
        self._toast.show()
        self._toast.raise_()
        QTimer.singleShot(1400, self._toast.hide)

    def toggle_find(self) -> None:
        if self._find_bar.isVisible():
            self._find_bar.hide()
            self._find_input.clear()
            self._box.setFocus()
        else:
            self._find_bar.show()
            self._find_input.setFocus()
            self._find_input.selectAll()

    def _find_next(self) -> None:
        needle = self._find_input.text()
        if not needle:
            return
        found = self._box.find(needle)
        if not found:
            cursor = self._box.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._box.setTextCursor(cursor)
            self._box.find(needle)

    def toggle_maximize(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return

        if self._maximized:
            self.setGeometry(self._normal_geometry)
            self._maximized = False
            self._title_bar._btn_max._icon = "+"
            self._title_bar._btn_max._paint(
                self._title_bar._btn_max._color,
                self._title_bar._btn_max._icon_color,
            )
        else:
            self._normal_geometry = self.geometry()
            geo = screen.availableGeometry()
            margin = 24
            self.setGeometry(
                geo.x() + margin,
                geo.y() + margin,
                geo.width() - margin * 2,
                geo.height() - margin * 2,
            )
            self._maximized = True
            self._title_bar._btn_max._icon = "⤢"
            self._title_bar._btn_max._paint(
                self._title_bar._btn_max._color,
                self._title_bar._btn_max._icon_color,
            )
        self._sync_resize_rails()

    def _restore_geometry(self, anchor: QPoint | None) -> None:
        saved = self._settings.value("geometry")
        if saved and not anchor:
            self.restoreGeometry(saved)
            return

        w = self._settings.value("width", 580, type=int)
        h = self._settings.value("height", 380, type=int)
        self.resize(w, h)

        if anchor is not None:
            self._place_near(anchor)
        else:
            self._center_on_screen()

    def _place_near(self, anchor: QPoint) -> None:
        screen = QGuiApplication.screenAt(anchor) or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = anchor.x() - self.width() // 2
        y = anchor.y() + 18
        x = max(geo.x() + 8, min(x, geo.right() - self.width() - 8))
        y = max(geo.y() + 8, min(y, geo.bottom() - self.height() - 8))
        self.move(x, y)

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

    def _sync_resize_rails(self) -> None:
        if self._maximized:
            for rail in self._rails:
                rail.hide()
            return

        fr = self._frame.geometry()
        m = RESIZE_MARGIN
        side_h = max(1, fr.height() - 2 * m)
        side_w = max(1, fr.width() - 2 * m)
        placements: dict[int, tuple[int, int, int, int]] = {
            LEFT: (fr.left() - m, fr.top() + m, 2 * m, side_h),
            RIGHT: (fr.right() - m + 1, fr.top() + m, 2 * m, side_h),
            TOP: (fr.left() + m, fr.top() - m, side_w, 2 * m),
            BOTTOM: (fr.left() + m, fr.bottom() - m + 1, side_w, 2 * m),
            LEFT | TOP: (fr.left() - m, fr.top() - m, 2 * m, 2 * m),
            RIGHT | TOP: (fr.right() - m + 1, fr.top() - m, 2 * m, 2 * m),
            LEFT | BOTTOM: (fr.left() - m, fr.bottom() - m + 1, 2 * m, 2 * m),
            RIGHT | BOTTOM: (fr.right() - m + 1, fr.bottom() - m + 1, 2 * m, 2 * m),
        }
        for rail in self._rails:
            rail.setGeometry(*placements[rail._edges])
            rail.show()
            rail.raise_()

    def _start_resize(self, edges: int, global_pos: QPoint) -> None:
        self._resizing = True
        self._resize_edges = edges
        self._resize_origin = global_pos
        self._geom_origin = self.geometry()
        self.grabMouse()

    def _apply_resize(self, global_pos: QPoint) -> None:
        if not self._resizing:
            return
        delta = global_pos - self._resize_origin
        geo = QRect(self._geom_origin)
        if self._resize_edges & RIGHT:
            geo.setWidth(max(MIN_WIDTH, self._geom_origin.width() + delta.x()))
        if self._resize_edges & BOTTOM:
            geo.setHeight(max(MIN_HEIGHT, self._geom_origin.height() + delta.y()))
        if self._resize_edges & LEFT:
            new_w = max(MIN_WIDTH, self._geom_origin.width() - delta.x())
            geo.setX(self._geom_origin.x() + self._geom_origin.width() - new_w)
            geo.setWidth(new_w)
        if self._resize_edges & TOP:
            new_h = max(MIN_HEIGHT, self._geom_origin.height() - delta.y())
            geo.setY(self._geom_origin.y() + self._geom_origin.height() - new_h)
            geo.setHeight(new_h)
        self.setGeometry(geo)

    def _end_resize(self) -> None:
        if not self._resizing:
            return
        self._resizing = False
        self._resize_edges = 0
        self.releaseMouse()
        self._sync_resize_rails()

    def _cursor_for_edges(self, edges: int) -> Qt.CursorShape:
        if edges in (LEFT | TOP, RIGHT | BOTTOM):
            return Qt.CursorShape.SizeFDiagCursor
        if edges in (RIGHT | TOP, LEFT | BOTTOM):
            return Qt.CursorShape.SizeBDiagCursor
        if edges in (LEFT, RIGHT):
            return Qt.CursorShape.SizeHorCursor
        if edges in (TOP, BOTTOM):
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mouseMoveEvent(self, event) -> None:
        if self._resizing:
            self._apply_resize(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._resizing:
            self._end_resize()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_resize_rails()

    def eventFilter(self, obj, event) -> bool:
        if obj is self._box and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.close()
                return True
            if (
                event.key() == Qt.Key.Key_Return
                and self._find_bar.isVisible()
                and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            ):
                self._find_input.setFocus()
                self._find_prev()
                return True

        return super().eventFilter(obj, event)

    def _find_prev(self) -> None:
        needle = self._find_input.text()
        if not needle:
            return
        flags = QTextDocument.FindFlag.FindBackward
        found = self._box.find(needle, flags)
        if not found:
            cursor = self._box.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._box.setTextCursor(cursor)
            self._box.find(needle, flags)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if not self._maximized:
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("width", self.width())
            self._settings.setValue("height", self.height())
        super().closeEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_resize_rails()
        self._box.setFocus()


def read_input_text() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.read()
    if len(sys.argv) > 1:
        return sys.argv[1]
    return ""


def main() -> int:
    app = QApplication(sys.argv)
    anchor = QCursor.pos()
    window = Popup(read_input_text(), anchor=anchor)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
