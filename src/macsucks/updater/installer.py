"""MSI download and installation."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


def download_msi(url: str, dest: Path, progress_callback=None) -> Path:
    logger.info("Downloading update from %s", url)
    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
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


def install_msi(msi_path: Path) -> None:
    if not msi_path.exists():
        raise FileNotFoundError(f"MSI not found: {msi_path}")
    logger.info("Launching installer: %s", msi_path)
    subprocess.Popen(
        [
            "msiexec",
            "/i",
            str(msi_path),
            "/passive",
            "REBOOT=ReallySuppress",
        ],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    sys.exit(0)
