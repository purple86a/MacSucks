"""Packaged asset path helpers (dev + PyInstaller frozen)."""

from __future__ import annotations

import sys
from pathlib import Path


def assets_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "macsucks" / "assets"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent / "assets"


def asset_path(name: str) -> Path | None:
    path = assets_dir() / name
    return path if path.exists() else None
