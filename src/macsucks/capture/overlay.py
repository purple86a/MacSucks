"""Fullscreen dim overlay with region selection."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from macsucks.capture.screenshot import Region


@dataclass(frozen=True)
class SelectionResult:
    region: Region
    cancelled: bool = False


class SelectionOverlay(QWidget):
    completed = Signal(object)

    DIM_ALPHA = 115
    ACCENT = QColor(138, 43, 226)  # neon purple RGB(138, 43, 226)

    def __init__(self) -> None:
        super().__init__()
        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._screen_pixmaps: dict[int, QPixmap] = {}
        self._virtual_geometry = QRect()
        self._setup_window()
        self._capture_screens()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        screens = QGuiApplication.screens()
        if not screens:
            return
        left = min(s.geometry().left() for s in screens)
        top = min(s.geometry().top() for s in screens)
        right = max(s.geometry().right() for s in screens)
        bottom = max(s.geometry().bottom() for s in screens)
        self._virtual_geometry = QRect(left, top, right - left + 1, bottom - top + 1)
        self.setGeometry(self._virtual_geometry)

    def _capture_screens(self) -> None:
        for screen in QGuiApplication.screens():
            self._screen_pixmaps[id(screen)] = screen.grabWindow(0)

    def _selection_rect(self) -> QRect | None:
        if self._origin is None or self._current is None:
            return None
        return QRect(self._origin, self._current).normalized()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            for screen in QGuiApplication.screens():
                geom = screen.geometry()
                local_x = geom.left() - self._virtual_geometry.left()
                local_y = geom.top() - self._virtual_geometry.top()
                pixmap = self._screen_pixmaps.get(id(screen))
                if pixmap and not pixmap.isNull():
                    painter.drawPixmap(local_x, local_y, pixmap)

            painter.fillRect(self.rect(), QColor(0, 0, 0, self.DIM_ALPHA))

            rect = self._selection_rect()
            if rect and rect.width() > 0 and rect.height() > 0:
                for screen in QGuiApplication.screens():
                    geom = screen.geometry()
                    local_x = geom.left() - self._virtual_geometry.left()
                    local_y = geom.top() - self._virtual_geometry.top()
                    pixmap = self._screen_pixmaps.get(id(screen))
                    if not pixmap or pixmap.isNull():
                        continue
                    screen_local = QRect(local_x, local_y, geom.width(), geom.height())
                    intersection = rect.intersected(screen_local)
                    if intersection.isEmpty():
                        continue
                    src = QRect(
                        intersection.left() - local_x,
                        intersection.top() - local_y,
                        intersection.width(),
                        intersection.height(),
                    )
                    painter.drawPixmap(intersection, pixmap, src)

                pen = QPen(self.ACCENT, 2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
        finally:
            painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._origin is not None:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        self._current = event.position().toPoint()
        rect = self._selection_rect()
        if rect is None or rect.width() < 3 or rect.height() < 3:
            self._finish(cancelled=True)
            return
        global_left = self._virtual_geometry.left() + rect.left()
        global_top = self._virtual_geometry.top() + rect.top()
        region = Region(global_left, global_top, rect.width(), rect.height())
        self._finish(region=region)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._finish(cancelled=True)

    def _finish(self, region: Region | None = None, cancelled: bool = False) -> None:
        result = SelectionResult(
            region=region or Region(0, 0, 0, 0),
            cancelled=cancelled or region is None,
        )
        self.hide()
        self.completed.emit(result)
        self.deleteLater()

    @classmethod
    def start(cls, parent=None) -> SelectionOverlay:
        overlay = cls()
        if parent:
            overlay.setParent(parent)
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()
        overlay.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        return overlay
