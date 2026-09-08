"""System tray icon and menu."""

from __future__ import annotations

import logging

from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from macsucks.assets_util import asset_path

logger = logging.getLogger(__name__)


def app_icon_path():
    return asset_path("app.ico")


def load_app_icon() -> QIcon:
    path = app_icon_path()
    if path is not None:
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon

    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#8A2BE2"))
    painter.setPen(QColor("#6F22B8"))
    painter.drawRoundedRect(8, 8, 48, 48, 10, 10)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPointSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x84, "M")
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None) -> None:
        super().__init__(load_app_icon(), parent)
        self._menu = QMenu()
        self.action_settings = QAction("Open Settings", self)
        self.action_capture = QAction("Capture Region", self)
        self.action_check_updates = QAction("Check for Updates", self)
        self.action_quit = QAction("Quit", self)
        self._menu.addAction(self.action_settings)
        self._menu.addAction(self.action_capture)
        self._menu.addSeparator()
        self._menu.addAction(self.action_check_updates)
        self._menu.addSeparator()
        self._menu.addAction(self.action_quit)
        self.setContextMenu(self._menu)
        self.setToolTip("MacSucks — Screen Region OCR")

    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information) -> None:
        if self.isSystemTrayAvailable():
            self.showMessage(title, message, icon, 3000)
