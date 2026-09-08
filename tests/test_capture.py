"""Tests for screen capture."""

import pytest
from PySide6.QtCore import QPoint

from macsucks.capture.overlay import SelectionOverlay
from macsucks.capture.screenshot import Region, capture_region


def test_region_mss_monitor():
    region = Region(10, 20, 100, 50)
    assert region.mss_monitor == {
        "left": 10,
        "top": 20,
        "width": 100,
        "height": 50,
    }


def test_capture_invalid_region():
    with pytest.raises(ValueError):
        capture_region(Region(0, 0, 0, 10))


def test_selection_rect(qtbot):
    overlay = SelectionOverlay()
    qtbot.addWidget(overlay)
    assert overlay._selection_rect() is None
    overlay._origin = QPoint(10, 10)
    overlay._current = QPoint(40, 50)
    rect = overlay._selection_rect()
    assert rect is not None
    assert rect.width() == 31
    assert rect.height() == 41
