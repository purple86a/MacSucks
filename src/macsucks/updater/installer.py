"""MSI download and installation."""

from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def download_msi(url: str, dest: Path, progress_callback=None) -> Path:
    logger.info("Downloading update from %s", url)
    with httpx.stream(
        "GET",
        url,
        follow_redirects=True,
        timeout=120.0,
        headers={"User-Agent": f"MacSucks-Updater (+https://github.com/purple86a/MacSucks)"},
    ) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes(chunk_size=65536):
                fh.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    progress_callback(downloaded, total)
    return dest


def default_msi_path(version: str) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "MacSucks"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"MacSucks-{version}.msi"


def schedule_msi_install(msi_path: Path) -> None:
    """Install after this process exits so MacSucks.exe is not file-locked.

    Uses a detached cmd that waits briefly, runs msiexec, then relaunches the app.
    """
    if not msi_path.exists():
        raise FileNotFoundError(f"MSI not found: {msi_path}")

    relaunch = ""
    if getattr(sys, "frozen", False):
        exe = str(Path(sys.executable).resolve())
        relaunch = f' & if exist "{exe}" start "" "{exe}"'

    # ping ~3s delay without requiring timeout.exe privileges quirks
    script = (
        f'ping -n 4 127.0.0.1 >nul & '
        f'msiexec /i "{msi_path}" /passive REBOOT=ReallySuppress'
        f"{relaunch}"
    )
    logger.info("Scheduling MSI install: %s", msi_path)
    subprocess.Popen(
        ["cmd.exe", "/c", script],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )


def install_msi(msi_path: Path) -> None:
    """Backward-compatible name — schedules install then exits this process."""
    schedule_msi_install(msi_path)
    sys.exit(0)
