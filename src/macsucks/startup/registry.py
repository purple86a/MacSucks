"""Windows startup registry registration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MacSucks"


def executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def run_command() -> str:
    """Command written to HKCU\\...\\Run (always quoted for spaces)."""
    if getattr(sys, "frozen", False):
        return f'"{executable_path()}"'
    # Dev launches: use the active interpreter + module entrypoint.
    return f'"{Path(sys.executable).resolve()}" -m macsucks'


def _normalize_run_value(value: str) -> str:
    cleaned = value.strip().strip('"').replace("/", "\\")
    return " ".join(cleaned.split()).lower()


def registered_run_command() -> str | None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return str(value)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def is_startup_enabled() -> bool:
    """True only if Run points at *this* install/launch command."""
    current = registered_run_command()
    if current is None:
        return False
    return _normalize_run_value(current) == _normalize_run_value(run_command())


def enable_startup() -> None:
    import winreg

    command = run_command()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
    logger.info("Startup enabled: %s", command)


def disable_startup() -> None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        logger.info("Startup disabled")
    except FileNotFoundError:
        pass
