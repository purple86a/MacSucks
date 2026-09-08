"""Process CPU and memory sampling."""

from __future__ import annotations

import os

import psutil


class ResourceMonitor:
    def __init__(self) -> None:
        self._process = psutil.Process(os.getpid())
        self._process.cpu_percent(interval=None)

    def sample(self) -> tuple[float, float]:
        cpu = self._process.cpu_percent(interval=None)
        rss_mb = self._process.memory_info().rss / (1024 * 1024)
        return cpu, rss_mb
