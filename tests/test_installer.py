"""Tests for MSI update installer helpers."""

import os
from pathlib import Path

from macsucks.updater.installer import _clean_env_for_updater, build_update_batch


def test_batch_waits_for_msiexec_before_relaunch(tmp_path: Path):
    msi = tmp_path / "MacSucks-1.2.3.msi"
    msi.write_bytes(b"fake")
    exe = tmp_path / "MacSucks.exe"
    exe.write_bytes(b"fake")

    script = build_update_batch(msi, exe)

    assert "start /wait msiexec.exe" in script
    assert str(msi.resolve()) in script
    assert str(exe.resolve()) in script
    assert "/qn" in script
    assert "PYINSTALLER_RESET_ENVIRONMENT=1" in script
    assert "set _PYI_" in script
    # Relaunch only after success labels
    assert ":relaunch" in script
    assert script.index("start /wait msiexec.exe") < script.index(":relaunch")
    assert script.index("PYINSTALLER_RESET_ENVIRONMENT=1") < script.index(
        f'start "" "{exe.resolve()}"'
    )


def test_batch_without_relaunch_still_waits(tmp_path: Path):
    msi = tmp_path / "MacSucks-9.9.9.msi"
    msi.write_bytes(b"fake")
    script = build_update_batch(msi, None)
    assert "start /wait msiexec.exe" in script
    assert "start \"\"" not in script


def test_clean_env_strips_pyinstaller_state(monkeypatch):
    monkeypatch.setenv("_PYI_ARCHIVE_FILE", "spoof")
    monkeypatch.setenv("_PYI_APPLICATION_HOME_DIR", "C:\\Temp\\_MEI123")
    monkeypatch.setenv("PATH", os.environ.get("PATH", "C:\\Windows"))
    env = _clean_env_for_updater()
    assert "_PYI_ARCHIVE_FILE" not in env
    assert "_PYI_APPLICATION_HOME_DIR" not in env
    assert env["PYINSTALLER_RESET_ENVIRONMENT"] == "1"
    assert "PATH" in env
