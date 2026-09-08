"""Occasional mascot GIF overlay in the settings window."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QLabel, QWidget

from macsucks.assets_util import asset_path

MASCOT_INTERVAL_MS = 5 * 60 * 1000
MASCOT_DISPLAY_MS = 4500
MASCOT_SIZE = 88


class MascotOverlay(QLabel):
    """Plays pompompurin in the bottom-right when settings is open."""

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self._host = host
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(MASCOT_SIZE, MASCOT_SIZE)
        self.hide()

        self._movie: QMovie | None = None
        path = asset_path("mascot.gif")
        if path is not None:
            self._movie = QMovie(str(path))
            self._movie.setScaledSize(self.size())
            self.setMovie(self._movie)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._stop)

        self._interval = QTimer(self)
        self._interval.setInterval(MASCOT_INTERVAL_MS)
        self._interval.timeout.connect(self.play)

        host.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001
        if obj is self._host and event.type() == QEvent.Type.Resize:
            self._reposition()
        return super().eventFilter(obj, event)

    def on_host_shown(self) -> None:
        self.play()
        if not self._interval.isActive():
            self._interval.start()

    def on_host_hidden(self) -> None:
        self._interval.stop()
        self._stop()

    def play(self) -> None:
        if self._movie is None or not self._host.isVisible():
            return
        self._reposition()
        self.show()
        self.raise_()
        self._movie.start()
        self._hide_timer.start(MASCOT_DISPLAY_MS)

    def _stop(self) -> None:
        if self._movie is not None:
            self._movie.stop()
        self.hide()

    def _reposition(self) -> None:
        margin = 10
        self.move(
            self._host.width() - self.width() - margin,
            self._host.height() - self.height() - margin,
        )
