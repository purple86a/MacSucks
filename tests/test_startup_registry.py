"""Tests for Windows startup registry helpers."""

from macsucks.startup import registry


def test_normalize_run_value_ignores_quoting_and_slashes():
    a = r'"C:\Users\Sara\AppData\Local\Programs\MacSucks\MacSucks.exe"'
    b = r"C:/Users/Sara/AppData/Local/Programs/MacSucks/MacSucks.exe"
    assert registry._normalize_run_value(a) == registry._normalize_run_value(b)


def test_run_command_frozen_is_quoted(monkeypatch):
    class FakeSys:
        frozen = True
        executable = r"C:\Local\MacSucks\MacSucks.exe"
        argv = [r"C:\Local\MacSucks\MacSucks.exe"]

    monkeypatch.setattr(registry, "sys", FakeSys())
    monkeypatch.setattr(
        registry,
        "executable_path",
        lambda: type("P", (), {"__str__": lambda self: r"C:\Local\MacSucks\MacSucks.exe"})(),
    )
    assert registry.run_command() == '"C:\\Local\\MacSucks\\MacSucks.exe"'


def test_run_command_dev_uses_module(monkeypatch):
    class FakeSys:
        frozen = False
        executable = r"C:\Python\python.exe"
        argv = [r"C:\proj\src\macsucks\main.py"]

    monkeypatch.setattr(registry, "sys", FakeSys())
    cmd = registry.run_command()
    assert "-m macsucks" in cmd
    assert cmd.startswith('"')
