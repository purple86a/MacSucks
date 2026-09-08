"""Tests for API key validation helpers and config migration."""

import sys

import pytest

from macsucks.config import DEFAULT_HOTKEY, AppConfig


def test_legacy_hotkey_migrates(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text('{"hotkey": "ctrl+shift+o", "startup_enabled": true}', encoding="utf-8")
    monkeypatch.setattr("macsucks.config.config_path", lambda: cfg_path)
    loaded = AppConfig.load()
    assert loaded.hotkey == DEFAULT_HOTKEY
    assert '"alt+c"' in cfg_path.read_text(encoding="utf-8")


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
def test_secrets_roundtrip():
    from macsucks.secrets import delete_api_key, get_api_key, set_api_key

    delete_api_key()
    set_api_key("llx-test-key-12345")
    assert get_api_key() == "llx-test-key-12345"
    delete_api_key()
    assert get_api_key() is None
