"""Floating GIF toasts — same layout for processing / success / error."""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QMovie
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from macsucks.assets_util import asset_path


class ToastKind(str, Enum):
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


_GIF_FILES = {
    ToastKind.PROCESSING: "processing.gif",
    ToastKind.SUCCESS: "success.gif",
    ToastKind.ERROR: "error.gif",
}

_DEFAULT_TIMEOUT_MS = {
    ToastKind.PROCESSING: 120_000,
    ToastKind.SUCCESS: 3500,
    ToastKind.ERROR: 5000,
}

_BORDER = {
    ToastKind.PROCESSING: "#8A2BE2",
    ToastKind.SUCCESS: "#5ecf8a",
    ToastKind.ERROR: "#e05a6a",
}


class AppToast(QWidget):
    """Always-on-top bottom-right toast with a kind-specific GIF."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setObjectName("appToast")

        self._movies: dict[ToastKind, QMovie] = {}
        self._active_kind: ToastKind | None = None
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_toast)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 14, 10)
        root.setSpacing(10)

        self._gif = QLabel()
        self._gif.setFixedSize(56, 56)
        self._gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gif.setStyleSheet("background: transparent;")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._title = QLabel("MacSucks")
        self._title.setObjectName("toastTitle")
        self._message = QLabel("")
        self._message.setObjectName("toastBody")
        self._message.setWordWrap(True)
        self._message.setMaximumWidth(280)
        text_col.addWidget(self._title)
        text_col.addWidget(self._message)

        root.addWidget(self._gif)
        root.addLayout(text_col)

        for kind, filename in _GIF_FILES.items():
            path = asset_path(filename)
            if path is None:
                continue
            movie = QMovie(str(path))
            movie.setScaledSize(self._gif.size())
            self._movies[kind] = movie

        self._apply_chrome(ToastKind.PROCESSING)

    def show_processing(self, message: str = "Extracting text…") -> None:
        self.show_toast(ToastKind.PROCESSING, message)

    def show_success(self, message: str) -> None:
        self.show_toast(ToastKind.SUCCESS, message)

    def show_error(self, message: str) -> None:
        self.show_toast(ToastKind.ERROR, message)

    def show_toast(
        self,
        kind: ToastKind,
        message: str,
        *,
        timeout_ms: int | None = None,
    ) -> None:
        self._stop_movie()
        self._active_kind = kind
        self._apply_chrome(kind)
        self._message.setText(message)
        self.adjustSize()
        self._place_bottom_right()

        movie = self._movies.get(kind)
        if movie is not None:
            self._gif.setMovie(movie)
            movie.start()
        else:
            self._gif.clear()

        self.show()
        self.raise_()
        self._hide_timer.start(
            _DEFAULT_TIMEOUT_MS[kind] if timeout_ms is None else timeout_ms
        )

    def hide_toast(self) -> None:
        self._hide_timer.stop()
        self._stop_movie()
        self.hide()

    def _stop_movie(self) -> None:
        if self._active_kind is None:
            return
        movie = self._movies.get(self._active_kind)
        if movie is not None:
            movie.stop()
        self._active_kind = None

    def _apply_chrome(self, kind: ToastKind) -> None:
        border = _BORDER[kind]
        self.setStyleSheet(
            f"""
            QWidget#appToast {{
                background-color: rgba(18, 16, 22, 235);
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QLabel#toastTitle {{
                color: #f0eaf8;
                font-weight: 600;
                font-size: 14px;
                background: transparent;
            }}
            QLabel#toastBody {{
                color: #a898bc;
                font-size: 13px;
                background: transparent;
            }}
            """
        )

    def _place_bottom_right(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 24
        self.move(
            geo.right() - self.width() - margin,
            geo.bottom() - self.height() - margin,
        )


# Back-compat alias used by older imports
ProcessingToast = AppToast
