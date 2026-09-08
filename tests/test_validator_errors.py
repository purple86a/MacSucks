"""Tests for OCR error mapping."""

import httpx
from llama_cloud import AuthenticationError, RateLimitError

from macsucks.ocr.llamacloud import OcrError, map_exception


def _make_response(status: int) -> httpx.Response:
    request = httpx.Request("GET", "https://api.cloud.llamaindex.ai/test")
    return httpx.Response(status, request=request)


def test_auth_error_mapping():
    exc = map_exception(
        AuthenticationError("bad key", response=_make_response(401), body=None)
    )
    assert isinstance(exc, OcrError)
    assert "Invalid API key" in str(exc)
    assert exc.quota_exceeded is False


def test_rate_limit_mapping():
    exc = map_exception(
        RateLimitError("slow down", response=_make_response(429), body=None)
    )
    assert "Rate limit" in str(exc)


def test_quota_message_mapping():
    err = Exception("monthly quota exceeded")
    exc = map_exception(err)
    assert exc.quota_exceeded is True
