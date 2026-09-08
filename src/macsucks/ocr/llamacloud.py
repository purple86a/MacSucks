"""LlamaCloud OCR integration."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from llama_cloud import AuthenticationError, LlamaCloud, RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class OcrResult:
    text: str
    success: bool
    error_message: str | None = None


class OcrError(Exception):
    def __init__(self, message: str, *, quota_exceeded: bool = False) -> None:
        super().__init__(message)
        self.quota_exceeded = quota_exceeded


def map_exception(exc: Exception) -> OcrError:
    if isinstance(exc, AuthenticationError):
        return OcrError("Invalid API key. Check your LlamaCloud credentials.")
    if isinstance(exc, RateLimitError):
        return OcrError("Rate limit exceeded. Wait a moment and try again.")
    status = getattr(exc, "status_code", None)
    if status in (402, 403):
        return OcrError(
            "Monthly credit limit reached. Check your LlamaCloud dashboard.",
            quota_exceeded=True,
        )
    message = str(exc) or exc.__class__.__name__
    lower = message.lower()
    if "timeout" in lower or "timed out" in lower:
        return OcrError("Verification timed out. Check your network and try again.")
    if "quota" in lower or "credit" in lower:
        return OcrError(
            "Monthly credit limit reached. Check your LlamaCloud dashboard.",
            quota_exceeded=True,
        )
    return OcrError(f"OCR failed: {message}")


class LlamaCloudOcr:
    def __init__(self, api_key: str, *, parse_tier: str = "fast") -> None:
        self._client = LlamaCloud(api_key=api_key)
        self._parse_tier = parse_tier

    def extract_text(self, png_bytes: bytes) -> str:
        total_start = time.perf_counter()
        logger.info(
            "OCR start — upload %d bytes (tier=%s)",
            len(png_bytes),
            self._parse_tier,
        )
        try:
            upload_start = time.perf_counter()
            file = self._client.files.create(
                file=("capture.png", png_bytes, "image/png"),
                purpose="parse",
            )
            upload_ms = (time.perf_counter() - upload_start) * 1000
            logger.info("OCR upload done in %.0f ms (file_id=%s)", upload_ms, file.id)

            parse_start = time.perf_counter()
            result = self._client.parsing.parse(
                file_id=file.id,
                tier=self._parse_tier,
                version="latest",
                expand=["text"],
                processing_options={"ocr_parameters": {"languages": ["en"]}},
            )
            parse_ms = (time.perf_counter() - parse_start) * 1000
            logger.info("OCR parse done in %.0f ms (tier=%s)", parse_ms, self._parse_tier)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - total_start) * 1000
            logger.error("OCR failed after %.0f ms: %s", elapsed_ms, exc)
            raise map_exception(exc) from exc

        pages = []
        if result.text and result.text.pages:
            for page in result.text.pages:
                page_text = getattr(page, "text", None) or ""
                if page_text.strip():
                    pages.append(page_text.strip())
        if not pages and result.markdown and result.markdown.pages:
            for page in result.markdown.pages:
                md = getattr(page, "markdown", None) or ""
                if md.strip():
                    pages.append(md.strip())

        text = "\n".join(pages).strip()
        total_ms = (time.perf_counter() - total_start) * 1000
        if not text:
            logger.warning("OCR finished in %.0f ms but no text detected", total_ms)
            raise OcrError("No text detected in the selected region.")
        logger.info(
            "OCR extracted %d characters in %.0f ms total (upload+parse)",
            len(text),
            total_ms,
        )
        return text
