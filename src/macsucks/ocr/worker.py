"""OCR worker thread."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from macsucks.ocr.llamacloud import LlamaCloudOcr, OcrError

logger = logging.getLogger(__name__)


class OcrWorker(QThread):
    finished_ok = Signal(str)
    finished_error = Signal(str, bool)

    def __init__(
        self,
        api_key: str,
        png_bytes: bytes,
        *,
        parse_tier: str = "fast",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._api_key = api_key
        self._png_bytes = png_bytes
        self._parse_tier = parse_tier

    def run(self) -> None:
        import time

        start = time.perf_counter()
        logger.info(
            "OCR worker started (%d bytes, tier=%s)",
            len(self._png_bytes),
            self._parse_tier,
        )
        try:
            ocr = LlamaCloudOcr(self._api_key, parse_tier=self._parse_tier)
            text = ocr.extract_text(self._png_bytes)
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("OCR worker finished OK in %.0f ms", elapsed_ms)
            self.finished_ok.emit(text)
        except OcrError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("OCR worker failed in %.0f ms: %s", elapsed_ms, exc)
            self.finished_error.emit(str(exc), exc.quota_exceeded)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("Unexpected OCR error after %.0f ms", elapsed_ms)
            self.finished_error.emit(str(exc), False)
