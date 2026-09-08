"""Settings window with API key, shortcut, logs, and updates."""

from __future__ import annotations

import logging
import threading
from datetime import datetime

import keyboard
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from macsucks import __version__
from macsucks.config import (
    PARSE_TIER_IDS,
    PARSE_TIERS,
    AppConfig,
    parse_tier_label,
)
from macsucks.hotkeys.manager import HotkeyManager
from macsucks.monitor.resources import ResourceMonitor
from macsucks.secrets import get_api_key, has_api_key
from macsucks.startup.registry import disable_startup, enable_startup, is_startup_enabled
from macsucks.ui.mascot import MascotOverlay
from macsucks.ui.title_bar import TitleBar

logger = logging.getLogger(__name__)

MANUAL_UPDATE_COOLDOWN_SEC = 60
SPACE = 12
PAD = 4


def _refresh_style(widget: QWidget) -> None:
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def _wrap_scroll(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setObjectName("settingsScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(content)
    return scroll


class _NoWheelComboBox(QComboBox):
    """Ignore mouse-wheel so scrolling the settings page can't change the value."""

    def wheelEvent(self, event) -> None:  # noqa: ANN001
        event.ignore()


class SettingsWindow(QWidget):
    api_key_saved = Signal(str)
    hotkey_changed = Signal(str)
    startup_toggled = Signal(bool)
    check_updates_requested = Signal(bool)
    capture_requested = Signal()
    _verification_finished = Signal(bool, str)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._recording_hotkey = False
        self._update_cooldown = 0
        self._resource_monitor = ResourceMonitor()
        self._save_btn: QPushButton | None = None
        self._verification_finished.connect(self._on_verification_finished)
        self._setup_ui()
        self._resource_timer = QTimer(self)
        self._resource_timer.timeout.connect(self._refresh_resources)
        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.timeout.connect(self._tick_update_cooldown)

    def _setup_ui(self) -> None:
        self.setWindowTitle("MacSucks Settings")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("settingsWindow")
        self.setMinimumSize(480, 560)
        self.resize(500, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self._title_bar = TitleBar("MacSucks Settings", self)
        self._title_bar.close_requested.connect(self.hide)
        self._title_bar.minimize_requested.connect(self.showMinimized)
        root.addWidget(self._title_bar)

        body = QVBoxLayout()
        body.setContentsMargins(16, 8, 12, 12)
        body.setSpacing(0)
        tabs = QTabWidget()
        body.addWidget(tabs)
        root.addLayout(body)

        tabs.addTab(self._build_general_tab(), "General")
        tabs.addTab(self._build_updates_tab(), "Updates")
        tabs.addTab(self._build_logs_tab(), "Debug Log")

        self._refresh_resources()
        self._sync_startup_checkbox()
        self._mascot = MascotOverlay(self)

    def _build_general_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, PAD, 8, PAD)
        layout.setSpacing(SPACE)

        api_group = QGroupBox("LlamaCloud API Key")
        api_group.setObjectName("firstSection")
        api_layout = QVBoxLayout(api_group)
        api_layout.setContentsMargins(0, 8, 0, 4)
        api_layout.setSpacing(8)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("llx-...")
        saved = get_api_key()
        if saved:
            self.api_key_input.setPlaceholderText("•••••••• (saved — enter new key to replace)")
        self.api_status = QLabel("")
        self.api_status.setObjectName("muted")
        self.api_status.setWordWrap(True)
        self._save_btn = QPushButton("Save & Verify")
        self._save_btn.setObjectName("primary")
        self._save_btn.clicked.connect(self._on_save_api_key)
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self._save_btn)
        api_layout.addWidget(self.api_status)
        if self.config.api_key_verified or has_api_key():
            self._set_api_status("API key saved", error=False)
        layout.addWidget(api_group)

        ocr_group = QGroupBox("OCR Mode")
        ocr_layout = QVBoxLayout(ocr_group)
        ocr_layout.setContentsMargins(0, 8, 0, 4)
        ocr_layout.setSpacing(8)
        self.parse_tier_combo = _NoWheelComboBox()
        for tier_id, _name, _credits in PARSE_TIERS:
            self.parse_tier_combo.addItem(parse_tier_label(tier_id), tier_id)
        self._sync_parse_tier_combo()
        self.parse_tier_combo.activated.connect(self._on_parse_tier_activated)
        ocr_hint = QLabel(
            "Credits shown are from public LlamaCloud pricing and may be outdated. "
            "MacSucks is not affiliated with LlamaIndex — check your LlamaCloud dashboard for live rates."
        )
        ocr_hint.setObjectName("muted")
        ocr_hint.setWordWrap(True)
        ocr_layout.addWidget(self.parse_tier_combo)
        ocr_layout.addWidget(ocr_hint)
        layout.addWidget(ocr_group)

        shortcut_group = QGroupBox("Capture Shortcut")
        shortcut_layout = QVBoxLayout(shortcut_group)
        shortcut_layout.setContentsMargins(0, 8, 0, 4)
        shortcut_layout.setSpacing(8)
        self.hotkey_label = QLabel(HotkeyManager.format_display(self.config.hotkey))
        self.hotkey_label.setObjectName("hotkey_value")
        record_btn = QPushButton("Record Shortcut")
        record_btn.clicked.connect(self._start_hotkey_record)
        capture_btn = QPushButton("Capture Now")
        capture_btn.clicked.connect(self.capture_requested.emit)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(record_btn)
        row.addWidget(capture_btn)
        self.hotkey_hint = QLabel("Press Record, then your key combo. Esc cancels.")
        self.hotkey_hint.setObjectName("muted")
        self.hotkey_hint.setWordWrap(True)
        shortcut_layout.addWidget(self.hotkey_label)
        shortcut_layout.addLayout(row)
        shortcut_layout.addWidget(self.hotkey_hint)
        layout.addWidget(shortcut_group)

        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout(startup_group)
        startup_layout.setContentsMargins(0, 8, 0, 4)
        startup_layout.setSpacing(8)
        self.startup_checkbox = QCheckBox("Run at Windows login")
        self.startup_checkbox.toggled.connect(self._on_startup_toggled)
        startup_layout.addWidget(self.startup_checkbox)
        layout.addWidget(startup_group)

        resource_group = QGroupBox("App Resources")
        resource_layout = QFormLayout(resource_group)
        resource_layout.setContentsMargins(0, 8, 0, 4)
        resource_layout.setHorizontalSpacing(SPACE)
        resource_layout.setVerticalSpacing(6)
        self.cpu_label = QLabel("—")
        self.ram_label = QLabel("—")
        resource_layout.addRow("CPU", self.cpu_label)
        resource_layout.addRow("RAM", self.ram_label)
        layout.addWidget(resource_group)

        layout.addStretch(1)
        return _wrap_scroll(content)

    def _build_updates_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, PAD, 8, PAD)
        layout.setSpacing(SPACE)

        info_group = QGroupBox("Version")
        info_group.setObjectName("firstSection")
        info_layout = QFormLayout(info_group)
        info_layout.setContentsMargins(0, 8, 0, 4)
        info_layout.setHorizontalSpacing(SPACE)
        info_layout.setVerticalSpacing(6)
        self.version_label = QLabel(__version__)
        self.last_check_label = QLabel(self.config.last_update_check or "Never")
        info_layout.addRow("Installed", self.version_label)
        info_layout.addRow("Last check", self.last_check_label)
        layout.addWidget(info_group)

        update_group = QGroupBox("Updates")
        update_layout = QVBoxLayout(update_group)
        update_layout.setContentsMargins(0, 8, 0, 4)
        update_layout.setSpacing(8)
        self.check_updates_btn = QPushButton("Check for Updates")
        self.check_updates_btn.clicked.connect(lambda: self.check_updates_requested.emit(True))
        self.update_status = QLabel("")
        self.update_status.setObjectName("muted")
        self.update_status.setWordWrap(True)
        update_layout.addWidget(self.check_updates_btn)
        update_layout.addWidget(self.update_status)
        layout.addWidget(update_group)
        layout.addStretch(1)
        return _wrap_scroll(content)

    def _build_logs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, PAD, 0, PAD)
        layout.setSpacing(8)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(280)
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_view.clear)
        layout.addWidget(self.log_view)
        layout.addWidget(clear_btn)
        return widget

    def append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._resource_timer.start(3000)
        self._refresh_resources()
        self._sync_parse_tier_combo()
        self._mascot.on_host_shown()

    def hideEvent(self, event) -> None:  # noqa: ANN001
        self._mascot.on_host_hidden()
        super().hideEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._resource_timer.stop()
        self._mascot.on_host_hidden()
        event.ignore()
        self.hide()

    def _refresh_resources(self) -> None:
        cpu, ram = self._resource_monitor.sample()
        self.cpu_label.setText(f"{cpu:.1f}%")
        self.ram_label.setText(f"{ram:.1f} MB")

    def _sync_startup_checkbox(self) -> None:
        self.startup_checkbox.blockSignals(True)
        self.startup_checkbox.setChecked(is_startup_enabled())
        self.startup_checkbox.blockSignals(False)

    def _on_save_api_key(self) -> None:
        key = self.api_key_input.text().strip()
        if not key and not has_api_key():
            self._set_api_status("Enter an API key.", error=True)
            return
        if not key:
            self._set_api_status("No changes — existing key kept.", error=False)
            return

        self.api_status.setText("Verifying…")
        self.api_status.setObjectName("muted")
        _refresh_style(self.api_status)
        if self._save_btn is not None:
            self._save_btn.setEnabled(False)

        def work() -> None:
            from macsucks.ocr.validator import validate_api_key
            from macsucks.secrets import set_api_key

            ok = False
            message = "Verification failed."
            try:
                ok, message = validate_api_key(key)
                if ok:
                    set_api_key(key)
                    self.config.api_key_verified = True
                    self.config.save()
            except Exception as exc:
                logger.exception("API key validation crashed")
                ok = False
                message = str(exc)
            self._verification_finished.emit(ok, message)

        threading.Thread(target=work, daemon=True).start()

    def _on_verification_finished(self, ok: bool, message: str) -> None:
        if self._save_btn is not None:
            self._save_btn.setEnabled(True)
        if ok:
            self.api_key_input.clear()
            self.api_key_input.setPlaceholderText("•••••••• (saved — enter new key to replace)")
            self._set_api_status(message, error=False)
            self.api_key_saved.emit("saved")
        else:
            self._set_api_status(message, error=True)

    def _set_api_status(self, message: str, *, error: bool) -> None:
        self.api_status.setText(message)
        self.api_status.setObjectName("status_err" if error else "status_ok")
        _refresh_style(self.api_status)

    def show_quota_warning(self, message: str) -> None:
        self._set_api_status(message, error=True)
        QMessageBox.warning(self, "LlamaCloud Usage Limit", message)

    def _start_hotkey_record(self) -> None:
        if self._recording_hotkey:
            return
        self._recording_hotkey = True
        self.hotkey_hint.setText("Press key combination now… (Esc to cancel)")

        def record() -> None:
            try:
                combo = keyboard.read_hotkey(suppress=False)
                if combo and combo != "esc":
                    QTimer.singleShot(0, self, lambda: self._apply_hotkey(combo))
                else:
                    QTimer.singleShot(0, self, self._cancel_hotkey_record)
            except Exception as exc:
                logger.error("Hotkey record failed: %s", exc)
                QTimer.singleShot(0, self, self._cancel_hotkey_record)

        threading.Thread(target=record, daemon=True).start()

    def _apply_hotkey(self, combo: str) -> None:
        self._recording_hotkey = False
        self.config.hotkey = combo
        self.config.save()
        self.hotkey_label.setText(HotkeyManager.format_display(combo))
        self.hotkey_hint.setText("Shortcut updated.")
        self.hotkey_changed.emit(combo)

    def _cancel_hotkey_record(self) -> None:
        self._recording_hotkey = False
        self.hotkey_hint.setText("Recording cancelled.")

    def _sync_parse_tier_combo(self) -> None:
        tier = self.config.parse_tier if self.config.parse_tier in PARSE_TIER_IDS else "fast"
        idx = self.parse_tier_combo.findData(tier)
        self.parse_tier_combo.blockSignals(True)
        self.parse_tier_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.parse_tier_combo.blockSignals(False)

    def _on_parse_tier_activated(self, index: int) -> None:
        tier = self.parse_tier_combo.itemData(index)
        if tier is None:
            return
        tier_id = str(tier)
        if tier_id not in PARSE_TIER_IDS:
            return
        self.config.parse_tier = tier_id
        self.config.save()
        logger.info("OCR parse tier saved: %s", tier_id)

    def _on_startup_toggled(self, checked: bool) -> None:
        try:
            if checked:
                enable_startup()
            else:
                disable_startup()
            self.config.startup_enabled = checked
            self.config.save()
            self.startup_toggled.emit(checked)
        except Exception as exc:
            logger.error("Startup toggle failed: %s", exc)
            QMessageBox.warning(self, "Startup", f"Could not update startup setting:\n{exc}")
            self._sync_startup_checkbox()

    def start_update_cooldown(self) -> None:
        self._update_cooldown = MANUAL_UPDATE_COOLDOWN_SEC
        self.check_updates_btn.setEnabled(False)
        self._update_cooldown_label()
        self._cooldown_timer.start(1000)

    def _tick_update_cooldown(self) -> None:
        self._update_cooldown -= 1
        if self._update_cooldown <= 0:
            self._cooldown_timer.stop()
            self.check_updates_btn.setEnabled(True)
            self.update_status.setText("")
        else:
            self._update_cooldown_label()

    def _update_cooldown_label(self) -> None:
        self.update_status.setText(f"Wait {self._update_cooldown}s before checking again.")

    def set_last_update_check(self, iso_timestamp: str) -> None:
        self.config.last_update_check = iso_timestamp
        self.config.save()
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            self.last_check_label.setText(dt.strftime("%Y-%m-%d %H:%M UTC"))
        except ValueError:
            self.last_check_label.setText(iso_timestamp)

    def set_update_message(self, message: str, *, error: bool = False) -> None:
        self.update_status.setText(message)
        self.update_status.setObjectName("status_err" if error else "muted")
        _refresh_style(self.update_status)
