"""GitHub release update checker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from packaging import version

from macsucks import __version__

logger = logging.getLogger(__name__)

DEFAULT_OWNER = "purple86a"
DEFAULT_REPO = "MacSucks"
GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    download_url: str
    release_notes: str

    @property
    def update_available(self) -> bool:
        try:
            return version.parse(self.latest_version) > version.parse(self.current_version)
        except version.InvalidVersion:
            return False


def _repo_config() -> tuple[str, str]:
    try:
        import tomllib
        from pathlib import Path

        pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
        if pyproject.exists():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            tool = data.get("tool", {}).get("macsucks", {})
            owner = tool.get("update_repo_owner", DEFAULT_OWNER)
            repo = tool.get("update_repo_name", DEFAULT_REPO)
            return owner, repo
    except Exception:
        pass
    return DEFAULT_OWNER, DEFAULT_REPO


def check_for_updates(timeout: float = 15.0) -> UpdateInfo | None:
    owner, repo = _repo_config()
    url = GITHUB_API.format(owner=owner, repo=repo)
    try:
        response = httpx.get(
            url,
            timeout=timeout,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("Update check failed: %s", exc)
        return None

    tag = data.get("tag_name", "").lstrip("v")
    if not tag:
        return None

    download_url = ""
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.lower().endswith(".msi"):
            download_url = asset.get("browser_download_url", "")
            break

    return UpdateInfo(
        current_version=__version__,
        latest_version=tag,
        download_url=download_url,
        release_notes=data.get("body") or "",
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
