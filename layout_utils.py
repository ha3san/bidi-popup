"""Compute popup dimensions from rendered content."""

from __future__ import annotations

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QFontMetrics, QGuiApplication, QTextDocument

MIN_WIDTH = 360
MIN_HEIGHT = 220
OUTER_MARGIN = 32  # shadow layout margins (16 * 2)
CONTENT_PAD = 28


def _screen_limits(anchor_x: int | None = None) -> tuple[int, int]:
    screen = QGuiApplication.primaryScreen()
    if anchor_x is not None:
        screen = QGuiApplication.screenAt(QPoint(anchor_x, 0)) or screen
    if screen is None:
        return 1200, 900
    geo = screen.availableGeometry()
    return int(geo.width() * 0.88), int(geo.height() * 0.88)


def compute_popup_size(
    editor: QTextEdit,
    *,
    settings: AppSettings,
    title_bar_height: int = 46,
    find_bar_height: int = 0,
    anchor_x: int | None = None,
) -> tuple[int, int]:
    """Return (width, height) in pixels for the outer popup widget."""
    doc: QTextDocument = editor.document()
    font = editor.font()
    fm = QFontMetrics(font)

    screen_w, screen_h = _screen_limits(anchor_x)
    max_w = min(settings.auto_max_width, screen_w)
    max_h = min(settings.auto_max_height, screen_h)

    plain = editor.toPlainText()
    lines = plain.splitlines() or [""]
    longest = max((fm.horizontalAdvance(line) for line in lines), default=200)
    natural_w = longest + CONTENT_PAD * 2

    chrome_w = OUTER_MARGIN + 16
    content_w = max(240, min(int(natural_w), max_w - chrome_w))

    doc.setTextWidth(float(content_w))
    doc_h = int(doc.size().height()) + CONTENT_PAD

    line_count = len(lines)
    if line_count <= 3:
        doc_h = min(doc_h, int(fm.lineSpacing() * line_count + CONTENT_PAD + 8))
    elif line_count <= 8:
        doc_h = min(doc_h, int(fm.lineSpacing() * (line_count + 0.5) + CONTENT_PAD))

    chrome_h = OUTER_MARGIN + title_bar_height + find_bar_height
    height = max(MIN_HEIGHT, min(doc_h + chrome_h, max_h))
    width = max(MIN_WIDTH, min(content_w + chrome_w, max_w))

    return width, height
