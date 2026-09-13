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

# Windows: hide the helper console window.
CREATE_NO_WINDOW = 0x08000000


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
    logger.info("Download complete: %s (%s bytes)", dest, dest.stat().st_size)
    return dest


def default_msi_path(version: str) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "MacSucks"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"MacSucks-{version}.msi"


def build_update_batch(msi_path: Path, relaunch_exe: Path | None = None) -> str:
    """Build a cmd script that waits for msiexec to finish before relaunching.

    Plain `msiexec` from cmd returns immediately (GUI subsystem), so without
    `start /wait` the app was relaunched while the old EXE was still locked and
    the upgrade never stuck — endless update prompts.

    Relaunch must set PYINSTALLER_RESET_ENVIRONMENT=1 and clear inherited
    ``_PYI_*`` vars; otherwise the onefile bootloader thinks it is a worker
    child of cmd.exe and aborts with a security validation error.
    """
    msi = str(msi_path.resolve())
    log = str((msi_path.parent / "msi-update.log").resolve())
    status = str((msi_path.parent / "msi-update-exit.txt").resolve())
    lines = [
        "@echo off",
        "setlocal",
        "rem Give MacSucks time to fully exit and unlock MacSucks.exe",
        "ping -n 6 127.0.0.1 >nul",
        f'start /wait msiexec.exe /i "{msi}" /qn REBOOT=ReallySuppress /l*v "{log}"',
        "set ERR=%ERRORLEVEL%",
        f'echo msiexec_exit=%ERR%> "{status}"',
        "rem 0 = success, 3010 = success reboot required",
        "if %ERR%==0 goto relaunch",
        "if %ERR%==3010 goto relaunch",
        "exit /b %ERR%",
        ":relaunch",
        "rem PyInstaller onefile: start a fresh instance, not a worker child",
        "set PYINSTALLER_RESET_ENVIRONMENT=1",
        "for /f \"tokens=1 delims==\" %%V in ('set _PYI_ 2^>nul') do set \"%%V=\"",
    ]
    if relaunch_exe is not None:
        exe = str(relaunch_exe.resolve())
        lines.append(f'if exist "{exe}" start "" "{exe}"')
    lines.append("exit /b 0")
    lines.append("")
    return "\r\n".join(lines)


def _clean_env_for_updater() -> dict[str, str]:
    """Env for the install helper — strip PyInstaller process-state variables."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("_PYI_") and key != "_MEIPASS2"
    }
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def schedule_msi_install(msi_path: Path) -> None:
    """Install after this process exits so MacSucks.exe is not file-locked.

    Writes a small batch file and runs it detached so install survives our exit.
    """
    msi_path = Path(msi_path)
    if not msi_path.exists():
        raise FileNotFoundError(f"MSI not found: {msi_path}")

    relaunch_exe: Path | None = None
    if getattr(sys, "frozen", False):
        relaunch_exe = Path(sys.executable).resolve()

    batch = msi_path.parent / "install-update.cmd"
    batch.write_text(build_update_batch(msi_path, relaunch_exe), encoding="utf-8")
    logger.info(
        "Scheduling MSI install via %s (msi=%s, relaunch=%s)",
        batch,
        msi_path,
        relaunch_exe,
    )
    subprocess.Popen(
        ["cmd.exe", "/c", str(batch)],
        cwd=str(msi_path.parent),
        env=_clean_env_for_updater(),
        creationflags=CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )


def install_msi(msi_path: Path) -> None:
    """Backward-compatible name — schedules install then exits this process."""
    schedule_msi_install(msi_path)
    sys.exit(0)
