"""Application orchestrator."""

from __future__ import annotations

import logging
import sys
import threading

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from macsucks.capture.overlay import SelectionOverlay
from macsucks.capture.screenshot import capture_region
from macsucks.config import AppConfig
from macsucks.hotkeys.manager import HotkeyManager
from macsucks.ocr.worker import OcrWorker
from macsucks.secrets import get_api_key, has_api_key
from macsucks.startup.registry import enable_startup, is_startup_enabled
from macsucks.tray import TrayIcon
from macsucks.ui.log_handler import UiLogHandler
from macsucks.ui.settings_window import SettingsWindow
from macsucks.ui.toast import AppToast
from macsucks.updater.checker import check_for_updates, utc_now_iso
from macsucks.updater.installer import default_msi_path, download_msi, install_msi

logger = logging.getLogger(__name__)

UPDATE_INTERVAL_MS = 2 * 60 * 60 * 1000


class AppController:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.config = AppConfig.load()
        self.hotkeys = HotkeyManager(parent=app)
        self.tray = TrayIcon()
        self.settings = SettingsWindow(self.config)
        self._ocr_worker: OcrWorker | None = None
        self._overlay: SelectionOverlay | None = None
        self._toast = AppToast()

        self._wire_signals()
        self._setup_logging()
        self._register_hotkey()
        self._ensure_startup()
        self._setup_update_timer()

        self.tray.show()
        if not has_api_key():
            self.settings.show()
            self.settings.raise_()
            self.settings.activateWindow()
        elif self.config.api_key_verified or has_api_key():
            # Keep settings available from tray; ensure status isn't left on Verifying.
            pass

        QTimer.singleShot(2000, lambda: self._check_updates(manual=False))

    def _wire_signals(self) -> None:
        self.tray.action_settings.triggered.connect(self.settings.show)
        self.tray.action_capture.triggered.connect(self.start_capture)
        self.tray.action_check_updates.triggered.connect(lambda: self._check_updates(manual=True))
        self.tray.action_quit.triggered.connect(self.quit)
        self.settings.capture_requested.connect(self.start_capture)
        self.settings.hotkey_changed.connect(self._register_hotkey)
        self.settings.check_updates_requested.connect(lambda _: self._check_updates(manual=True))

    def _setup_logging(self) -> None:
        from macsucks.logging_config import make_formatter

        root = logging.getLogger()
        root.setLevel(logging.DEBUG if self.config.debug_logging else logging.INFO)
        formatter = make_formatter()

        # Avoid duplicate handlers on re-init.
        for existing in list(root.handlers):
            if isinstance(existing, (UiLogHandler, logging.StreamHandler)):
                root.removeHandler(existing)

        ui_handler = UiLogHandler(self.settings.append_log)
        ui_handler.setLevel(logging.DEBUG)
        ui_handler.setFormatter(formatter)
        root.addHandler(ui_handler)

        stream = logging.StreamHandler()
        stream.setLevel(logging.DEBUG if self.config.debug_logging else logging.INFO)
        stream.setFormatter(formatter)
        root.addHandler(stream)
        logger.info("MacSucks started")

    def _register_hotkey(self, _combo: str | None = None) -> None:
        combo = _combo or self.config.hotkey
        if _combo:
            self.config.hotkey = _combo
        try:
            self.hotkeys.register(combo, self.start_capture)
            logger.info("Global shortcut active: %s", combo)
        except Exception as exc:
            logger.error("Hotkey registration failed: %s", exc)
            self._toast.show_error(
                "Could not register shortcut. Use Capture from tray menu."
            )

    def _ensure_startup(self) -> None:
        if self.config.startup_enabled and not is_startup_enabled():
            try:
                enable_startup()
            except Exception as exc:
                logger.warning("Could not enable startup: %s", exc)

    def _setup_update_timer(self) -> None:
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(lambda: self._check_updates(manual=False))
        self._update_timer.start(UPDATE_INTERVAL_MS)

    def start_capture(self) -> None:
        if self._overlay is not None:
            return
        if not has_api_key():
            self._toast.show_error("Add your LlamaCloud API key in Settings first.")
            self.settings.show()
            return
        logger.info("Capture overlay opened")
        self._overlay = SelectionOverlay.start()
        self._overlay.completed.connect(self._on_selection_done)

    def _on_selection_done(self, result) -> None:
        import time

        self._overlay = None
        if result.cancelled:
            logger.info("Selection cancelled")
            return
        try:
            shot_start = time.perf_counter()
            png_bytes = capture_region(result.region)
            shot_ms = (time.perf_counter() - shot_start) * 1000
            logger.info(
                "Screenshot captured in %.0f ms (%dx%d, %d bytes)",
                shot_ms,
                result.region.width,
                result.region.height,
                len(png_bytes),
            )
        except Exception as exc:
            logger.error("Screenshot failed: %s", exc)
            self._toast.show_error(f"Capture failed: {exc}")
            return

        api_key = get_api_key()
        if not api_key:
            return

        logger.info("Starting OCR worker (tier=%s)", self.config.parse_tier)
        self._toast.show_processing("Extracting text…")
        self._ocr_worker = OcrWorker(
            api_key,
            png_bytes,
            parse_tier=self.config.parse_tier,
        )
        self._ocr_worker.finished_ok.connect(self._on_ocr_ok)
        self._ocr_worker.finished_error.connect(self._on_ocr_error)
        self._ocr_worker.start()

    def _on_ocr_ok(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        preview = text[:80] + ("…" if len(text) > 80 else "")
        logger.info("Copied to clipboard: %s", preview)
        self._toast.show_success("Text copied to clipboard.")

    def _on_ocr_error(self, message: str, quota_exceeded: bool) -> None:
        logger.error("OCR error: %s", message)
        if quota_exceeded:
            self.settings.show_quota_warning(message)
        self._toast.show_error(message)

    def _check_updates(self, *, manual: bool) -> None:
        if manual:
            self.settings.start_update_cooldown()

        def work() -> None:
            info = check_for_updates()
            ts = utc_now_iso()

            def finish() -> None:
                self.settings.set_last_update_check(ts)
                if info is None:
                    msg = "Could not check for updates (repo not configured or offline)."
                    if manual:
                        self.settings.set_update_message(msg, error=True)
                    return
                if not info.update_available:
                    msg = f"You are on the latest version ({info.current_version})."
                    if manual:
                        self.settings.set_update_message(msg)
                    return
                if not info.download_url:
                    self.settings.set_update_message(
                        "Update available but no MSI asset found on release.",
                        error=True,
                    )
                    return
                self._prompt_update(info.latest_version, info.download_url, info.release_notes)

            QTimer.singleShot(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def _prompt_update(self, version: str, url: str, notes: str) -> None:
        box = QMessageBox(self.settings)
        box.setWindowTitle("Update Available")
        box.setText(f"MacSucks v{version} is available.")
        box.setInformativeText(notes[:500] if notes else "Download and install now?")
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        def download_and_install() -> None:
            try:
                dest = default_msi_path(version)
                download_msi(url, dest)
                QTimer.singleShot(0, lambda: install_msi(dest))
            except Exception as exc:
                logger.error("Update download failed: %s", exc)
                QTimer.singleShot(
                    0,
                    lambda: self.settings.set_update_message(f"Update failed: {exc}", error=True),
                )

        self.settings.set_update_message("Downloading update…")
        threading.Thread(target=download_and_install, daemon=True).start()

    def quit(self) -> None:
        self._toast.hide_toast()
        self.hotkeys.unregister()
        self.app.quit()
