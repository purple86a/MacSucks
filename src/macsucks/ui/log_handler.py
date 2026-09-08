"""Logging handler that feeds the settings UI."""

from __future__ import annotations

import logging
from typing import Callable

from macsucks.logging_config import make_formatter


class UiLogHandler(logging.Handler):
    def __init__(self, emit_callback: Callable[[str], None]) -> None:
        super().__init__()
        self._emit_callback = emit_callback
        self.setFormatter(make_formatter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._emit_callback(msg)
        except Exception:
            self.handleError(record)
