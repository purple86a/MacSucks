"""Application configuration persisted to disk."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_HOTKEY = "alt+c"
LEGACY_HOTKEYS = frozenset({"ctrl+shift+o"})

# LlamaParse v2 tiers. Credits/page are from public LlamaCloud pricing and may change.
DEFAULT_PARSE_TIER = "fast"
PARSE_TIERS: tuple[tuple[str, str, int], ...] = (
    ("fast", "Fast", 1),
    ("cost_effective", "Cost-effective", 3),
    ("agentic", "Agentic", 10),
    ("agentic_plus", "Agentic Plus", 45),
)
PARSE_TIER_IDS = frozenset(t[0] for t in PARSE_TIERS)


def parse_tier_label(tier_id: str) -> str:
    for tid, name, credits in PARSE_TIERS:
        if tid == tier_id:
            unit = "credit" if credits == 1 else "credits"
            return f"{name} — {credits} {unit} / page"
    return tier_id


def config_dir() -> Path:
    base = os.environ.get("APPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Roaming")
    path = Path(base) / "MacSucks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return config_dir() / "config.json"


@dataclass
class AppConfig:
    hotkey: str = DEFAULT_HOTKEY
    startup_enabled: bool = True
    debug_logging: bool = True
    last_update_check: str | None = None
    api_key_verified: bool = False
    parse_tier: str = DEFAULT_PARSE_TIER

    @classmethod
    def load(cls) -> AppConfig:
        path = config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            known = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in known}
            cfg = cls(**filtered)
        except (json.JSONDecodeError, TypeError):
            return cls()

        dirty = False
        if cfg.hotkey.lower() in LEGACY_HOTKEYS:
            cfg.hotkey = DEFAULT_HOTKEY
            dirty = True
        if cfg.parse_tier not in PARSE_TIER_IDS:
            cfg.parse_tier = DEFAULT_PARSE_TIER
            dirty = True
        if dirty:
            cfg.save()
        return cfg

    def save(self) -> None:
        config_path().write_text(
            json.dumps(asdict(self), indent=2),
            encoding="utf-8",
        )
