"""Global hotkey registration with Qt-safe callback marshaling."""

from __future__ import annotations

import logging
from typing import Any, Callable

import keyboard
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class _HotkeyBridge(QObject):
    triggered = Signal()


class HotkeyManager:
    def __init__(self, parent: QObject | None = None) -> None:
        self._hotkey: str | None = None
        self._hook: Any = None
        self._callback: Callable[[], None] | None = None
        self._bridge = _HotkeyBridge(parent)
        self._bridge.triggered.connect(self._dispatch)

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        self.unregister()
        self._hotkey = hotkey
        self._callback = callback
        try:
            # keyboard fires from a non-Qt thread; bridge signal marshals to UI thread.
            self._hook = keyboard.add_hotkey(hotkey, self._bridge.triggered.emit, suppress=False)
            logger.info("Registered hotkey: %s", hotkey)
        except Exception as exc:
            self._hook = None
            self._hotkey = None
            self._callback = None
            logger.error("Failed to register hotkey %s: %s", hotkey, exc)
            raise

    def _dispatch(self) -> None:
        if self._callback:
            self._callback()

    def unregister(self) -> None:
        if self._hook is not None:
            try:
                keyboard.remove_hotkey(self._hook)
            except (KeyError, ValueError, AttributeError) as exc:
                logger.debug("Hotkey handle remove failed: %s", exc)
            self._hook = None
        elif self._hotkey:
            try:
                keyboard.remove_hotkey(self._hotkey)
            except (KeyError, ValueError):
                pass
        self._hotkey = None

    @staticmethod
    def format_display(hotkey: str) -> str:
        parts = hotkey.split("+")
        return " + ".join(p.capitalize() for p in parts)
