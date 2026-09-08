"""MacSucks entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from macsucks.app_controller import AppController
from macsucks.tray import load_app_icon
from macsucks.ui.styles import build_stylesheet

logger = logging.getLogger(__name__)

SINGLE_INSTANCE_KEY = "MacSucks_SingleInstance_v1"


def _another_instance_running() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(SINGLE_INSTANCE_KEY)
    if socket.waitForConnected(500):
        socket.close()
        return True
    return False


def _claim_single_instance(app: QApplication) -> QLocalServer | None:
    server = QLocalServer(app)
    QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
    if not server.listen(SINGLE_INSTANCE_KEY):
        return None
    return server


def main() -> None:
    if _another_instance_running():
        QMessageBox.warning(
            None,
            "MacSucks",
            "MacSucks is already running. Check the system tray.",
        )
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("MacSucks")
    app.setWindowIcon(load_app_icon())
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())

    server = _claim_single_instance(app)
    if server is None:
        QMessageBox.warning(None, "MacSucks", "Could not start — another instance may be running.")
        sys.exit(1)

    controller = AppController(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
