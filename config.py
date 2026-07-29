"""
Configuration persistence via INI file.
LLM settings are saved/loaded automatically — API key is encrypted at rest.
"""

import configparser
from pathlib import Path

from privacy import encrypt, safe_decrypt

CONFIG_PATH = Path(__file__).parent / "settings.ini"


def load_config() -> configparser.ConfigParser:
    """Load settings.ini, returning a ConfigParser (empty if file missing)."""
    cfg = configparser.ConfigParser()
    if CONFIG_PATH.exists():
        cfg.read(str(CONFIG_PATH), encoding="utf-8")
    return cfg


def save_config(cfg: configparser.ConfigParser) -> None:
    """Write ConfigParser to settings.ini."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        cfg.write(f)


def get_llm_settings() -> dict:
    """Return saved LLM settings as a dict with defaults. API key is decrypted on read."""
    cfg = load_config()
    raw_key = cfg.get("llm", "api_key", fallback="")
    # Decrypt if it's an encrypted token, otherwise treat as plaintext
    key = safe_decrypt(raw_key) if raw_key else ""
    return {
        "provider": cfg.get("llm", "provider", fallback="openai"),
        "base_url": cfg.get(
            "llm",
            "base_url",
            fallback="https://api.openai.com/v1",
        ),
        "api_key": key,
        "model": cfg.get("llm", "model", fallback="gpt-4o"),
    }


def set_llm_settings(provider: str, base_url: str, api_key: str, model: str) -> None:
    """Persist LLM settings. API key is encrypted before writing."""
    cfg = load_config()
    if "llm" not in cfg:
        cfg.add_section("llm")
    cfg["llm"]["provider"] = provider
    cfg["llm"]["base_url"] = base_url
    cfg["llm"]["api_key"] = encrypt(api_key) if api_key else ""
    cfg["llm"]["model"] = model
    save_config(cfg)
