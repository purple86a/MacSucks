"""Custom frameless title bar matching app theme."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from macsucks.tray import load_app_icon


class TitleBar(QWidget):
    close_requested = Signal()
    minimize_requested = Signal()

    def __init__(self, title: str = "MacSucks", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(8)

        icon = QLabel()
        pixmap = load_app_icon().pixmap(18, 18)
        icon.setPixmap(pixmap)
        icon.setFixedSize(18, 18)

        self._title = QLabel(title)
        self._title.setObjectName("titleBarLabel")

        layout.addWidget(icon)
        layout.addWidget(self._title)
        layout.addStretch()

        self._min_btn = QPushButton("─")
        self._min_btn.setObjectName("titleBarBtn")
        self._min_btn.setFixedSize(36, 28)
        self._min_btn.clicked.connect(self.minimize_requested.emit)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("titleBarCloseBtn")
        self._close_btn.setFixedSize(36, 28)
        self._close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self._min_btn)
        layout.addWidget(self._close_btn)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)
