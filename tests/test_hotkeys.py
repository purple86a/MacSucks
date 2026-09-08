"""Tests for hotkey manager."""

from macsucks.hotkeys.manager import HotkeyManager


def test_format_display():
    assert HotkeyManager.format_display("alt+c") == "Alt + C"
    assert HotkeyManager.format_display("ctrl+shift+o") == "Ctrl + Shift + O"
