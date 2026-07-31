"""
Configuration persistence via TOML file (Streamlit standard).
LLM settings are saved/loaded automatically — API key is encrypted at rest.

Reads from .streamlit/settings.toml using tomllib (stdlib, Python 3.11+).
Writes manual TOML — no extra dependencies needed.

Cloud / shared deployment mode:
  Set environment variable RESUMEBRIDGE_DEPLOYMENT=cloud (or use
  Streamlit Cloud secrets) to activate cloud mode. In cloud mode,
  the sidebar is hidden, the model is fixed to deepseek-v4-flask,
  and no data is persisted.
"""

import os
import tomllib
from pathlib import Path

from privacy import encrypt, safe_decrypt

CONFIG_DIR = Path(__file__).parent / ".streamlit"
CONFIG_PATH = CONFIG_DIR / "settings.toml"


def _load_toml() -> dict:
    """Read the TOML file, returning a dict (empty if file missing)."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def _save_toml(data: dict) -> None:
    """Write a flat dict to TOML. Only [llm] section is supported."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    llm = data.get("llm", {})
    lines = [
        "# ResumeBridge settings — API key is encrypted at rest\n",
        "\n",
        "[llm]\n",
        f"provider = \"{llm.get('provider', 'openai')}\"\n",
        f"base_url = \"{llm.get('base_url', 'https://api.openai.com/v1')}\"\n",
        f"api_key = \"{llm.get('api_key', '')}\"\n",
        f"model = \"{llm.get('model', 'gpt-5.6-terra')}\"\n",
    ]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_llm_settings() -> dict:
    """Return saved LLM settings as a dict with defaults. API key is decrypted on read."""
    data = _load_toml()
    llm = data.get("llm", {})
    raw_key = llm.get("api_key", "")
    key = safe_decrypt(raw_key) if raw_key else ""
    return {
        "provider": llm.get("provider", "openai"),
        "base_url": llm.get("base_url", "https://api.openai.com/v1"),
        "api_key": key,
        "model": llm.get("model", "gpt-5.6-terra"),
    }


def set_llm_settings(provider: str, base_url: str, api_key: str, model: str) -> None:
    """Persist LLM settings. API key is encrypted before writing."""
    _save_toml({
        "llm": {
            "provider": provider,
            "base_url": base_url,
            "api_key": encrypt(api_key) if api_key else "",
            "model": model,
        }
    })


# ---------------------------------------------------------------------------
# Cloud / shared deployment detection
# ---------------------------------------------------------------------------

def is_cloud_deployment() -> bool:
    """
    Return True if the app is deployed on a shared/cloud platform
    (e.g. share.streamlit.io) where we want simplified UX and no
    persistent data storage.

    Detection order:
      1. RESUMEBRIDGE_DEPLOYMENT env var set to "cloud"
      2. STREAMLIT_SHARING_MODE env var (auto-set by some Streamlit hosts)
    """
    if os.getenv("RESUMEBRIDGE_DEPLOYMENT", "").lower() == "cloud":
        return True
    if os.getenv("STREAMLIT_SHARING_MODE", "") == "streamlit":
        return True
    return False


def get_cloud_config() -> dict:
    """
    Read LLM configuration for cloud/shared deployment.

    Checks (in order):
      1. Environment variables (RESUMEBRIDGE_*)
      2. Streamlit secrets (st.secrets.resumebridge) — standard for Streamlit Cloud

    Defaults: deepseek provider, deepseek-v4-flask model.

    Example Streamlit Cloud secrets.toml:
        RESUMEBRIDGE_API_KEY = "sk-..."
        # RESUMEBRIDGE_PROVIDER = "deepseek"       # optional, this is the default
        # RESUMEBRIDGE_MODEL = "deepseek-v4-flask" # optional, this is the default
    """
    # Start with environment variables
    provider = os.getenv("RESUMEBRIDGE_PROVIDER", "")
    base_url = os.getenv("RESUMEBRIDGE_BASE_URL", "")
    api_key = os.getenv("RESUMEBRIDGE_API_KEY", "")
    model = os.getenv("RESUMEBRIDGE_MODEL", "")

    # Fallback: try Streamlit secrets (the standard way on share.streamlit.io)
    if not (provider and api_key):
        try:
            import streamlit as st
            secrets = dict(st.secrets.get("resumebridge", {}))
        except Exception:
            secrets = {}
        if not provider:
            provider = secrets.get("provider", "deepseek")
        if not base_url:
            base_url = secrets.get("base_url", "https://api.deepseek.com/v1")
        if not api_key:
            api_key = secrets.get("api_key", "")
        if not model:
            model = secrets.get("model", "deepseek-v4-flask")

    # Apply hard defaults for anything still unset
    return {
        "provider": provider or "deepseek",
        "base_url": base_url or "https://api.deepseek.com/v1",
        "api_key": api_key,
        "model": model or "deepseek-v4-flask",
    }
