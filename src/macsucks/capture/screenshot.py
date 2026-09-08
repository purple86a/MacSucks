"""Screen region capture via mss."""

from __future__ import annotations

import io
from dataclasses import dataclass

import mss
from PIL import Image


@dataclass(frozen=True)
class Region:
    left: int
    top: int
    width: int
    height: int

    @property
    def mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


def capture_region(region: Region) -> bytes:
    if region.width < 1 or region.height < 1:
        raise ValueError("Region must have positive dimensions")
    with mss.mss() as sct:
        shot = sct.grab(region.mss_monitor)
        image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
