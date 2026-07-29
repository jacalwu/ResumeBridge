"""
LLM Client — abstract layer over multiple LLM APIs.
Supports OpenAI, Anthropic, DeepSeek, Qwen (Tongyi), GLM (Zhipu), Kimi (Moonshot),
and any OpenAI-compatible endpoint via custom Base URL.

Anthropic uses its native /messages API.
All other providers use the OpenAI-compatible /chat/completions API.
"""

from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-terra",          # GPT-5.6 Terra — balanced perf/cost (July 2026)
        "api_format": "openai",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-5-20250630",  # Claude Sonnet 5 — default for most users (June 2026)
        "api_format": "anthropic",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",              # DeepSeek-V4 (stable alias, auto-updated)
        "api_format": "openai",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",                  # Qwen3.8-Max (stable alias, auto-updated, July 2026)
        "api_format": "openai",
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-5.2",                    # GLM-5.2 — latest open-weight flagship (June 2026)
        "api_format": "openai",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k3",                    # Kimi K3 — 2.8T MoE flagship (July 2026)
        "api_format": "openai",
    },
}

VALID_PROVIDERS = list(PROVIDER_DEFAULTS.keys())


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMClientError(Exception):
    """Raised when the LLM provider returns an error."""
    pass


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified client. Dispatch is based on api_format (openai vs anthropic)."""

    def __init__(self, provider: str, base_url: str, api_key: str, model: str):
        if provider not in PROVIDER_DEFAULTS:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Valid options: {', '.join(VALID_PROVIDERS)}"
            )
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._api_format = PROVIDER_DEFAULTS[provider]["api_format"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request and return the text response."""
        if self._api_format == "openai":
            return self._call_openai_compatible(system_prompt, user_prompt)
        else:
            return self._call_anthropic(system_prompt, user_prompt)

    # ------------------------------------------------------------------
    # OpenAI-compatible (OpenAI, DeepSeek, Qwen, GLM, Kimi, custom)
    # ------------------------------------------------------------------

    def _call_openai_compatible(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=120)
        if resp.status_code != 200:
            raise LLMClientError(
                f"{self.provider} error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ------------------------------------------------------------------
    # Anthropic (native API)
    # ------------------------------------------------------------------

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.3,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=120)
        if resp.status_code != 200:
            raise LLMClientError(
                f"Anthropic error {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        return data["content"][0]["text"]
