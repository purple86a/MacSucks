"""Tests for update checker."""

from packaging import version

from macsucks.updater.checker import UpdateInfo


def test_update_available():
    info = UpdateInfo(
        current_version="0.1.0",
        latest_version="0.2.0",
        download_url="https://example.com/app.msi",
        release_notes="Fixes",
    )
    assert info.update_available is True


def test_no_update_when_same():
    info = UpdateInfo(
        current_version="1.0.0",
        latest_version="1.0.0",
        download_url="",
        release_notes="",
    )
    assert info.update_available is False


def test_no_update_when_older_remote():
    info = UpdateInfo(
        current_version="2.0.0",
        latest_version="1.9.0",
        download_url="",
        release_notes="",
    )
    assert info.update_available is False
