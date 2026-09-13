"""Tests for MSI update installer helpers."""

from pathlib import Path

from macsucks.updater.installer import build_update_batch


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
    # Relaunch only after success labels
    assert ":relaunch" in script
    assert script.index("start /wait msiexec.exe") < script.index(":relaunch")


def test_batch_without_relaunch_still_waits(tmp_path: Path):
    msi = tmp_path / "MacSucks-9.9.9.msi"
    msi.write_bytes(b"fake")
    script = build_update_batch(msi, None)
    assert "start /wait msiexec.exe" in script
    assert "start \"\"" not in script
