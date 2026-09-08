"""API key validation before persistence."""

from __future__ import annotations

import logging
import time

from llama_cloud import LlamaCloud

from macsucks.ocr.llamacloud import map_exception

logger = logging.getLogger(__name__)

VALIDATE_TIMEOUT_SEC = 15.0


def validate_api_key(api_key: str) -> tuple[bool, str]:
    key = api_key.strip()
    if not key:
        return False, "API key cannot be empty."
    if not key.startswith("llx-"):
        return False, "API key should start with 'llx-'."

    start = time.perf_counter()
    logger.info("API key verify start (timeout=%.0fs)", VALIDATE_TIMEOUT_SEC)
    try:
        client = LlamaCloud(api_key=key, timeout=VALIDATE_TIMEOUT_SEC)
        client.files.list(page_size=1, timeout=VALIDATE_TIMEOUT_SEC)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("API key validation succeeded in %.0f ms via files.list", elapsed_ms)
        return True, "API key verified successfully."
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("API key validation failed after %.0f ms: %s", elapsed_ms, exc)
        mapped = map_exception(exc)
        message = str(mapped)
        if message.startswith("OCR failed:"):
            message = message.replace("OCR failed:", "Verification failed:", 1)
        return False, message
