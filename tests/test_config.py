"""Tests for AppConfig."""

from macsucks.config import AppConfig, config_path


def test_default_config():
    cfg = AppConfig()
    assert cfg.hotkey == "alt+c"
    assert cfg.startup_enabled is True
    assert cfg.parse_tier == "fast"


def test_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("macsucks.config.config_path", lambda: tmp_path / "config.json")
    cfg = AppConfig(hotkey="ctrl+alt+c", startup_enabled=False, parse_tier="agentic")
    cfg.save()
    loaded = AppConfig.load()
    assert loaded.hotkey == "ctrl+alt+c"
    assert loaded.startup_enabled is False
    assert loaded.parse_tier == "agentic"


def test_parse_tier_save_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr("macsucks.config.config_path", lambda: tmp_path / "config.json")
    cfg = AppConfig.load()
    assert cfg.parse_tier == "fast"
    cfg.parse_tier = "fast"
    cfg.save()
    assert AppConfig.load().parse_tier == "fast"
    cfg.parse_tier = "cost_effective"
    cfg.save()
    assert AppConfig.load().parse_tier == "cost_effective"
    cfg.parse_tier = "fast"
    cfg.save()
    assert AppConfig.load().parse_tier == "fast"


def test_invalid_parse_tier_resets(tmp_path, monkeypatch):
    monkeypatch.setattr("macsucks.config.config_path", lambda: tmp_path / "config.json")
    path = tmp_path / "config.json"
    path.write_text('{"parse_tier": "nope"}', encoding="utf-8")
    loaded = AppConfig.load()
    assert loaded.parse_tier == "fast"
