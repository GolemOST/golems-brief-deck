"""Local config persistence (~/.briefdeck/config.json). Stores the user's Anthropic key."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".briefdeck"
CONFIG_PATH = CONFIG_DIR / "config.json"


def _load() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    # Best-effort: tighten file permissions on POSIX. No-op on Windows.
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def get_api_key() -> str | None:
    """
    Resolution order:
      1. ANTHROPIC_API_KEY env var
      2. OPENAI_API_KEY env var
      3. Saved key in ~/.briefdeck/config.json (either provider)
    Returns None if nothing set.
    """
    for env_name in (
        "GEMINI_API_KEY", "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
    ):
        env = os.environ.get(env_name)
        if env and env.strip():
            return env.strip()
    cfg = _load()
    # Single canonical key slot — whichever provider's key was saved last.
    key = cfg.get("api_key") or cfg.get("anthropic_api_key")  # back-compat
    return key.strip() if key else None


def save_api_key(key: str) -> None:
    cfg = _load()
    cfg["api_key"] = key.strip()
    cfg.pop("anthropic_api_key", None)  # clear old field
    _save(cfg)


def clear_api_key() -> None:
    cfg = _load()
    cfg.pop("api_key", None)
    cfg.pop("anthropic_api_key", None)
    _save(cfg)
