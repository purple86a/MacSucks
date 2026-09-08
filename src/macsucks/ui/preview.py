"""Preview helpers for offscreen UI screenshots."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from macsucks.config import AppConfig
from macsucks.ui.settings_window import SettingsWindow
from macsucks.ui.styles import build_stylesheet


def build_preview() -> SettingsWindow:
    app = QApplication.instance()
    if app is not None:
        app.setStyle("Fusion")
        app.setStyleSheet(build_stylesheet())

    config = AppConfig(hotkey="alt+c", api_key_verified=True)
    window = SettingsWindow(config)
    window.resize(500, 600)
    window.hotkey_label.setText("Alt + C")
    window.api_status.setText("API key verified successfully.")
    window.api_status.setObjectName("status_ok")
    style = window.api_status.style()
    if style is not None:
        style.unpolish(window.api_status)
        style.polish(window.api_status)
    return window
