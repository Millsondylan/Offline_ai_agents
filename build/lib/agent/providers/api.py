from __future__ import annotations

import json
from typing import Dict, Optional, Tuple

from .base import Provider, ProviderError
from .keys import KeyStore

try:  # pragma: no cover - optional dep
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore


class HostedAPIProvider(Provider):
    """Hosted API provider with keyring-backed secret management."""

    name = "api"
    mode = "online"

    def __init__(self, config: Optional[Dict] = None, keystore: Optional[KeyStore] = None) -> None:
        super().__init__(config)
        self.backend = (self.config.get("backend") or "other").lower()
        self.model = self.config.get("model")
        self.temperature = float(self.config.get("temperature", 0.2))
        self.timeout = int(self.config.get("timeout", 120))
        self.key_source = self.config.get("key_source", "keyring")
        self.keystore = keystore or KeyStore()
        self.key_id = self.config.get("key_id", self.backend)
        self.system_prompt = self.config.get(
            "system_prompt",
            "You are an autonomous software engineer. Return unified diffs only when applicable.",
        )

    def _get_key(self) -> str:
        key = self.keystore.get(self.key_id)
        if not key:
            raise ProviderError(
                f"No API key stored for backend '{self.backend}'. Use `agent apikey set {self.key_id}`."
            )
        return key

    def generate_patch(self, prompt: str, cycle_dir: str) -> Optional[str]:
        if requests is None:
            raise ProviderError("requests package not available; install requests to use hosted APIs")
        key = self._get_key()
        payload, headers, url = self._build_request(prompt, key)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except Exception as exc:  # pragma: no cover - network failure
            raise ProviderError(f"API request failed: {exc}") from exc
        if resp.status_code >= 400:
            raise ProviderError(f"API error {resp.status_code}: {resp.text[:200]} ...")
        text = self._extract_text(resp.json())
        out_path = f"{cycle_dir}/provider_output.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text or "")
        return text

    def _build_request(self, prompt: str, key: str) -> Tuple[Dict, Dict, str]:
        backend = self.backend
        if backend == "openai":
            url = self.config.get("url", "https://api.openai.com/v1/chat/completions")
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            payload: Dict = {
                "model": self.model or "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self.temperature,
            }
            return payload, headers, url
        if backend == "anthropic":
            url = self.config.get("url", "https://api.anthropic.com/v1/messages")
            headers = {
                "x-api-key": key,
                "anthropic-version": self.config.get("anthropic_version", "2023-06-01"),
                "content-type": "application/json",
            }
            payload = {
                "model": self.model or "claude-3-sonnet-20240229",
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "system": self.system_prompt,
                "temperature": self.temperature,
                "max_tokens": int(self.config.get("max_tokens", 8000)),
            }
            return payload, headers, url
        url = self.config.get("url")
        if not url:
            raise ProviderError("api provider requires 'url' for backend 'other'")
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
        }
        payload.update(self.config.get("extra_payload", {}))
        headers.update(self.config.get("extra_headers", {}))
        return payload, headers, url

    def _extract_text(self, data: Dict) -> str:
        backend = self.backend
        if backend == "openai":
            choices = data.get("choices") if isinstance(data, dict) else None
            if choices:
                return choices[0].get("message", {}).get("content", "")
        elif backend == "anthropic":
            content = data.get("content") if isinstance(data, dict) else None
            if isinstance(content, list) and content:
                item = content[0]
                if isinstance(item, dict):
                    return item.get("text", "") or item.get("content", "") or ""
        return data.get("output") if isinstance(data, dict) else json.dumps(data)

